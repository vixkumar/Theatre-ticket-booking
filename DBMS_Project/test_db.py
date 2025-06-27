from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Nopainnogain#123@localhost/theatre_booking?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Test the connection
try:
    with app.app_context():
        # Try to execute a simple query
        result = db.session.execute(text('SELECT 1')).scalar()
        print("Database connection successful!")
        
        # Try to query the Admins table
        admins = db.session.execute(text('SELECT * FROM Admins')).fetchall()
        print("\nAdmins table contents:")
        for admin in admins:
            print(f"Admin ID: {admin[0]}, Password: {admin[1]}")
            
except Exception as e:
    print(f"Error connecting to database: {str(e)}") 