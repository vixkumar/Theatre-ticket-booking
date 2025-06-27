-- Drop existing objects first
DROP TRIGGER IF EXISTS after_booking_insert;
DROP FUNCTION IF EXISTS GetAvailableSeats;
DROP PROCEDURE IF EXISTS CalculateTotalRevenue;
DROP PROCEDURE IF EXISTS GetCustomerBookingHistory;

-- Stored Procedure: CalculateTotalRevenue
DELIMITER //
CREATE PROCEDURE CalculateTotalRevenue(
    IN theatre_id INT,
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        m.title as show_title,
        s.datetime as show_date,
        SUM(s.price * COUNT(bs.seat_no)) as total_revenue
    FROM Booking b
    JOIN Shows s ON b.show_id = s.show_id
    JOIN Movie m ON s.m_id = m.m_id
    JOIN Booking_Seats bs ON b.booking_id = bs.booking_id
    WHERE s.tid = theatre_id 
    AND b.payment_status = 'completed'
    AND DATE(s.datetime) BETWEEN start_date AND end_date
    GROUP BY s.show_id, m.title, s.datetime
    ORDER BY s.datetime;
END //
DELIMITER ;

-- Function: GetAvailableSeats
DELIMITER //
CREATE FUNCTION GetAvailableSeats(show_id INT) 
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total_seats INT;
    DECLARE booked_seats INT;
    
    -- Get total seats from theatre
    SELECT t.total_seats INTO total_seats
    FROM Shows s
    JOIN Theatre t ON s.tid = t.tid
    WHERE s.show_id = show_id;
    
    -- Get booked seats
    SELECT COUNT(*) INTO booked_seats
    FROM Booking_Seats bs
    JOIN Booking b ON bs.booking_id = b.booking_id
    WHERE b.show_id = show_id;
    
    RETURN total_seats - booked_seats;
END //
DELIMITER ;

-- Trigger: UpdateSeatAvailability
DELIMITER //
CREATE TRIGGER after_booking_insert
AFTER INSERT ON Booking_Seats
FOR EACH ROW
BEGIN
    DECLARE show_id INT;
    
    -- Get the show_id for this booking
    SELECT b.show_id INTO show_id
    FROM Booking b
    WHERE b.booking_id = NEW.booking_id;
    
    -- Check if seats are available
    IF GetAvailableSeats(show_id) < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No seats available for this show';
    END IF;
END //
DELIMITER ;

-- Cursor: GetCustomerBookingHistory
DELIMITER //
CREATE PROCEDURE GetCustomerBookingHistory(IN customer_id INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE booking_id INT;
    DECLARE show_id INT;
    DECLARE payment_status VARCHAR(20);
    DECLARE seat_numbers VARCHAR(1000);
    DECLARE total_amount DECIMAL(10,2);
    
    -- Cursor for getting booking details
    DECLARE booking_cursor CURSOR FOR
        SELECT 
            b.booking_id,
            b.show_id,
            b.payment_status,
            GROUP_CONCAT(bs.seat_no) as seat_numbers,
            COUNT(bs.seat_no) * s.price as total_amount
        FROM Booking b
        JOIN Shows s ON b.show_id = s.show_id
        JOIN Booking_Seats bs ON b.booking_id = bs.booking_id
        WHERE b.c_id = customer_id
        GROUP BY b.booking_id, b.show_id, b.payment_status, s.price;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Create temporary table for results
    DROP TEMPORARY TABLE IF EXISTS temp_booking_history;
    CREATE TEMPORARY TABLE temp_booking_history (
        booking_id INT,
        movie_title VARCHAR(100),
        theatre_name VARCHAR(100),
        show_datetime DATETIME,
        seat_numbers VARCHAR(1000),
        total_amount DECIMAL(10,2),
        payment_status VARCHAR(20),
        booking_date DATETIME
    );
    
    OPEN booking_cursor;
    
    read_loop: LOOP
        FETCH booking_cursor INTO booking_id, show_id, payment_status, seat_numbers, total_amount;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Insert booking details into temporary table
        INSERT INTO temp_booking_history
        SELECT 
            b.booking_id,
            m.title,
            t.t_name,
            s.datetime,
            seat_numbers,
            total_amount,
            b.payment_status,
            b.booking_date
        FROM Booking b
        JOIN Shows s ON b.show_id = s.show_id
        JOIN Movie m ON s.m_id = m.m_id
        JOIN Theatre t ON s.tid = t.tid
        WHERE b.booking_id = booking_id;
    END LOOP;
    
    CLOSE booking_cursor;
    
    -- Return results
    SELECT * FROM temp_booking_history ORDER BY show_datetime DESC;
    
    -- Clean up
    DROP TEMPORARY TABLE IF EXISTS temp_booking_history;
END //
DELIMITER ; 