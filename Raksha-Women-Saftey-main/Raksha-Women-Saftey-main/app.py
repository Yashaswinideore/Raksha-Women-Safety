from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import json
from dotenv import load_dotenv
import requests
from twilio.rest import Client
from data import send_emergency_alerts

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///women_safety.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize Twilio client
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(twilio_account_sid, twilio_auth_token)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    profile_pic = db.Column(db.String(200))
    contacts = db.relationship('Contact', backref='user', lazy=True)
    safety_zones = db.relationship('SafetyZone', backref='user', lazy=True)
    emergency_history = db.relationship('EmergencyHistory', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class SafetyZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)  # in meters
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class EmergencyHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_name = db.Column(db.String(200))
    status = db.Column(db.String(50))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    zones = SafetyZone.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', contacts=contacts, zones=zones)

@app.route('/safety-zones', methods=['GET', 'POST'])
@login_required
def manage_safety_zones():
    if request.method == 'POST':
        data = request.get_json()
        zone = SafetyZone(
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            radius=data['radius'],
            description=data.get('description'),
            user_id=current_user.id
        )
        db.session.add(zone)
        db.session.commit()
        return jsonify({'message': 'Safety zone added successfully'})
    
    zones = SafetyZone.query.filter_by(user_id=current_user.id).all()
    return render_template('safety_zones.html', zones=zones)

@app.route('/api/safety-zones', methods=['GET'])
@login_required
def get_safety_zones():
    zones = SafetyZone.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': zone.id,
        'name': zone.name,
        'latitude': zone.latitude,
        'longitude': zone.longitude,
        'radius': zone.radius,
        'description': zone.description
    } for zone in zones])

