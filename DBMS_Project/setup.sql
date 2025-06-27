DROP DATABASE IF EXISTS theatre_booking;
CREATE DATABASE theatre_booking;
USE theatre_booking;

CREATE TABLE Admins (
    admin_id INT PRIMARY KEY,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE Theatre (
    tid INT PRIMARY KEY AUTO_INCREMENT,
    t_name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    admin_id INT NOT NULL,
    total_seats INT NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES Admins(admin_id)
);

CREATE TABLE Movie (
    m_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    release_date DATE NOT NULL,
    director VARCHAR(50) NOT NULL,
    actors JSON NOT NULL,
    admin_id INT NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES Admins(admin_id)
);

CREATE TABLE Shows (
    show_id INT PRIMARY KEY AUTO_INCREMENT,
    m_id INT NOT NULL,
    tid INT NOT NULL,
    datetime DATETIME NOT NULL,
    language VARCHAR(20) NOT NULL,
    price DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (m_id) REFERENCES Movie(m_id),
    FOREIGN KEY (tid) REFERENCES Theatre(tid)
);

CREATE TABLE Customer (
    c_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE Booking (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    c_id INT NOT NULL,
    show_id INT NOT NULL,
    seats JSON NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    FOREIGN KEY (c_id) REFERENCES Customer(c_id),
    FOREIGN KEY (show_id) REFERENCES Shows(show_id)
);

CREATE TABLE Booking_Seats (
    booking_id INT,
    seat_no VARCHAR(10),
    PRIMARY KEY (booking_id, seat_no),
    FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE
);

-- Insert default admin
INSERT INTO Admins (admin_id, password) VALUES 
(1, 'admin@123'),
(2, 'secureP@ss');

-- Insert test movies
INSERT INTO Movie (title, release_date, director, actors, admin_id) VALUES 
('Dragon', '2025-04-26', 'Ashwath Marimuthu', JSON_ARRAY('Pradeep'), 1),
('Baaghi', '2025-03-01', 'Deepak Shiv', JSON_ARRAY('Salman Khan'), 1),
('Baaghi', '2025-02-07', 'Sabbir Khan', JSON_ARRAY('Tiger Shroff'), 1);

-- Insert test theatres
INSERT INTO Theatre (tid, t_name, location, admin_id, total_seats) VALUES 
(1, 'Satyam Cinemas', 'Chennai', 1, 350),
(2, 'Gokul Theatre', 'Madurai', 2, 180),
(3, 'Satyam Cinemas', 'Hyderabad', 1, 300);

-- Insert test shows
INSERT INTO Shows (show_id, m_id, tid, datetime, language, price) VALUES 
(1, 1, 1, '2025-05-10 18:00:00', 'Tamil', 150),
(2, 2, 2, '2025-05-11 15:30:00', 'Tamil', 250);

-- Insert test customers
INSERT INTO Customer (c_id, name, email, password) VALUES 
(1, 'Rahul', 'rahul@gmail.com', 'pass123'),
(2, 'Mohan', 'mohan@gmail.com', 'pass456');

-- Insert test bookings
INSERT INTO Booking (booking_id, c_id, show_id, seats, payment_status) VALUES 
(1, 1, 1, '["A1", "A2"]', 'completed'),
(2, 2, 2, '["B3"]', 'pending');

-- Insert test booking seats
INSERT INTO Booking_Seats (booking_id, seat_no) VALUES 
(1, 'A1'),
(1, 'A2'),
(2, 'B3');

DELIMITER //

CREATE PROCEDURE BookSeats(
    IN p_show_id INT,
    IN p_customer_id INT,
    IN p_seats JSON,
    OUT p_success BOOLEAN,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_theatre_id INT;
    DECLARE v_total_seats INT;
    DECLARE v_booked_seats INT;
    
    -- Get theatre ID and total seats for the show
    SELECT t.tid, t.total_seats INTO v_theatre_id, v_total_seats
    FROM Shows s
    JOIN Theatre t ON s.tid = t.tid
    WHERE s.show_id = p_show_id;
    
    -- Count currently booked seats for this show
    SELECT COUNT(*) INTO v_booked_seats
    FROM Booking b
    WHERE b.show_id = p_show_id;
    
    -- Check if total seats after booking would exceed theatre capacity
    IF (v_booked_seats + JSON_LENGTH(p_seats)) > v_total_seats THEN
        SET p_success = FALSE;
        SET p_message = 'Not enough seats available';
    ELSE
        -- Create the booking
        INSERT INTO Booking (c_id, show_id, seats, payment_status)
        VALUES (p_customer_id, p_show_id, p_seats, 'pending');
        
        SET p_success = TRUE;
        SET p_message = 'Booking successful';
    END IF;
END //

DELIMITER ; 