-- Drop existing procedures if they exist
DROP PROCEDURE IF EXISTS CalculateTotalRevenue;
DROP PROCEDURE IF EXISTS GetCustomerBookingHistory;

-- Create procedure for calculating revenue
DELIMITER //
CREATE PROCEDURE CalculateTotalRevenue(
    IN theatre_id INT,
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        m.title as movie_title,
        s.datetime as show_datetime,
        s.language,
        COUNT(DISTINCT b.booking_id) as total_bookings,
        COUNT(bs.seat_no) as seats_booked,
        s.price as ticket_price,
        (COUNT(bs.seat_no) * s.price) as total_revenue
    FROM Shows s
    LEFT JOIN Booking b ON s.show_id = b.show_id AND b.payment_status = 'completed'
    LEFT JOIN Movie m ON s.m_id = m.m_id
    LEFT JOIN Booking_Seats bs ON b.booking_id = bs.booking_id
    WHERE s.tid = theatre_id 
    AND DATE(s.datetime) BETWEEN start_date AND end_date
    GROUP BY s.show_id, m.title, s.datetime, s.language, s.price
    ORDER BY s.datetime;
END //

-- Create procedure for getting customer booking history
CREATE PROCEDURE GetCustomerBookingHistory(
    IN customer_id INT
)
BEGIN
    SELECT 
        b.booking_id,
        m.title as movie_title,
        t.t_name as theatre_name,
        t.location as theatre_location,
        s.datetime as show_datetime,
        s.language,
        s.price as ticket_price,
        GROUP_CONCAT(bs.seat_no ORDER BY bs.seat_no) as booked_seats,
        COUNT(bs.seat_no) as total_seats,
        (COUNT(bs.seat_no) * s.price) as total_amount,
        b.payment_status
    FROM Booking b
    JOIN Shows s ON b.show_id = s.show_id
    JOIN Movie m ON s.m_id = m.m_id
    JOIN Theatre t ON s.tid = t.tid
    JOIN Booking_Seats bs ON b.booking_id = bs.booking_id
    WHERE b.c_id = customer_id
    GROUP BY b.booking_id, m.title, t.t_name, t.location, s.datetime, s.language, s.price, b.payment_status
    ORDER BY s.datetime DESC;
END //

DELIMITER ; 