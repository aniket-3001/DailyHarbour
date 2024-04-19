create database if not exists DailyHarbour;
use DailyHarbour;


CREATE TABLE IF NOT EXISTS user (
    user_id INT AUTO_INCREMENT,
    mobile_number VARCHAR(10) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    middle_name VARCHAR(20),
    last_name VARCHAR(20),
    password_hash VARCHAR(100) NOT NULL,
    gender VARCHAR(20) NOT NULL CHECK (LOWER(gender) IN ("male", "female", "other", "non-binary", "prefer not to say")),
    date_of_birth DATE NOT NULL,
    UNIQUE (mobile_number),
    PRIMARY KEY (user_id)
);


CREATE TABLE IF NOT EXISTS category (
    category_id INT NOT NULL,
    category_name VARCHAR(50) NOT NULL,
    subcategory_level_1 VARCHAR(50),
    subcategory_level_2 VARCHAR(50),
    discount_percentage FLOAT CHECK(discount_percentage >= 0),
    PRIMARY KEY (category_id)
);


INSERT INTO category (category_id, category_name, subcategory_level_1, subcategory_level_2, discount_percentage)
VALUES
(1, 'Electronics', 'Smartphones', 'Accessories', 10.5),
(2, 'Food', 'dairy products', 'solid products', 15.0),
(3, 'Medical', 'Emergency', null, 8.75),
(4, 'Bathroom', 'Oral Hygiene', null, 5.25),
(5, 'Fruits and Vegetables', 'Fresh Fruits', 'Organic Vegetables', 12.0);


CREATE TABLE IF NOT EXISTS product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(50) NOT NULL,
    unit_of_measure VARCHAR(20),
    quantity_per_unit INT NOT NULL CHECK(quantity_per_unit > 0),
    available_units INT NOT NULL CHECK(available_units >= 0),
    mrp FLOAT NOT NULL CHECK(mrp > 0),
    selling_price FLOAT NOT NULL CHECK(selling_price >= 0),
    manufacturer_name VARCHAR(20),
    product_description VARCHAR(500),
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE ON UPDATE CASCADE
);


INSERT INTO product (product_name, unit_of_measure, quantity_per_unit, available_units, mrp, selling_price, manufacturer_name, product_description, category_id)
VALUES
('Headphones', 'Single Unit', 1, 100000, 49.99, 39.99, 'SoundTech', 'Sleek and lightweight headphones for on-the-go audio enjoyment.', 1),
('Charger', 'Single Unit', 1, 100000, 19.99, 14.99, 'PowerTech', 'Universal charger compatible with various devices.', 2),
('Potatoes', 'Per Kg', 1, 100000, 1.99, 1.49, 'FarmFresh', 'Freshly harvested potatoes from local farms.', 3),
('Soap', 'Single Unit', 1, 100000, 2.99, 2.49, 'CleanCare', 'Gentle and moisturizing soap for daily use.', 4),
('Spinach', 'Per Bunch', 1, 100000, 3.99, 2.99, 'GreenHarvest', 'Organically grown spinach packed with nutrients.', 5),
('Medical Kit', 'Single Unit', 1, 100000, 29.99, 24.99, 'MediAid', 'Comprehensive first aid kit for emergencies.', 3),
('Watch', 'Single Unit', 1, 100000, 99.99, 79.99, 'TimeWise', 'Stylish and durable wristwatch for everyday wear.', 2),
('Perfume', 'Per Bottle', 1, 100000, 149.99, 129.99, 'Chanel', 'Elegant fragrance with floral and woody notes.', 1),
('Toothbrush', 'Single Unit', 1, 100000, 3.49, 2.99, 'CleanCare', 'Soft-bristled toothbrush for gentle cleaning.', 2);


-- Shipping address is a multivariate attribute of user, hence making it a separate entity
CREATE TABLE IF NOT EXISTS shipping_address (
    user_id INT,
    address_name VARCHAR(20) NOT NULL,
    address_line_1 VARCHAR(100) NOT NULL,
    address_line_2 VARCHAR(100),
    address_line_3 VARCHAR(100),
    city VARCHAR(20) NOT NULL,
    state VARCHAR(20) NOT NULL,
    pincode VARCHAR(6) NOT NULL CHECK (LENGTH(pincode) = 6),
    PRIMARY KEY (user_id, address_name),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS coupon (
    coupon_code VARCHAR(10) NOT NULL,
    coupon_description VARCHAR(200),
    minimum_order_value FLOAT CHECK(minimum_order_value > 0),
    validity_status BOOLEAN,
    discount_percentage FLOAT CHECK(discount_percentage >= 0),
    discount_amount FLOAT CHECK(discount_amount >= 0),
    PRIMARY KEY (coupon_code)
);


INSERT INTO coupon (coupon_code, coupon_description, minimum_order_value, validity_status, discount_percentage, discount_amount)
VALUES
('SAVE10', 'Get 10% off on your order!', 50.0, true, 10.0, 0.0),
('FREESHIP', 'Free shipping on orders above $30', 30.0, true, 0.0, 0.0),
('SALE15', 'Exclusive 15% off for a limited time', 75.0, true, 15.0, 0.0),
('SPECIAL20', 'Special discount: 20% off on selected items', 100.0, true, 20.0, 0.0),
('WELCOME5', 'Welcome discount: 5% off on your first order', 20.0, true, 5.0, 0.0);


CREATE TABLE IF NOT EXISTS order_details (
    order_no INT AUTO_INCREMENT,
    user_id INT NOT NULL,
    coupon_code VARCHAR(10),
    address_name VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    total_number_of_items INT NOT NULL CHECK(total_number_of_items > 0),
    order_value FLOAT NOT NULL CHECK(order_value > 0),
    delivery_charge FLOAT NOT NULL CHECK(delivery_charge >= 0),
    PRIMARY KEY (order_no),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (coupon_code) REFERENCES coupon(coupon_code) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (user_id, address_name) REFERENCES shipping_address(user_id, address_name) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS order_products (
    order_no INT,
    product_id INT,
    number_of_units INT NOT NULL CHECK(number_of_units > 0),
    price_per_unit FLOAT NOT NULL CHECK(price_per_unit >= 0),
    PRIMARY KEY (order_no, product_id),
    FOREIGN KEY (order_no) REFERENCES order_details(order_no) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS shipment (
    order_no INT,
    shipment_status VARCHAR(20) NOT NULL,
    delivery_date_time DATETIME NOT NULL,
    PRIMARY KEY (order_no),
    FOREIGN KEY (order_no) REFERENCES order_details(order_no) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS add_to_cart (
    user_id INT,
    product_id INT,
    number_of_units INT NOT NULL, -- The number of units of that particular product selected by the user
    PRIMARY KEY (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE
);