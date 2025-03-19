import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)

# Configure secret key from environment variable
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure SQLAlchemy (use SQLite for simplicity)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///carpool.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import routes after app is created to avoid circular imports
with app.app_context():
    from app import models, routes
    
    # Create all database tables
    db.create_all()
    
    # Setup user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))