@app.route('/api/safety-zones', methods=['POST'])
@login_required
def add_safety_zone():
    data = request.get_json()
    
    if not all(k in data for k in ['name', 'latitude', 'longitude', 'radius']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        zone = SafetyZone(
            name=data['name'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            radius=float(data['radius']),
            description=data.get('description', ''),
            user_id=current_user.id
        )
        db.session.add(zone)
        db.session.commit()
        
        return jsonify({
            'message': 'Safety zone added successfully',
            'zone': {
                'id': zone.id,
                'name': zone.name,
                'latitude': zone.latitude,
                'longitude': zone.longitude,
                'radius': zone.radius,
                'description': zone.description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/safety-zones/<int:zone_id>', methods=['PUT'])
@login_required
def update_safety_zone(zone_id):
    zone = SafetyZone.query.get_or_404(zone_id)
    
    if zone.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    try:
        if 'name' in data:
            zone.name = data['name']
        if 'latitude' in data:
            zone.latitude = float(data['latitude'])
        if 'longitude' in data:
            zone.longitude = float(data['longitude'])
        if 'radius' in data:
            zone.radius = float(data['radius'])
        if 'description' in data:
            zone.description = data['description']
            
        db.session.commit()
        
        return jsonify({
            'message': 'Safety zone updated successfully',
            'zone': {
                'id': zone.id,
                'name': zone.name,
                'latitude': zone.latitude,
                'longitude': zone.longitude,
                'radius': zone.radius,
                'description': zone.description
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/safety-zones/<int:zone_id>', methods=['DELETE'])
@login_required
def delete_safety_zone(zone_id):
    zone = SafetyZone.query.get_or_404(zone_id)
    
    if zone.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(zone)
        db.session.commit()
        return jsonify({'message': 'Safety zone deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/share-location', methods=['POST'])
@login_required
def share_location():
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return jsonify({'error': 'Location data not provided'}), 400

        # Get location name using geopy
        geolocator = Nominatim(user_agent="women_safety_app")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        location_name = location.address if location else "Unknown Location"

        # Create location record
        new_location = Location(
            latitude=latitude,
            longitude=longitude,
            address=location_name,
            user_id=current_user.id
        )
        db.session.add(new_location)
        db.session.commit()

        # Share with emergency contacts
        contacts = Contact.query.filter_by(user_id=current_user.id).all()
        for contact in contacts:
            try:
                message = twilio_client.messages.create(
                    body=f"Location Update from {current_user.username}:\n"
                         f"Current Location: {location_name}\n"
                         f"Coordinates: {latitude}, {longitude}",
                    from_=os.getenv('TWILIO_PHONE_NUMBER'),
                    to=contact.phone
                )
                print(f"Location shared with {contact.phone}: {message.sid}")
            except Exception as e:
                print(f"Error sharing location with {contact.phone}: {str(e)}")
                continue

        return jsonify({
            'message': 'Location shared successfully',
            'location': location_name
        })

    except Exception as e:
        print(f"Error sharing location: {str(e)}")
        return jsonify({'error': 'Failed to share location'}), 500

@app.route('/sos', methods=['POST'])
@login_required
def sos():
    try:
        # Get user's location
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            print("Error: Location data not provided")
            return jsonify({'error': 'Location data not provided'}), 400

        # Get location name using geopy
        try:
            geolocator = Nominatim(user_agent="women_safety_app")
            location = geolocator.reverse(f"{latitude}, {longitude}")
            location_name = location.address if location else "Unknown Location"
        except Exception as e:
            print(f"Error getting location name: {str(e)}")
            location_name = "Unknown Location"

        # Create Google Maps links for navigation
        maps_link = f"https://www.google.com/maps/dir/?api=1&destination={latitude},{longitude}"
        maps_view_link = f"https://www.google.com/maps?q={latitude},{longitude}"

        # Check if user is in any safety zone
        safety_zones = SafetyZone.query.filter_by(user_id=current_user.id).all()
        in_safety_zone = False
        for zone in safety_zones:
            try:
                distance = geodesic(
                    (latitude, longitude),
                    (zone.latitude, zone.longitude)
                ).meters
                if distance <= zone.radius:
                    in_safety_zone = True
                    break
            except Exception as e:
                print(f"Error calculating distance to safety zone: {str(e)}")
                continue

        # Create emergency history record
        emergency = EmergencyHistory(
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            status='active',
            description='Emergency SOS triggered'
        )
        db.session.add(emergency)
        db.session.commit()

        # Use the send_emergency_alerts function from data.py
        # This will send messages to all emergency contacts using Pushbullet
        message_prefix = "🚨 EMERGENCY ALERT 🚨"
        location_info = (
            f"{location_name}\n"
            f"Coordinates: {latitude}, {longitude}\n"
            f"Safety Zone Status: {'Inside' if in_safety_zone else 'Outside'}\n\n"
            f"📍 View location: {maps_view_link}\n"
            f"🚗 Get directions: {maps_link}"
        )
        
        alert_result = send_emergency_alerts(
            current_user.username,  # Use current user's username
            location=location_info,
            message_prefix=message_prefix,
            user_id=current_user.id  # Pass the user ID instead of password
        )
        
        # Check if Pushbullet alerts were successful
        pushbullet_success = alert_result.get('success', False)
        
        # Try Twilio as backup if Pushbullet failed or if Twilio is configured
        twilio_success = False
        if twilio_account_sid and twilio_auth_token and os.getenv('TWILIO_PHONE_NUMBER'):
            contacts = Contact.query.filter_by(user_id=current_user.id).all()
            
            for contact in contacts:
                try:
                    # Format phone number to E.164 format if needed
                    phone_number = contact.phone
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number

                    message = twilio_client.messages.create(
                        body=(
                            f"🚨 EMERGENCY ALERT 🚨\n\n"
                            f"{current_user.username} has triggered an SOS signal!\n\n"
                            f"Location: {location_name}\n"
                            f"Coordinates: {latitude}, {longitude}\n"
                            f"Safety Zone Status: {'Inside' if in_safety_zone else 'Outside'}\n\n"
                            f"📍 View location: {maps_view_link}\n"
                            f"🚗 Get directions: {maps_link}\n\n"
                            f"Please respond immediately!\n"
                            f"Call emergency services if needed."
                        ),
                        from_=os.getenv('TWILIO_PHONE_NUMBER'),
                        to=phone_number
                    )
                    print(f"Twilio SMS sent successfully to {phone_number}: {message.sid}")
                    twilio_success = True
                except Exception as e:
                    print(f"Error sending Twilio SMS to {contact.phone}: {str(e)}")
                    continue

        # Determine overall success
        alerts_sent = pushbullet_success or twilio_success
        
        if not alerts_sent:
            print("Warning: No emergency messages were sent successfully")
            return jsonify({
                'message': 'Emergency recorded but alert sending failed',
                'emergency_id': emergency.id,
                'location': location_name,
                'in_safety_zone': in_safety_zone
            }), 500

        return jsonify({
            'message': 'SOS alert sent successfully',
            'emergency_id': emergency.id,
            'location': location_name,
            'in_safety_zone': in_safety_zone,
            'maps_link': maps_link,
            'pushbullet_status': alert_result.get('message', 'Failed'),
            'twilio_status': 'Sent' if twilio_success else 'Failed or not configured'
        })

    except Exception as e:
        print(f"Error in SOS route: {str(e)}")
        return jsonify({'error': 'Failed to send SOS alert'}), 500

@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def manage_contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        relationship = request.form.get('relationship')
        
        contact = Contact(
            name=name,
            phone=phone,
            relationship=relationship,
            user_id=current_user.id
        )
        db.session.add(contact)
        db.session.commit()
        
        flash('Contact added successfully!')
        return redirect(url_for('manage_contacts'))
    
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=contacts)

@app.route('/emergency-history')
@login_required
def emergency_history():
    history = EmergencyHistory.query.filter_by(user_id=current_user.id).order_by(EmergencyHistory.timestamp.desc()).all()
    return render_template('emergency_history.html', history=history)

@app.route('/emergency-services')
@login_required
def emergency_services():
    # Define emergency services with their details
    emergency_services = [
        {
            'name': 'Police',
            'number': '100',
            'description': 'For crime, violence, or immediate threats',
            'icon': 'fas fa-shield-alt',
            'color': '#007bff'
        },
        {
            'name': 'Women Helpline',
            'number': '1091',
            'description': 'National helpline for women in distress',
            'icon': 'fas fa-venus',
            'color': '#e83e8c'
        },
        {
            'name': 'Ambulance',
            'number': '108',
            'description': 'Medical emergencies and ambulance services',
            'icon': 'fas fa-ambulance',
            'color': '#dc3545'
        },
        {
            'name': 'Fire Emergency',
            'number': '101',
            'description': 'For fire incidents and rescue operations',
            'icon': 'fas fa-fire',
            'color': '#fd7e14'
        },
        {
            'name': 'Disaster Management',
            'number': '1070',
            'description': 'For natural disasters and emergency situations',
            'icon': 'fas fa-radiation',
            'color': '#6f42c1'
        },
        {
            'name': 'Tourist Helpline',
            'number': '1363',
            'description': 'For tourists facing emergency situations',
            'icon': 'fas fa-map-marked-alt',
            'color': '#20c997'
        }
    ]
    
    return render_template('emergency_services.html', services=emergency_services)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/emergency-status/<int:emergency_id>', methods=['POST'])
@login_required
def update_emergency_status(emergency_id):
    try:
        emergency = EmergencyHistory.query.get_or_404(emergency_id)
        
        # Ensure the emergency belongs to the current user
        if emergency.user_id != current_user.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('emergency_history'))
        
        status = request.form.get('status')
        if status in ['active', 'resolved']:
            emergency.status = status
            db.session.commit()
            flash(f'Emergency status updated to {status}', 'success')
        else:
            flash('Invalid status value', 'danger')
            
        return redirect(url_for('emergency_history'))
    except Exception as e:
        flash(f'Error updating emergency status: {str(e)}', 'danger')
        return redirect(url_for('emergency_history'))

@app.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    try:
        contacts = Contact.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': contact.id,
            'name': contact.name,
            'phone': contact.phone,
            'relationship': contact.relationship
        } for contact in contacts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
@login_required
def create_contact():
    try:
        data = request.get_json()
        contact = Contact(
            name=data['name'],
            phone=data['phone'],
            relationship=data.get('relationship', ''),
            user_id=current_user.id
        )
        db.session.add(contact)
        db.session.commit()
        return jsonify({
            'message': 'Contact created successfully',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'relationship': contact.relationship
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def update_contact(contact_id):
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        data = request.get_json()
        contact.name = data.get('name', contact.name)
        contact.phone = data.get('phone', contact.phone)
        contact.relationship = data.get('relationship', contact.relationship)
        
        db.session.commit()
        return jsonify({
            'message': 'Contact updated successfully',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'relationship': contact.relationship
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    try:
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404
        
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'message': 'Contact deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=8080, debug=True) 