import os
from flask import Flask, render_template, abort, request, jsonify, redirect, url_for, session
from flask_mysqldb import MySQL
from utils.format_price import format_price
import logging

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'myuser'
app.config['MYSQL_PASSWORD'] = 'mypassword'
app.config['MYSQL_DB'] = 'shop'
app.secret_key = os.urandom(24)

mysql = MySQL(app)

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

    plaintext_password = password

    cur = mysql.connection.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cur.fetchone()
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 400

        cur.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                    (username, email, plaintext_password))
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
            stored_password = user[2]  # Assuming password is in the third column
            logging.debug(f'Comparing provided password "{password}" with stored password "{stored_password}"')
            if stored_password == password:
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
    item['price'] = format_price(item['price'])
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
        item['price'] = format_price(item['price'])
        coffee_items.append(item)

    return render_template('index.html', items=coffee_items)

@app.route('/loadApp', methods=['GET'])
def loadApp():
    return 'App loaded'

if __name__ == '__main__':
    app.run(debug=True, port=8000)
