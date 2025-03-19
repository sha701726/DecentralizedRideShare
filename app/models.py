from app.app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for storing user-related data"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    ethereum_address = db.Column(db.String(42), unique=True, nullable=True)
    ipfs_profile_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reputation = db.Column(db.Float, default=5.0)
    
    # Relationships
    rides_offered = db.relationship('Ride', backref='driver', lazy='dynamic')
    bookings = db.relationship('Booking', backref='passenger', lazy='dynamic')
    
    def set_password(self, password):
        """Create hashed password"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Ride(db.Model):
    """Ride model for storing ride-related data"""
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_location = db.Column(db.String(128), nullable=False)
    end_location = db.Column(db.String(128), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price in ETH
    available_seats = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    smart_contract_id = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='ride', lazy='dynamic')
    
    def __repr__(self):
        return f'<Ride {self.id}: {self.start_location} to {self.end_location}>'

class Booking(db.Model):
    """Booking model for storing booking-related data"""
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_hash = db.Column(db.String(66), nullable=True)
    seats_booked = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<Booking {self.id}: Ride {self.ride_id}, Passenger {self.passenger_id}>'

class Review(db.Model):
    """Review model for storing user reviews"""
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    reviewee = db.relationship('User', foreign_keys=[reviewee_id])
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating}>'
