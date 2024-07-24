CREATE TABLE coffee_items (
    entity_id INT AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(255) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    shortdesc TEXT,
    price DECIMAL(10, 4) NOT NULL,
    link VARCHAR(255),
    image VARCHAR(255),
    Brand VARCHAR(255),
    Rating INT,
    CaffeineType VARCHAR(50),
    Count INT,
    Flavored VARCHAR(10),
    Seasonal VARCHAR(10),
    Instock VARCHAR(10),
    Facebook VARCHAR(255),
    IsKCup VARCHAR(10)
) ENGINE=InnoDB;

-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- Create brands table
CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT
) ENGINE=InnoDB;

-- Create cart table
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES coffee_items(entity_id),
    UNIQUE (user_id, item_id)
) ENGINE=InnoDB;

-- Create orders table
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Shipped', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- Create order_items table
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (item_id) REFERENCES coffee_items(entity_id)
) ENGINE=InnoDB;

INSERT INTO brands (name)
SELECT DISTINCT Brand FROM coffee_items;
ALTER TABLE orders
ADD COLUMN house VARCHAR(255) NOT NULL,
ADD COLUMN street VARCHAR(255) NOT NULL,
ADD COLUMN city VARCHAR(255) NOT NULL,
ADD COLUMN postal_code VARCHAR(20) NOT NULL,
ADD COLUMN state VARCHAR(255) NOT NULL,
ADD COLUMN country VARCHAR(255) NOT NULL;

SELECT c.item_id, c.quantity, co.price FROM cart c
                JOIN coffee_items co ON c.item_id = co.entity_id
                WHERE c.user_id = 1;

SELECT * FROM brands;
SELECT * FROM cart;
SELECT * FROM users;
SELECT * FROM coffee_items;
select * from orders;
select * from order_items;



