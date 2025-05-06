import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import User, Ride, Booking, Review
from blockchain_service import blockchain_service
from ipfs_service import ipfs_storage

logger = logging.getLogger(__name__)

# Home page
@app.route('/')
def home():
    # Get latest rides
    latest_rides = Ride.query.filter_by(is_active=True).order_by(Ride.created_at.desc()).limit(5).all()
    return render_template('home.html', latest_rides=latest_rides)

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        otp_code = request.form.get('otp_code')
        
        # Check if we're in the OTP verification step
        if 'user_id' in session and session.get('awaiting_otp'):
            user = User.query.get(session['user_id'])
            
            if not user:
                flash('User not found', 'danger')
                session.pop('user_id', None)
                session.pop('awaiting_otp', None)
                return render_template('login.html')
                
            # Verify OTP
            if not otp_code:
                flash('Please enter your OTP code', 'danger')
                return render_template('login.html', awaiting_otp=True, username=user.username)
                
            if user.verify_otp(otp_code):
                # OTP verified, log the user in
                login_user(user)
                flash('Login successful!', 'success')
                
                # Clear the session variables
                session.pop('user_id', None)
                session.pop('awaiting_otp', None)
                
                # Redirect to requested page or home
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
            else:
                flash('Invalid OTP code. Please try again.', 'danger')
                return render_template('login.html', awaiting_otp=True, username=user.username)
        
        # Initial login step (password verification)
        # Validate form data
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        # Check password
        if user and user.check_password(password):
            # Check if user has OTP enabled
            if user.otp_enabled:
                # Store user ID in session and await OTP
                session['user_id'] = user.id
                session['awaiting_otp'] = True
                return render_template('login.html', awaiting_otp=True, username=user.username)
            else:
                # No OTP required, log the user in directly
                login_user(user)
                flash('Login successful!', 'success')
                
                # Redirect to requested page or home
                next_page = request.args.get('next')
                return redirect(next_page or url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        ethereum_address = request.form.get('ethereum_address')
        
        # Validate form data
        if not username or not email or not password:
            flash('Please fill all required fields', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already in use', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, email=email, ethereum_address=ethereum_address)
        new_user.set_password(password)
        
        # Save user data to IPFS (basic profile)
        user_profile = {
            'username': username,
            'email': email,
            'ethereum_address': ethereum_address,
            'created_at': datetime.utcnow().isoformat()
        }
        
        ipfs_hash = ipfs_storage.add_json(user_profile)
        if ipfs_hash:
            new_user.ipfs_profile_hash = ipfs_hash
            logger.info(f"User profile saved to IPFS with hash: {ipfs_hash}")
        else:
            logger.warning("Failed to save user profile to IPFS")
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

# Ride management routes
@app.route('/offer-ride', methods=['GET', 'POST'])
@login_required
def offer_ride():
    if request.method == 'POST':
        # Get form data
        start_location = request.form.get('start_location')
        end_location = request.form.get('end_location')
        departure_time_str = request.form.get('departure_time')
        price = request.form.get('price')
        available_seats = request.form.get('available_seats')
        
        # Validate form data
        if not all([start_location, end_location, departure_time_str, price, available_seats]):
            flash('Please fill all required fields', 'danger')
            return render_template('offer_ride.html')
        
        try:
            # Parse departure time
            departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
            
            # Parse price and seats
            price = float(price)
            available_seats = int(available_seats)
            
            if price <= 0 or available_seats <= 0:
                raise ValueError("Price and seats must be positive numbers")
                
        except ValueError as e:
            flash(f'Invalid data format: {str(e)}', 'danger')
            return render_template('offer_ride.html')
        
        # Create ride in database
        new_ride = Ride(
            driver_id=current_user.id,
            start_location=start_location,
            end_location=end_location,
            departure_time=departure_time,
            price=price,
            available_seats=available_seats,
            is_active=True
        )
        
        db.session.add(new_ride)
        db.session.commit()
        
        # Check if ethereum address is set
        if not current_user.ethereum_address:
            flash('You need to set up your Ethereum address in your profile to create blockchain rides', 'warning')
            return redirect(url_for('ride_details', ride_id=new_ride.id))
        
        # Create ride on blockchain
        if blockchain_service.w3 and blockchain_service.contract:
            result = blockchain_service.create_ride(
                driver_address=current_user.ethereum_address,
                start_location=start_location,
                end_location=end_location,
                price=price,
                available_seats=available_seats
            )
            
            if result:
                # Update ride with blockchain data
                new_ride.smart_contract_id = result['ride_id']
                db.session.commit()
                
                flash('Ride created successfully on blockchain!', 'success')
            else:
                flash('Ride created in database but blockchain transaction failed', 'warning')
        else:
            flash('Ride created in database but blockchain service is not available', 'warning')
        
        return redirect(url_for('ride_details', ride_id=new_ride.id))
    
    return render_template('offer_ride.html')

@app.route('/search-ride', methods=['GET', 'POST'])
def search_ride():
    rides = []
    
    if request.method == 'POST':
        # Get search parameters
        start_location = request.form.get('start_location', '')
        end_location = request.form.get('end_location', '')
        date_str = request.form.get('date', '')
        
        # Build query
        query = Ride.query.filter_by(is_active=True)
        
        if start_location:
            query = query.filter(Ride.start_location.ilike(f'%{start_location}%'))
        
        if end_location:
            query = query.filter(Ride.end_location.ilike(f'%{end_location}%'))
        
        if date_str:
            try:
                search_date = datetime.strptime(date_str, '%Y-%m-%d')
                # Filter rides on the selected date
                query = query.filter(
                    Ride.departure_time >= search_date,
                    Ride.departure_time < search_date.replace(hour=23, minute=59, second=59)
                )
            except ValueError:
                flash('Invalid date format', 'danger')
        
        # Execute query
        rides = query.order_by(Ride.departure_time).all()
        
    return render_template('search_ride.html', rides=rides)

@app.route('/ride/<int:ride_id>')
def ride_details(ride_id):
    # Get ride from database
    ride = Ride.query.get_or_404(ride_id)
    
    # Check if user has already booked this ride
    user_booking = None
    if current_user.is_authenticated:
        user_booking = Booking.query.filter_by(
            ride_id=ride.id,
            passenger_id=current_user.id
        ).first()
    
    # Get blockchain data if available
    blockchain_data = None
    if ride.smart_contract_id and blockchain_service.w3 and blockchain_service.contract:
        blockchain_data = blockchain_service.get_ride(ride.smart_contract_id)
    
    return render_template('ride_details.html', ride=ride, user_booking=user_booking, blockchain_data=blockchain_data)

@app.route('/book-ride/<int:ride_id>', methods=['POST'])
@login_required
def book_ride(ride_id):
    # Get ride from database
    ride = Ride.query.get_or_404(ride_id)
    
    # Check if ride is available
    if not ride.is_active or ride.available_seats <= 0:
        flash('This ride is no longer available', 'danger')
        return redirect(url_for('ride_details', ride_id=ride_id))
    
    # Check if user has already booked this ride
    existing_booking = Booking.query.filter_by(
        ride_id=ride.id,
        passenger_id=current_user.id
    ).first()
    
    if existing_booking:
        flash('You have already booked this ride', 'warning')
        return redirect(url_for('ride_details', ride_id=ride_id))
    
    # Check if ethereum address is set
    if not current_user.ethereum_address and ride.smart_contract_id:
        flash('You need to set up your Ethereum address in your profile to book blockchain rides', 'warning')
        return redirect(url_for('ride_details', ride_id=ride_id))
    
    # Create booking in database
    seats_requested = int(request.form.get('seats', 1))
    
    if seats_requested <= 0 or seats_requested > ride.available_seats:
        flash(f'Invalid seat request. Available seats: {ride.available_seats}', 'danger')
        return redirect(url_for('ride_details', ride_id=ride_id))
    
    new_booking = Booking(
        ride_id=ride.id,
        passenger_id=current_user.id,
        status='pending',
        seats_booked=seats_requested
    )
    
    # Update available seats
    ride.available_seats -= seats_requested
    
    db.session.add(new_booking)
    db.session.commit()
    
    # Book ride on blockchain
    if ride.smart_contract_id and blockchain_service.w3 and blockchain_service.contract:
        result = blockchain_service.book_ride(
            passenger_address=current_user.ethereum_address,
            ride_id=ride.smart_contract_id,
            price=ride.price * seats_requested
        )
        
        if result:
            # Update booking with transaction hash
            new_booking.transaction_hash = result['tx_hash']
            new_booking.status = 'confirmed'
            db.session.commit()
            
            flash('Ride booked successfully on blockchain!', 'success')
        else:
            flash('Booking created in database but blockchain transaction failed', 'warning')
    else:
        flash('Booking created in database but blockchain service is not available', 'warning')
    
    return redirect(url_for('ride_details', ride_id=ride_id))

@app.route('/complete-ride/<int:ride_id>', methods=['POST'])
@login_required
def complete_ride(ride_id):
    # Get ride from database
    ride = Ride.query.get_or_404(ride_id)
    
    # Check if user is the driver
    if ride.driver_id != current_user.id:
        flash('Only the driver can complete this ride', 'danger')
        return redirect(url_for('ride_details', ride_id=ride_id))
    
    # Complete ride on blockchain
    if ride.smart_contract_id and blockchain_service.w3 and blockchain_service.contract:
        result = blockchain_service.complete_ride(
            driver_address=current_user.ethereum_address,
            ride_id=ride.smart_contract_id
        )
        
        if result:
            # Update ride and bookings
            ride.is_active = False
            bookings = Booking.query.filter_by(ride_id=ride.id).all()
            for booking in bookings:
                booking.status = 'completed'
            
            db.session.commit()
            
            flash('Ride completed successfully!', 'success')
        else:
            flash('Blockchain transaction failed', 'warning')
    else:
        # Complete ride in database only
        ride.is_active = False
        bookings = Booking.query.filter_by(ride_id=ride.id).all()
        for booking in bookings:
            booking.status = 'completed'
        
        db.session.commit()
        
        flash('Ride marked as completed in database', 'success')
    
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    # Get user's rides and bookings
    offered_rides = Ride.query.filter_by(driver_id=current_user.id).order_by(Ride.departure_time.desc()).all()
    bookings = Booking.query.filter_by(passenger_id=current_user.id).order_by(Booking.created_at.desc()).all()
    
    # Get IPFS profile data if available
    ipfs_profile = None
    if current_user.ipfs_profile_hash:
        ipfs_profile = ipfs_storage.get_json(current_user.ipfs_profile_hash)
    
    # Generate OTP URI for QR code if not already verified
    otp_uri = None
    if not current_user.otp_verified:
        otp_uri = current_user.get_otp_uri()
    
    return render_template('profile.html', 
                          offered_rides=offered_rides, 
                          bookings=bookings, 
                          ipfs_profile=ipfs_profile, 
                          otp_uri=otp_uri)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    # Get form data
    ethereum_address = request.form.get('ethereum_address')
    
    if ethereum_address:
        # Update user
        current_user.ethereum_address = ethereum_address
        
        # Update IPFS profile
        user_profile = {
            'username': current_user.username,
            'email': current_user.email,
            'ethereum_address': ethereum_address,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        ipfs_hash = ipfs_storage.add_json(user_profile)
        if ipfs_hash:
            current_user.ipfs_profile_hash = ipfs_hash
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    else:
        flash('Ethereum address is required', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/setup-otp', methods=['POST'])
@login_required
def setup_otp():
    # Generate new OTP secret and verify it's working
    otp_code = request.form.get('otp_code')
    
    if not otp_code:
        flash('Please enter the OTP code from your authenticator app', 'danger')
        return redirect(url_for('profile'))
    
    # Verify the OTP code
    if current_user.verify_otp(otp_code):
        current_user.otp_verified = True
        current_user.enable_otp()
        flash('Two-factor authentication has been set up successfully!', 'success')
    else:
        flash('Invalid OTP code. Please try again.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/disable-otp', methods=['POST'])
@login_required
def disable_otp():
    # Disable OTP for the user
    otp_code = request.form.get('otp_code')
    
    if not otp_code:
        flash('Please enter the OTP code to disable two-factor authentication', 'danger')
        return redirect(url_for('profile'))
    
    # Verify the OTP code
    if current_user.verify_otp(otp_code):
        current_user.otp_verified = False
        current_user.disable_otp()
        flash('Two-factor authentication has been disabled', 'info')
    else:
        flash('Invalid OTP code. Please try again.', 'danger')
    
    return redirect(url_for('profile'))

# API endpoints
@app.route('/api/rides', methods=['GET'])
def api_rides():
    # Get all active rides
    rides = Ride.query.filter_by(is_active=True).all()
    
    # Convert to JSON
    rides_json = [{
        'id': ride.id,
        'start_location': ride.start_location,
        'end_location': ride.end_location,
        'departure_time': ride.departure_time.isoformat(),
        'price': ride.price,
        'available_seats': ride.available_seats,
        'driver_id': ride.driver_id,
        'smart_contract_id': ride.smart_contract_id
    } for ride in rides]
    
    return jsonify(rides_json)

@app.route('/api/ride/<int:ride_id>', methods=['GET'])
def api_ride(ride_id):
    # Get ride from database
    ride = Ride.query.get_or_404(ride_id)
    
    # Convert to JSON
    ride_json = {
        'id': ride.id,
        'start_location': ride.start_location,
        'end_location': ride.end_location,
        'departure_time': ride.departure_time.isoformat(),
        'price': ride.price,
        'available_seats': ride.available_seats,
        'driver_id': ride.driver_id,
        'smart_contract_id': ride.smart_contract_id,
        'is_active': ride.is_active
    }
    
    # Get blockchain data if available
    if ride.smart_contract_id and blockchain_service.w3 and blockchain_service.contract:
        blockchain_data = blockchain_service.get_ride(ride.smart_contract_id)
        if blockchain_data:
            ride_json['blockchain_data'] = blockchain_data
    
    return jsonify(ride_json)

@app.route('/api/blockchain/rides', methods=['GET'])
def api_blockchain_rides():
    # Get active rides from blockchain
    if blockchain_service.w3 and blockchain_service.contract:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        
        rides = blockchain_service.get_active_rides(offset, limit)
        if rides:
            return jsonify({'rides': rides})
        else:
            return jsonify({'rides': [], 'error': 'Failed to get rides from blockchain'})
    else:
        return jsonify({'rides': [], 'error': 'Blockchain service not available'})

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500
