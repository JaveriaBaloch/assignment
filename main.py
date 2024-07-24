import os
from flask import Flask, render_template, abort, request, jsonify, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
import logging

app = Flask(__name__)

# Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'myuser')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'mypassword')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'shop')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.secret_key = os.urandom(24)

# Initialize extensions
mysql = MySQL(app)
bcrypt = Bcrypt(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/log-up')
def logup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'message': 'Username, email, and password are required'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    cur = mysql.connection.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cur.fetchone()
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 400

        cur.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                    (username, email, hashed_password))
        mysql.connection.commit()

        # Fetch the newly created user to get user_id
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        new_user = cur.fetchone()
        session['user_id'] = new_user[0]  # Set session user_id to newly created user_id

        return jsonify({'message': 'User registered and logged in successfully', 'redirect': url_for('index')}), 201
    except Exception as e:
        app.logger.error(f'Error during signup for email {email}: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        if user:
            stored_password = user[2]
            if bcrypt.check_password_hash(stored_password, password):
                session['user_id'] = user[0]
                return jsonify({'message': 'Login successful', 'redirect': url_for('index')}), 200
            else:
                return jsonify({'message': 'Invalid email or password'}), 401
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    except Exception as e:
        app.logger.error(f'Error during login for email {email}: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('signin'))

@app.route('/signin', methods=['GET'])
def signin():
    return render_template('signin.html')

@app.route('/xml_to_dict')
def xml_to_dict():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM coffee_items')
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    coffee_items = []
    for row in rows:
        item = dict(zip(columns, row))
        coffee_items.append(item)

    return jsonify(coffee_items)

@app.route('/item/<int:entity_id>')
def item_detail(entity_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM coffee_items WHERE entity_id = %s', (entity_id,))
    row = cur.fetchone()
    if row is None:
        abort(404)

    columns = [desc[0] for desc in cur.description]
    item = dict(zip(columns, row))
    item['price'] = round(float(item['price']), 2)
    return render_template('item.html', item=item)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM coffee_items')
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    coffee_items = []
    for row in rows:
        item = dict(zip(columns, row))
        item['price'] = round(float(item['price']), 2)
        coffee_items.append(item)

    return render_template('index.html', items=coffee_items)

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT ci.*, c.quantity
            FROM cart c
            JOIN coffee_items ci ON c.item_id = ci.entity_id
            WHERE c.user_id = %s
        ''', (user_id,))
        cart_items = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        cart_items_list = []
        for row in cart_items:
            item = dict(zip(columns, row))
            item['price'] = round(float(item['price']), 2)
            cart_items_list.append(item)
        return render_template('cart.html', items=cart_items_list)
    except Exception as e:
        app.logger.error(f'Error retrieving cart: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT * FROM cart WHERE user_id = %s AND item_id = %s
        ''', (user_id, item_id))
        existing_item = cur.fetchone()

        if existing_item:
            cur.execute('''
                UPDATE cart SET quantity = %s WHERE user_id = %s AND item_id = %s
            ''', (quantity, user_id, item_id))
        else:
            cur.execute('''
                INSERT INTO cart (user_id, item_id, quantity) VALUES (%s, %s, %s)
            ''', (user_id, item_id, quantity))

        mysql.connection.commit()
        return redirect(url_for('cart'))
    except Exception as e:
        app.logger.error(f'Error adding to cart: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    try:
        cur.execute('''
            SELECT c.item_id, c.quantity, ci.price, ci.name, ci.image 
            FROM cart c
            JOIN coffee_items ci ON c.item_id = ci.entity_id
            WHERE c.user_id = %s
        ''', (user_id,))
        cart_items = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        cart_items_list = []
        total_amount = 0

        for row in cart_items:
            item = dict(zip(columns, row))
            item['price'] = round(float(item['price']) if item['price'] is not None else 0, 2)
            item['quantity'] = int(item['quantity']) if item['quantity'] is not None else 0
            item['total'] = round(item['price'] * item['quantity'], 2)
            total_amount += item['total']
            cart_items_list.append(item)

        total_amount = round(total_amount, 2)
        cur.close()
        return render_template('checkout.html', items=cart_items_list, total_amount=total_amount)
    except Exception as e:
        app.logger.error(f'Error retrieving cart items for checkout: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']
    house = request.form.get('house')
    street = request.form.get('street')
    city = request.form.get('city')
    postal_code = request.form.get('postal_code')
    state = request.form.get('state')
    country = request.form.get('country')

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT cart.item_id, cart.quantity, coffee_items.price 
            FROM cart 
            JOIN coffee_items ON cart.item_id = coffee_items.entity_id 
            WHERE cart.user_id = %s
        ''', (user_id,))
        cart_items = cur.fetchall()

        if not cart_items:
            return jsonify({'message': 'Cart is empty'}), 400

        total_amount = 0
        for item in cart_items:
            total_amount += float(item[2]) * int(item[1])

        total_amount = round(total_amount, 2)

        cur.execute('''
            INSERT INTO orders (user_id, total_amount, house, street, city, postal_code, state, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, total_amount, house, street, city, postal_code, state, country))
        order_id = cur.lastrowid

        for item in cart_items:
            cur.execute('''
                INSERT INTO order_items (order_id, item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, item[0], item[1], item[2]))

        cur.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))
        mysql.connection.commit()
        return jsonify({'message': 'Order placed successfully', 'redirect': url_for('index')}), 200
    except Exception as e:
        app.logger.error(f'Error placing order: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT * FROM coffee_items 
            WHERE name LIKE %s OR description LIKE %s
        ''', (f'%{query}%', f'%{query}%'))
        results = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

        items = []
        for row in results:
            item = dict(zip(columns, row))
            item['price'] = round(float(item['price']), 2)
            items.append(item)

        return render_template('search_results.html', items=items, query=query)
    except Exception as e:
        app.logger.error(f'Error during search: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
