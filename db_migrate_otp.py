from app import app, db
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def migrate_database():
    """
    Add OTP fields to the User model in the database
    """
    logger.info("Running OTP migration script...")
    
    try:
        with app.app_context():
            # Add OTP columns to User table
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE "user" 
                    ADD COLUMN IF NOT EXISTS otp_secret VARCHAR(32),
                    ADD COLUMN IF NOT EXISTS otp_enabled BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS otp_verified BOOLEAN DEFAULT FALSE;
                """))
                conn.commit()
            logger.info("OTP columns added successfully")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = migrate_database()
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed")