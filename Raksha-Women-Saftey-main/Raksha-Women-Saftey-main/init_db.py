from app import app, db, User, Contact, SafetyZone
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            # Create test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                phone='+1234567890'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            
            # Add test emergency contact
            contact = Contact(
                name='Emergency Contact',
                phone='+1987654321',
                relationship='Family',
                user_id=test_user.id
            )
            db.session.add(contact)
            
            # Add test safety zone
            safety_zone = SafetyZone(
                name='Home',
                latitude=0.0,  # Replace with actual coordinates
                longitude=0.0,  # Replace with actual coordinates
                radius=1000,  # 1km radius
                description='My home location',
                user_id=test_user.id
            )
            db.session.add(safety_zone)
            
            db.session.commit()
            print("Test user and data created successfully!")
        else:
            print("Test user already exists!")

if __name__ == '__main__':
    init_database() 