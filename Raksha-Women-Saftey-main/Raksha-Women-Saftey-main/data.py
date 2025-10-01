from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask import Flask
import os
from dotenv import load_dotenv
import subprocess
import json

# Load environment variables
load_dotenv()

# Initialize a minimal Flask app to use with SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///women_safety.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User and Contact models (simplified versions of those in app.py)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    contacts = db.relationship('Contact', backref='user', lazy=True)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


def get_emergency_contacts(username, password=None, user_id=None):
    """
    Retrieve emergency contacts for a user based on username and password
    
    Parameters:
    username (str): The username of the user
    password (str, optional): The password of the user
    user_id (int, optional): User ID to directly retrieve contacts without password
    
    Returns:
    dict: Dictionary containing success/error status and contacts list or error message
    """
    try:
        # Initialize app context to use SQLAlchemy
        with app.app_context():
            # Find user by username or ID
            user = None
            if user_id:
                # If user_id is provided, use it directly (for web app integration)
                user = User.query.get(user_id)
            else:
                # Otherwise use username and verify password
                user = User.query.filter_by(username=username).first()
                
                # Check if user exists
                if not user:
                    return {
                        "success": False,
                        "message": "User not found"
                    }
                
                # Check if password is correct (if provided)
                if password and not user.check_password(password):
                    return {
                        "success": False,
                        "message": "Invalid password"
                    }
            
            # Retrieve user's emergency contacts
            contacts = Contact.query.filter_by(user_id=user.id).all()
            
            # Format contacts into a dictionary
            contacts_list = []
            for contact in contacts:
                # Format phone number to ensure it has +91 prefix
                phone_number = contact.phone
                if not phone_number.startswith('+'):
                    phone_number = '+91' + phone_number
                elif not phone_number.startswith('+91'):
                    # If it has a different prefix, replace it with +91
                    if phone_number.startswith('+'):
                        phone_number = '+91' + phone_number[1:]
                    else:
                        phone_number = '+91' + phone_number
                
                contacts_list.append({
                    "id": contact.id,
                    "name": contact.name,
                    "phone": phone_number,
                    "relationship": contact.relationship
                })
            
            return {
                "success": True,
                "contacts": contacts_list,
                "total_contacts": len(contacts_list)
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving contacts: {str(e)}"
        }


def send_emergency_alerts(username, password=None, location="", message_prefix="EMERGENCY ALERT!", user_id=None):
    """
    Send emergency messages to all contacts of a user
    
    Parameters:
    username (str): The username of the user
    password (str, optional): The password of the user (not needed if user_id is provided)
    location (str): Optional location information to include in the message
    message_prefix (str): Prefix for the emergency message
    user_id (int, optional): User ID to directly retrieve contacts without password
    
    Returns:
    dict: Dictionary containing success/error status and results
    """
    try:
        # Get user's contacts
        contacts_result = get_emergency_contacts(username, password, user_id)
        
        if not contacts_result["success"]:
            return contacts_result
        
        if contacts_result["total_contacts"] == 0:
            return {
                "success": False,
                "message": "No emergency contacts found"
            }
        
        # Pushbullet API key and device ID
        api_key = os.getenv('PUSHBULLET_API_KEY', 'o.b4mbchHpAfij0odL3ornqGvcxYnXwDIq')  # Default to your key
        device_id = os.getenv('PUSHBULLET_DEVICE_ID', 'ujAQHzKKZCSsjCBEeHexUq')  # Default to your device
        
        # Prepare emergency message
        emergency_message = f"{message_prefix}\n\nUser: {username}"
        if location:
            emergency_message += f"\nLocation: {location}"
        emergency_message += "\nPlease respond immediately!"
        
        # Send messages to all contacts
        results = []
        for contact in contacts_result["contacts"]:
            try:
                # Command to send message using push.py
                cmd = [
                    "python", 
                    "push.py", 
                    "--api-key", api_key,
                    "--device", device_id,
                    "--number", contact["phone"],
                    "--message", f"{emergency_message}\n\nContact: {contact['name']} ({contact['relationship']})"
                ]
                
                # Execute the command
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                # Check if message was sent successfully
                if process.returncode == 0 and "successfully" in process.stdout:
                    results.append({
                        "contact": contact["name"],
                        "phone": contact["phone"],
                        "success": True
                    })
                else:
                    results.append({
                        "contact": contact["name"],
                        "phone": contact["phone"],
                        "success": False,
                        "error": process.stderr or process.stdout
                    })
            except Exception as e:
                results.append({
                    "contact": contact["name"],
                    "phone": contact["phone"],
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate success rate
        successful = sum(1 for r in results if r["success"])
        
        return {
            "success": successful > 0,
            "message": f"Sent emergency alerts to {successful} of {len(results)} contacts",
            "results": results,
            "success_rate": f"{successful}/{len(results)}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error sending emergency alerts: {str(e)}"
        }


# Example usage
if __name__ == "__main__":
    # Example: Get contacts for a user
    username = "zeo"
    password = "Asp@123"
    
    # Get emergency contacts
    result = get_emergency_contacts(username, password)
    
    if result["success"]:
        print(f"Found {result['total_contacts']} emergency contacts:")
        for contact in result["contacts"]:
            print(f"- {contact['name']} ({contact['relationship']}): {contact['phone']}")
        
        # Send emergency alerts to all contacts
        print("\nSending emergency alerts...")
        alert_result = send_emergency_alerts(
            username, 
            password, 
            location="123 Main St, Anytown, IN",
            message_prefix="🚨 EMERGENCY! Need immediate assistance!"
        )
        
        print(f"\nAlert Status: {alert_result['message']}")
        
        # Show detailed results
        for result in alert_result["results"]:
            status = "✅ Sent" if result["success"] else "❌ Failed"
            print(f"{status} to {result['contact']} ({result['phone']})")
            if not result["success"] and "error" in result:
                print(f"  Error: {result['error']}")
    else:
        print(f"Error: {result['message']}")
