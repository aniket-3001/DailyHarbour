use database DailyHarbour;

-- 1) Empty the cart for the user once they place the order, i.e a record has been inserted into the order_details table
CREATE TRIGGER empty_cart_after_order
AFTER INSERT ON order_details
FOR EACH ROW
BEGIN
    DELETE FROM add_to_cart WHERE user_id = NEW.user_id;
END;


-- 2) Deplete the total stock once the user adds respective items to cart
CREATE TRIGGER deplete_stock_on_add_to_cart
AFTER INSERT ON add_to_cart
FOR EACH ROW
BEGIN
    UPDATE product
    SET available_units = available_units - NEW.number_of_units
    WHERE product_id = NEW.product_id;
END;


-- 3) Update the total stock when user gets timed out and the items are removed from the cart
CREATE TRIGGER update_stock_on_cart_timeout
AFTER DELETE ON add_to_cart
FOR EACH ROW
BEGIN
    UPDATE product
    SET available_units = available_units + OLD.number_of_units
    WHERE product_id = OLD.product_id;
END;