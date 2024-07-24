# Flask Coffee Shop Application

This project is a Flask-based web application for a coffee shop, featuring user authentication, cart management, and order processing. It uses MySQL for database management and includes a variety of endpoints to handle user interactions.

### Table of Contents
- Features
- Setup Instructions
- Usage
- SOLID Principles Applied
- License

### Features
User signup and login with password hashing
Cart management with item addition and removal
Order placement and checkout process
Search functionality for coffee items
Error handling with custom error pages

## Setup Instructions
### Prerequisites
- Python 11.x
- MySQL
- Pip (Python package installer)

### Cloning the Repository
```bash 
git clone https://github.com/yourusername/your-repo.git
```

### Setting Up a Virtual Environment
- Create a Virtual Environment:
```bash 
python -m venv venv
```
- Activate the Virtual Environment:
    - On macOS/Linux:
       ```bash
        source venv/bin/activate
      ```
    - On Windows:
     ```bash
        venv\Scripts\activate
  ```
  
  - Installing Dependencies:
      ```bash 
    pip install -r requirements.txt 
    ```
### Configuring the Database
  - Set Up MySQL Database:
      Create a MySQL database and user with appropriate permissions. Update the following configuration variables in app.py or in your environment variables:
       ```bash 
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'myuser'
    app.config['MYSQL_PASSWORD'] = 'mypassword'
    app.config['MYSQL_DB'] = 'shop' 
       ```
  - run myql_setup_file.sql in mysql workbench to have tables and use data.scv file import wizard to update coffee_items data and it will have all data about products then.


### Running the Application

```python main.py```

Visit http://127.0.0.1:5000/ in your web browser to access the application.

## Usage
- Signup: Navigate to /log-up to create a new account.
- Login: Navigate to /signin to log in to your account.
- Cart: Add items to your cart and view them at /cart.
- Checkout: Proceed with your order at /checkout.
- Search: Use the search functionality at /search.

## SOLID Principles Applied
### Single Responsibility Principle (SRP)
Each module and function in this application adheres to the Single Responsibility Principle:

- User Management: Handles signup, login, and session management.
- Cart Management: Manages cart items and their quantities.
- Order Processing: Handles checkout and order placement.
- Error Handling: Manages custom error responses and logging. 
- 
### Open/Closed Principle (OCP)

The application is designed to be open for extension but closed for modification. For example, adding new features (like new types of items or payment methods) can be done by extending the existing functionality without modifying the core codebase significantly.

### Liskov Substitution Principle (LSP)
The application uses Flask’s built-in mechanisms to ensure that subclasses (such as custom error handlers) can replace base classes (like default error handling) without altering the application's behavior.

### Interface Segregation Principle (ISP)
Flask’s route handlers are designed to manage specific functionalities (like /login or /cart) without forcing users to depend on methods they don’t use. Each route is responsible for a specific task, adhering to this principle.

### Dependency Inversion Principle (DIP)
The application’s components, such as database interactions and session management, are abstracted behind Flask’s provided interfaces and extensions (e.g., flask_mysqldb, flask_bcrypt). This design allows for easier swapping out of components if needed (e.g., changing the database backend) with minimal changes to the high-level logic.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


