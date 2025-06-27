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
        SUM(s.price * COUNT(bs.seat_number)) as total_revenue
    FROM Booking b
    JOIN Shows s ON b.show_id = s.show_id
    JOIN Movie m ON s.m_id = m.m_id
    JOIN BookingSeats bs ON b.booking_id = bs.booking_id
    WHERE s.tid = theatre_id 
    AND b.payment_status = 'completed'
    AND DATE(s.datetime) BETWEEN start_date AND end_date
    GROUP BY s.show_id, m.title, s.datetime
    ORDER BY s.datetime;
END //

DELIMITER ; 