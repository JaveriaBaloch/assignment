import os
from flask import Flask, render_template, abort, request, jsonify, redirect, url_for, session
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
import logging

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'myuser'
app.config['MYSQL_PASSWORD'] = 'mypassword'
app.config['MYSQL_DB'] = 'shop'
app.secret_key = os.urandom(24)

mysql = MySQL(app)
bcrypt = Bcrypt(app)

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

    # Hash the password
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
        return jsonify({'message': 'User registered successfully', 'redirect': url_for('index')}), 201
    except Exception as e:
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
        logging.debug(f'Fetched user: {user}')

        if user:
            stored_password = user[2]  # Assuming password hash is in the third column
            logging.debug(f'Verifying provided password against stored hash')
            if bcrypt.check_password_hash(stored_password, password):
                session['user_id'] = user[0]
                return jsonify({'message': 'Login successful', 'redirect': url_for('index')}), 200
            else:
                logging.debug('Password mismatch')
                return jsonify({'message': 'Invalid email or password'}), 401
        else:
            logging.debug('User not found')
            return jsonify({'message': 'Invalid email or password'}), 401
    except Exception as e:
        logging.error(f'Error during login: {str(e)}')
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
        app.logger.error(f'Error retrieving cart: {str(e)}')  # Log the error for debugging
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('signin'))  # Redirect to login if not logged in

    user_id = session['user_id']
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))  # Default to 1 if not provided

    cur = mysql.connection.cursor()
    try:
        # Check if item already exists in cart
        cur.execute('''
            SELECT * FROM cart WHERE user_id = %s AND item_id = %s
        ''', (user_id, item_id))
        existing_item = cur.fetchone()

        if existing_item:
            # Update quantity if item already in cart
            cur.execute('''
                UPDATE cart SET quantity = %s WHERE user_id = %s AND item_id = %s
            ''', (quantity, user_id, item_id))
        else:
            # Add new item to cart
            cur.execute('''
                INSERT INTO cart (user_id, item_id, quantity) VALUES (%s, %s, %s)
            ''', (user_id, item_id, quantity))

        mysql.connection.commit()
        return redirect(url_for('cart'))  # Redirect to cart page after adding
    except Exception as e:
        app.logger.error(f'Error adding to cart: {str(e)}')  # Log the error for debugging
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

        total_amount = round(total_amount, 2)  # Ensure total amount is rounded to 2 decimal places
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
        # Fetch cart items
        cur.execute('''
            SELECT cart.item_id, cart.quantity, coffee_items.price 
            FROM cart 
            JOIN coffee_items ON cart.item_id = coffee_items.entity_id 
            WHERE cart.user_id = %s
        ''', (user_id,))
        cart_items = cur.fetchall()

        # Log the cart_items to debug
        app.logger.debug(f'Cart items fetched: {cart_items}')

        # Convert cart_items to a list if necessary
        if isinstance(cart_items, tuple):
            cart_items = list(cart_items)

        # Ensure cart_items is iterable
        if not isinstance(cart_items, list):
            raise ValueError('Expected cart_items to be a list of tuples.')

        # Calculate total amount
        total_amount = sum(float(item[2]) * item[1] for item in cart_items)

        # Insert the order
        cur.execute('''
            INSERT INTO orders (user_id, total_amount, house, street, city, postal_code, state, country)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, total_amount, house, street, city, postal_code, state, country))
        order_id = cur.lastrowid

        # Insert items into order_items
        for item in cart_items:
            item_id = item[0]
            quantity = item[1]
            price = float(item[2])

            cur.execute('''
                INSERT INTO order_items (order_id, item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, item_id, quantity, price))

        # Clear the cart
        cur.execute('DELETE FROM cart WHERE user_id = %s', (user_id,))

        mysql.connection.commit()
        return redirect(url_for('orders'))

    except Exception as e:
        app.logger.error(f'Error during checkout: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    try:
        # Fetch user orders
        cur.execute('SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC', (user_id,))
        orders_list = cur.fetchall()

        if not orders_list:
            app.logger.debug('No orders found for the user.')
            return render_template('orders.html', orders=[])

        order_columns = [desc[0] for desc in cur.description]
        app.logger.debug(f'Order columns: {order_columns}')

        order_data = []
        for order in orders_list:
            order_dict = dict(zip(order_columns, order))
            app.logger.debug(f'Processing order: {order_dict}')

            # Fetch items for each order
            cur.execute('''
                SELECT oi.*, ci.name, ci.image 
                FROM order_items oi 
                JOIN coffee_items ci ON oi.item_id = ci.entity_id 
                WHERE oi.order_id = %s
            ''', (order_dict['order_id'],))
            order_items = cur.fetchall()

            item_columns = [desc[0] for desc in cur.description]
            app.logger.debug(f'Item columns: {item_columns}')

            order_items_dict = [dict(zip(item_columns, item)) for item in order_items]
            order_data.append({'order': order_dict, 'items': order_items_dict})

        return render_template('orders.html', orders=order_data)
    except Exception as e:
        app.logger.error(f'Error retrieving orders: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}'}), 500
    finally:
        cur.close()


@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT * FROM coffee_items 
        WHERE name LIKE %s OR description LIKE %s OR CategoryName LIKE %s
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    search_results = []
    for row in rows:
        item = dict(zip(columns, row))
        item['price'] = round(float(item['price']), 2)
        search_results.append(item)

    return render_template('search_results.html', items=search_results)

if __name__ == '__main__':
    app.run(debug=True)
