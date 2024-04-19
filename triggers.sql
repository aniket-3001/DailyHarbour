use DailyHarbour;


-- 1) Deplete the total stock once the user adds respective items to cart
DELIMITER //

CREATE TRIGGER deplete_stock_on_add_to_cart
AFTER INSERT ON add_to_cart
FOR EACH ROW
BEGIN
    UPDATE product
    SET available_units = available_units - NEW.number_of_units
    WHERE product_id = NEW.product_id;
END;
//

DELIMITER ;

-- 2) Update the total stock when the user times out and the items are removed from the cart
DELIMITER //

CREATE TRIGGER update_stock_on_cart_timeout
AFTER DELETE ON add_to_cart
FOR EACH ROW
BEGIN
    UPDATE product
    SET available_units = available_units + OLD.number_of_units
    WHERE product_id = OLD.product_id;
END;
//

DELIMITER ;
