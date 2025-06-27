from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import re
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nopainnogain#123@localhost/theatre_booking?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class Admin(UserMixin, db.Model):
    __tablename__ = 'Admins'
    admin_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.admin_id)

class Theatre(db.Model):
    __tablename__ = 'Theatre'
    tid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    t_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('Admins.admin_id'), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    admin = db.relationship('Admin', backref='theatres')

class Movie(db.Model):
    __tablename__ = 'Movie'
    m_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    director = db.Column(db.String(50), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('Admins.admin_id'), nullable=False)
    actors = db.Column(db.JSON, nullable=True)
    admin = db.relationship('Admin', backref='movies')

    def __repr__(self):
        return f'<Movie {self.title}>'

    def get_actors(self):
        if isinstance(self.actors, str):
            try:
                return json.loads(self.actors)
            except json.JSONDecodeError:
                return []
        return self.actors if self.actors else []

    def set_actors(self, actor_list):
        if isinstance(actor_list, str):
            self.actors = json.dumps([actor.strip() for actor in actor_list.split(',')])
        else:
            self.actors = json.dumps(actor_list)

class Shows(db.Model):
    __tablename__ = 'Shows'
    show_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    m_id = db.Column(db.Integer, db.ForeignKey('Movie.m_id'), nullable=False)
    tid = db.Column(db.Integer, db.ForeignKey('Theatre.tid'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    language = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(8,2), nullable=False)
    movie = db.relationship('Movie', backref='shows')
    theatre = db.relationship('Theatre', backref='shows')

class Customer(UserMixin, db.Model):
    __tablename__ = 'Customer'
    c_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def get_id(self):
        return str(self.c_id)

class Booking(db.Model):
    __tablename__ = 'Booking'
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    c_id = db.Column(db.Integer, db.ForeignKey('Customer.c_id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('Shows.show_id'), nullable=False)
    payment_status = db.Column(db.String(20), nullable=False)
    customer = db.relationship('Customer', backref='bookings')
    show = db.relationship('Shows', backref='bookings')
    booking_seats = db.relationship('BookingSeats', backref='booking', cascade='all, delete-orphan')

    def __init__(self, c_id, show_id, payment_status):
        self.c_id = c_id
        self.show_id = show_id
        self.payment_status = payment_status

class BookingSeats(db.Model):
    __tablename__ = 'Booking_Seats'
    booking_id = db.Column(db.Integer, db.ForeignKey('Booking.booking_id'), primary_key=True)
    seat_no = db.Column(db.String(10), primary_key=True)
    
    def __init__(self, booking_id, seat_number):
        if not re.match(r'^[A-Z][0-9]+$', seat_number):
            raise ValueError('Invalid seat format. Must be in format A1, B2, etc.')
        self.booking_id = booking_id
        self.seat_no = seat_number
    
    def __repr__(self):
        return f'<BookingSeat {self.seat_no}>'

@login_manager.user_loader
def load_user(user_id):
    if session.get('user_type') == 'admin':
        return Admin.query.get(int(user_id))
    return Customer.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Login attempt - Type: {user_type}, Email/ID: {email}, Password: {password}")

        if user_type == 'admin':
            try:
                admin_id = int(email)  # Convert email field to admin_id
                admin = Admin.query.filter_by(admin_id=admin_id).first()
                print(f"Found admin: {admin}")
                if admin and admin.password == password:
                    print("Password match successful")
                    login_user(admin)
                    session['user_type'] = 'admin'
                    return redirect(url_for('admin_dashboard'))
                else:
                    print("Password match failed")
            except ValueError:
                print("Invalid admin ID format")
                flash('Invalid admin ID format')
        else:
            customer = Customer.query.filter_by(email=email).first()
            if customer and customer.password == password:
                login_user(customer)
                session['user_type'] = 'customer'
                return redirect(url_for('user_dashboard'))

        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if Customer.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        new_customer = Customer(name=name, email=email, password=password)
        db.session.add(new_customer)
        db.session.commit()

        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Get theatres managed by this admin
        theatres = Theatre.query.filter_by(admin_id=current_user.admin_id).all()
        theatre_ids = [theatre.tid for theatre in theatres]
        
        # Get movies belonging to this admin
        movies = Movie.query.filter_by(admin_id=current_user.admin_id).all()
        
        # Get shows in this admin's theatres
        shows = Shows.query.filter(Shows.tid.in_(theatre_ids)).all()
        
        return render_template('admin_dashboard.html', 
                             theatres=theatres,
                             movies=movies,
                             shows=shows)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/admin/add_movie', methods=['POST'])
@login_required
def add_movie():
    if session.get('user_type') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        title = request.form.get('title')
        release_date = request.form.get('release_date')
        director = request.form.get('director')
        actors = request.form.get('actors')

        if not all([title, release_date, director, actors]):
            flash('All fields are required')
            return redirect(url_for('admin_dashboard'))

        # Convert string date to datetime
        try:
            release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid release date format')
            return redirect(url_for('admin_dashboard'))

        # Check if movie with same title and release date already exists for this admin
        existing_movie = Movie.query.filter_by(
            title=title,
            release_date=release_date,
            admin_id=current_user.admin_id
        ).first()
        
        if existing_movie:
            flash('A movie with this title and release date already exists')
            return redirect(url_for('admin_dashboard'))

        # Create new movie
        new_movie = Movie(
            title=title,
            release_date=release_date,
            director=director,
            admin_id=current_user.admin_id
        )
        new_movie.set_actors(actors)
        
        db.session.add(new_movie)
        db.session.commit()
        flash('Movie added successfully!')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding movie: {str(e)}')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_show', methods=['POST'])
@login_required
def add_show():
    if session.get('user_type') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        m_id = request.form.get('m_id')
        tid = request.form.get('tid')
        datetime_str = request.form.get('datetime')
        language = request.form.get('language')
        price = request.form.get('price')

        if not all([m_id, tid, datetime_str, language, price]):
            flash('All fields are required')
            return redirect(url_for('admin_dashboard'))

        # Verify movie exists
        movie = Movie.query.get(m_id)
        if not movie:
            flash('Invalid movie selection')
            return redirect(url_for('admin_dashboard'))

        # Verify theatre belongs to current admin
        theatre = Theatre.query.get(tid)
        if not theatre or theatre.admin_id != current_user.admin_id:
            flash('Invalid theatre selection')
            return redirect(url_for('admin_dashboard'))

        try:
            show_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
            if show_datetime < datetime.now():
                flash('Show time must be in the future')
                return redirect(url_for('admin_dashboard'))
        except ValueError:
            flash('Invalid date/time format')
            return redirect(url_for('admin_dashboard'))

        try:
            price = float(price)
            if price <= 0:
                raise ValueError("Price must be positive")
        except ValueError:
            flash('Invalid price')
            return redirect(url_for('admin_dashboard'))

        new_show = Shows(
            m_id=m_id,
            tid=tid,
            datetime=show_datetime,
            language=language,
            price=price
        )
        db.session.add(new_show)
        db.session.commit()
        flash('Show added successfully!')

    except Exception as e:
        print("Error adding show:", str(e))
        db.session.rollback()
        flash(f'Error adding show: {str(e)}')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_theatre', methods=['POST'])
@login_required
def add_theatre():
    if session.get('user_type') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        print("Received theatre data:", request.form)  # Debug print
        
        t_name = request.form.get('t_name')
        location = request.form.get('location')
        total_seats = request.form.get('total_seats')

        if not all([t_name, location, total_seats]):
            flash('All fields are required')
            return redirect(url_for('admin_dashboard'))

        # Convert total_seats to integer
        try:
            total_seats = int(total_seats)
            if total_seats <= 0:
                raise ValueError("Total seats must be positive")
        except ValueError as e:
            flash('Invalid number of seats')
            return redirect(url_for('admin_dashboard'))

        new_theatre = Theatre(
            t_name=t_name,
            location=location,
            admin_id=current_user.admin_id,
            total_seats=total_seats
        )
        
        print("Creating new theatre:", vars(new_theatre))  # Debug print
        db.session.add(new_theatre)
        db.session.commit()
        print("Theatre added successfully!")  # Debug print
        flash('Theatre added successfully!')

    except Exception as e:
        print("Error adding theatre:", str(e))  # Debug print
        db.session.rollback()
        flash(f'Error adding theatre: {str(e)}')

    return redirect(url_for('admin_dashboard'))

@app.route('/edit_theatre/<int:tid>', methods=['GET', 'POST'])
@login_required
def edit_theatre(tid):
    if session.get('user_type') != 'admin':
        flash('Access denied. Admin login required.', 'danger')
        return redirect(url_for('login'))
    
    theatre = Theatre.query.get_or_404(tid)
    
    # Verify that the theatre belongs to the logged-in admin
    if theatre.admin_id != current_user.admin_id:
        flash('You do not have permission to edit this theatre.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            theatre.t_name = request.form['t_name']
            theatre.location = request.form['location']
            theatre.total_seats = int(request.form['total_seats'])
            
            db.session.commit()
            flash('Theatre updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating theatre: {str(e)}', 'danger')
    
    return render_template('edit_theatre.html', theatre=theatre)

@app.route('/admin/delete_theatre/<int:tid>')
@login_required
def delete_theatre(tid):
    theatre = Theatre.query.get_or_404(tid)
    if theatre.admin_id != current_user.admin_id:
        flash('You are not authorized to delete this theatre')
        return redirect(url_for('admin_dashboard'))
    
    # Check if theatre has any shows
    shows = Shows.query.filter_by(tid=tid).first()
    if shows:
        flash('Cannot delete theatre as it has shows scheduled')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(theatre)
    db.session.commit()
    flash('Theatre deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('user_type') != 'customer':
        return redirect(url_for('index'))
    
    # Get all unique locations from theatres
    locations = db.session.query(Theatre.location).distinct().all()
    locations = [loc[0] for loc in locations]
    
    # Get selected location from query parameter
    selected_location = request.args.get('location')
    
    # Get user's bookings
    user_bookings = Booking.query.filter_by(c_id=current_user.c_id).all()
    booking_details = []
    
    for booking in user_bookings:
        show = Shows.query.get(booking.show_id)
        movie = Movie.query.get(show.m_id)
        theatre = Theatre.query.get(show.tid)
        seats = BookingSeats.query.filter_by(booking_id=booking.booking_id).all()
        
        booking_details.append({
            'booking_id': booking.booking_id,
            'movie_title': movie.title,
            'theatre_name': theatre.t_name,
            'show_time': show.datetime,
            'seats': [seat.seat_no for seat in seats],
            'total_amount': len(seats) * float(show.price),
            'payment_status': booking.payment_status
        })
    
    if selected_location:
        # Get theatres in the selected location
        theatres = Theatre.query.filter_by(location=selected_location).all()
        
        # Get shows for each theatre
        theatre_shows = {}
        for theatre in theatres:
            shows = Shows.query.filter_by(tid=theatre.tid).all()
            theatre_shows[theatre.tid] = shows
        
        return render_template('user_dashboard.html', 
                             theatres=theatres,
                             theatre_shows=theatre_shows,
                             selected_location=selected_location,
                             locations=locations,
                             bookings=booking_details)
    
    # If no location selected, show location selection page
    return render_template('user_dashboard.html', 
                         locations=locations,
                         selected_location=None,
                         bookings=booking_details)

@app.route('/book_ticket/<int:show_id>', methods=['GET', 'POST'])
@login_required
def book_ticket(show_id):
    if session.get('user_type') != 'customer':
        flash('Please login as a customer to book tickets', 'danger')
        return redirect(url_for('login'))
    
    show = Shows.query.get_or_404(show_id)
    theatre = Theatre.query.get(show.tid)
    movie = Movie.query.get(show.m_id)
    
    if request.method == 'POST':
        seats = request.form.getlist('seats[]')
        print(f"Selected seats: {seats}")  # Debug print
        
        if not seats:
            flash('Please select at least one seat', 'danger')
            return redirect(url_for('book_ticket', show_id=show_id))
        
        # Calculate total amount
        total_amount = len(seats) * float(show.price)
        print(f"Total amount: {total_amount}")  # Debug print
        
        # Redirect to payment confirmation
        return render_template('payment_confirmation.html',
                             show=show,
                             theatre=theatre,
                             movie=movie,
                             seats=seats,
                             total_amount=total_amount)
    
    # Get booked seats for this show
    booked_seats = db.session.query(BookingSeats.seat_no)\
        .join(Booking, BookingSeats.booking_id == Booking.booking_id)\
        .filter(Booking.show_id == show_id)\
        .all()
    booked_seats = [seat[0] for seat in booked_seats]
    print(f"Booked seats: {booked_seats}")  # Debug print
    
    # Generate all possible seats based on theatre capacity
    all_seats = []
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    seats_per_row = theatre.total_seats // len(rows)
    
    for row in rows:
        for num in range(1, seats_per_row + 1):
            seat = f"{row}{num}"
            all_seats.append({
                'number': seat,
                'booked': seat in booked_seats
            })
    
    return render_template('book_ticket.html', 
                         show=show, 
                         theatre=theatre, 
                         movie=movie,
                         seats=all_seats)

@app.route('/confirm_booking/<int:show_id>', methods=['POST'])
@login_required
def confirm_booking(show_id):
    if session.get('user_type') != 'customer':
        flash('Please login as a customer to book tickets', 'danger')
        return redirect(url_for('login'))
    
    try:
        show = Shows.query.get_or_404(show_id)
        seats = request.form.get('seats')
        print(f"Received seats in confirm_booking: {seats}")  # Debug print
        
        if not seats:
            flash('No seats selected', 'danger')
            return redirect(url_for('book_ticket', show_id=show_id))
        
        seats = seats.split(',')
        print(f"Split seats: {seats}")  # Debug print
        
        # Check if seats are already booked
        booked_seats = db.session.query(BookingSeats.seat_no)\
            .join(Booking, BookingSeats.booking_id == Booking.booking_id)\
            .filter(Booking.show_id == show_id)\
            .all()
        booked_seats = [seat[0] for seat in booked_seats]
        print(f"Currently booked seats: {booked_seats}")  # Debug print
        
        for seat in seats:
            if seat in booked_seats:
                flash(f'Seat {seat} is already booked', 'danger')
                return redirect(url_for('book_ticket', show_id=show_id))
        
        try:
            # Create new booking
            new_booking = Booking(
                c_id=current_user.c_id,
                show_id=show_id,
                payment_status='completed'
            )
            db.session.add(new_booking)
            db.session.flush()  # Get the booking_id without committing
            
            # Add seats to Booking_Seats
            for seat in seats:
                booking_seat = BookingSeats(
                    booking_id=new_booking.booking_id,
                    seat_number=seat
                )
                db.session.add(booking_seat)
            
            # Commit all changes
            db.session.commit()
            print("Successfully committed booking and seats")  # Debug print
            
            flash(f'Booking confirmed successfully! Your booking ID is: {new_booking.booking_id}', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            print(f"Error in transaction: {str(e)}")  # Debug print
            db.session.rollback()
            raise e
            
    except Exception as e:
        print(f"Error in confirm_booking: {str(e)}")  # Debug print
        db.session.rollback()
        flash(f'Error confirming booking: {str(e)}', 'danger')
        return redirect(url_for('book_ticket', show_id=show_id))

@app.route('/complete_payment/<int:booking_id>', methods=['POST'])
@login_required
def complete_payment(booking_id):
    if session.get('user_type') != 'customer':
        flash('Please login as a customer', 'danger')
        return redirect(url_for('login'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify the booking belongs to the current user
    if booking.c_id != current_user.c_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        booking.payment_status = 'completed'
        db.session.commit()
        flash('Payment completed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error completing payment. Please try again.', 'danger')
    
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

@app.route('/user/movie_theatres/<int:movie_id>')
@login_required
def movie_theatres(movie_id):
    if session.get('user_type') != 'customer':
        return redirect(url_for('index'))
    
    location = request.args.get('location')
    if not location:
        return redirect(url_for('user_dashboard'))
    
    # Get theatres in the selected location
    theatres = Theatre.query.filter_by(location=location).all()
    theatre_ids = [theatre.tid for theatre in theatres]
    
    # Get shows for this movie in these theatres
    shows = Shows.query.filter(
        Shows.m_id == movie_id,
        Shows.tid.in_(theatre_ids)
    ).all()
    
    # Get unique theatres from these shows
    show_theatre_ids = [show.tid for show in shows]
    show_theatres = Theatre.query.filter(Theatre.tid.in_(show_theatre_ids)).all()
    
    # Get movie details
    movie = Movie.query.get(movie_id)
    
    return render_template('movie_theatres.html',
                         movie=movie,
                         theatres=show_theatres,
                         shows=shows,
                         location=location)

@app.route('/movies_by_location')
def movies_by_location():
    # Get all unique locations
    locations = db.session.query(Theatre.location).distinct().all()
    locations = [loc[0] for loc in locations]
    
    # Get theatres for each location
    location_theatres = {}
    for location in locations:
        # Get theatres in this location
        theatres = Theatre.query.filter_by(location=location).all()
        
        # Get shows for each theatre
        theatre_shows = {}
        for theatre in theatres:
            shows = Shows.query.filter_by(tid=theatre.tid).all()
            theatre_shows[theatre.tid] = shows
        
        location_theatres[location] = {
            'theatres': theatres,
            'shows': theatre_shows
        }
    
    return render_template('movies_by_location.html', 
                         locations=locations, 
                         location_theatres=location_theatres)

@app.route('/movies')
def movies():
    # Get all movies
    movies = Movie.query.all()
    return render_template('movies.html', movies=movies)

@app.route('/check_seat_availability/<int:show_id>')
@login_required
def check_seat_availability(show_id):
    try:
        # Call the function to get available seats
        result = db.session.execute(
            text('SELECT GetAvailableSeats(:show_id) as available_seats'),
            {'show_id': show_id}
        ).scalar()
        
        return jsonify({
            'available_seats': result,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/customer/booking_history')
@login_required
def customer_booking_history():
    if session.get('user_type') != 'customer':
        return redirect(url_for('index'))
    
    try:
        # Call the cursor procedure to get booking history
        cursor = db.session.execute(
            text('CALL GetCustomerBookingHistory(:customer_id)'),
            {'customer_id': current_user.c_id}
        )
        booking_history = cursor.fetchall()
        
        return render_template('booking_history.html', booking_history=booking_history)
    except Exception as e:
        flash(f'Error retrieving booking history: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))

@app.route('/admin/manage_shows/<int:theatre_id>')
@login_required
def manage_shows(theatre_id):
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        theatre = Theatre.query.get_or_404(theatre_id)
        
        # Verify theatre belongs to current admin
        if theatre.admin_id != current_user.admin_id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        # Get all shows for this theatre
        shows = Shows.query.filter_by(tid=theatre_id).all()
        
        # Get all movies for show creation
        movies = Movie.query.all()
        
        return render_template('manage_shows.html',
                             theatre=theatre,
                             shows=shows,
                             movies=movies)
    except Exception as e:
        flash(f'Error loading shows: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(movie_id):
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        movie = Movie.query.get_or_404(movie_id)
        
        if request.method == 'POST':
            title = request.form.get('title')
            release_date = request.form.get('release_date')
            director = request.form.get('director')
            actors = request.form.get('actors')

            if not all([title, release_date, director, actors]):
                flash('All fields are required')
                return redirect(url_for('edit_movie', movie_id=movie_id))

            try:
                release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid release date format')
                return redirect(url_for('edit_movie', movie_id=movie_id))

            # Update movie details
            movie.title = title
            movie.release_date = release_date
            movie.director = director
            movie.set_actors(actors)

            db.session.commit()
            flash('Movie updated successfully!')
            return redirect(url_for('admin_dashboard'))

        return render_template('edit_movie.html', movie=movie)

    except Exception as e:
        flash(f'Error editing movie: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_movie/<int:movie_id>')
@login_required
def delete_movie(movie_id):
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        movie = Movie.query.get_or_404(movie_id)
        
        # Verify movie belongs to current admin
        if movie.admin_id != current_user.admin_id:
            flash('You are not authorized to delete this movie', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Get all shows for this movie
        shows = Shows.query.filter_by(m_id=movie_id).all()
        
        # Delete all bookings and booking seats for each show
        for show in shows:
            # Booking_Seats will be automatically deleted due to ON DELETE CASCADE
            Booking.query.filter_by(show_id=show.show_id).delete()
        
        # Delete all shows for this movie
        Shows.query.filter_by(m_id=movie_id).delete()
        
        # Delete the movie
        db.session.delete(movie)
        db.session.commit()
        flash('Movie deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting movie: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_show/<int:show_id>', methods=['GET', 'POST'])
@login_required
def edit_show(show_id):
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        show = Shows.query.get_or_404(show_id)
        
        # Verify show belongs to current admin's theatre
        theatre = Theatre.query.get(show.tid)
        if theatre.admin_id != current_user.admin_id:
            flash('You are not authorized to edit this show', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        if request.method == 'POST':
            m_id = request.form.get('m_id')
            datetime_str = request.form.get('datetime')
            language = request.form.get('language')
            price = request.form.get('price')

            if not all([m_id, datetime_str, language, price]):
                flash('All fields are required', 'danger')
                return redirect(url_for('edit_show', show_id=show_id))

            try:
                show_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
                if show_datetime < datetime.now():
                    flash('Show time must be in the future', 'danger')
                    return redirect(url_for('edit_show', show_id=show_id))
            except ValueError:
                flash('Invalid date/time format', 'danger')
                return redirect(url_for('edit_show', show_id=show_id))

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError("Price must be positive")
            except ValueError:
                flash('Invalid price', 'danger')
                return redirect(url_for('edit_show', show_id=show_id))

            # Update show details
            show.m_id = m_id
            show.datetime = show_datetime
            show.language = language
            show.price = price

            db.session.commit()
            flash('Show updated successfully!', 'success')
            return redirect(url_for('manage_shows', theatre_id=show.tid))

        # Get all movies for the select dropdown
        movies = Movie.query.filter_by(admin_id=current_user.admin_id).all()
        return render_template('edit_show.html', show=show, movies=movies)

    except Exception as e:
        flash(f'Error editing show: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_show/<int:show_id>')
@login_required
def delete_show(show_id):
    if session.get('user_type') != 'admin':
        flash('Please login as admin', 'danger')
        return redirect(url_for('login'))
    
    try:
        show = Shows.query.get_or_404(show_id)
        
        # Verify show belongs to current admin's theatre
        theatre = Theatre.query.get(show.tid)
        if theatre.admin_id != current_user.admin_id:
            flash('You are not authorized to delete this show', 'danger')
            return redirect(url_for('admin_dashboard'))
        
        # Check if show has any bookings
        bookings = Booking.query.filter_by(show_id=show_id).first()
        if bookings:
            flash('Cannot delete show as it has bookings', 'danger')
            return redirect(url_for('manage_shows', theatre_id=show.tid))
        
        db.session.delete(show)
        db.session.commit()
        flash('Show deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting show: {str(e)}', 'danger')
    
    return redirect(url_for('manage_shows', theatre_id=show.tid))

if __name__ == '__main__':
    app.run(debug=True, port=5002) 