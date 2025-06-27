import re
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class BookingSeats(db.Model):
    __tablename__ = 'BookingSeats'
    booking_seat_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('Booking.booking_id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    
    def __init__(self, booking_id, seat_number):
        if not re.match(r'^[A-Z][0-9]+$', seat_number):
            raise ValueError('Invalid seat format. Must be in format A1, B2, etc.')
        self.booking_id = booking_id
        self.seat_number = seat_number
    
    def __repr__(self):
        return f'<BookingSeat {self.seat_number}>' 