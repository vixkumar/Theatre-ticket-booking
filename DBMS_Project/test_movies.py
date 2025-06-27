from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Nopainnogain#123@localhost/theatre_booking?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Movie model
class Movie(db.Model):
    __tablename__ = 'Movie'
    m_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    director = db.Column(db.String(50), nullable=False)
    actors = db.Column(db.String(200), nullable=False)

# Test the connection and query movies
try:
    with app.app_context():
        # Try to execute a direct SQL query to see all movies
        print("\nExecuting direct SQL query:")
        result = db.session.execute(text('SELECT * FROM Movie')).fetchall()
        print(f"Number of movies found: {len(result)}")
        for movie in result:
            print(f"Movie: {movie}")
            
        # Try using the SQLAlchemy model
        print("\nExecuting SQLAlchemy query:")
        movies = Movie.query.all()
        print(f"Number of movies found: {len(movies)}")
        for movie in movies:
            print(f"Movie: ID={movie.m_id}, Title={movie.title}, Release Date={movie.release_date}, Director={movie.director}, Actors={movie.actors}")
            
except Exception as e:
    print(f"Error: {str(e)}") 