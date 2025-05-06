import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask application
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///carpool.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models and create tables
with app.app_context():
    from models import User, Ride, Booking, Review
    
    # Only create tables if they don't exist yet
    try:
        User.__table__.create(db.engine, checkfirst=True)
        Ride.__table__.create(db.engine, checkfirst=True)
        Booking.__table__.create(db.engine, checkfirst=True)
        Review.__table__.create(db.engine, checkfirst=True)
        logger.info("Database tables created or already exist")
    except Exception as e:
        # In case the direct table creation fails, fallback to create_all
        db.create_all()
        logger.info("Database tables created using create_all()")

# Import and register routes
from routes import *

# Configure login manager user loader
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
