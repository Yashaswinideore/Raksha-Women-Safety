# RAKSHA - Women Safety Application

<div align="center">
<img src="https://cdn-icons-png.flaticon.com/512/6598/6598519.png" alt="Raksha Logo" width="200">
  <br>
  <h3>Empowering Women Through Technology</h3>
  
  ![License](https://img.shields.io/badge/license-MIT-blue)
  ![Python](https://img.shields.io/badge/python-3.7+-brightgreen)
  ![Flask](https://img.shields.io/badge/flask-2.0.1-orange)
  ![Status](https://img.shields.io/badge/status-active-success)
</div>

## 📑 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Security Features](#-security-features)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Overview

RAKSHA is a comprehensive women's safety web application designed to provide immediate assistance during emergencies. The application offers real-time location tracking, emergency contact management, and direct access to essential emergency services - just a click away from contacting authorities when needed.

This platform was developed with the aim of creating a reliable safety companion that works across devices and provides peace of mind for women navigating their daily lives.

## 🔑 Key Features

- **Emergency SOS Alert System**
  - One-click emergency activation from the dashboard
  - Automated alerts sent to all emergency contacts with your exact location
  - Pushbullet integration for instant notifications across all your devices
  - Smart detection of safety zone status during emergencies

- **Safety Zone Management**
  - Define custom safe areas on an interactive map
  - Set personalized radius for each safety zone
  - Add descriptions and names to easily identify different zones
  - Visualization of all your safety zones on the dashboard map

- **Emergency Contact Management**
  - Add unlimited trusted emergency contacts
  - Store contact details including name, phone number, and relationship
  - Edit or remove contacts as needed
  - All contacts receive immediate alerts during emergencies

- **Direct Emergency Services Access**
  - One-touch dialing to emergency services directly from your device
  - Comprehensive directory of emergency numbers
  - Categorized and searchable emergency services
  - No login required to access emergency numbers in critical situations

- **Emergency History Tracking**
  - Complete records of all emergency events
  - Map visualization of emergency locations
  - Timestamp and status tracking
  - Option to mark emergencies as resolved

## 💻 Technology Stack

### Backend
- **Flask**: Lightweight web application framework
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping
- **Flask-Login**: User authentication and session management
- **Pushbullet API**: Cross-device notifications and SMS messaging
- **Geopy**: Geolocation services and distance calculations

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **JavaScript/jQuery**: Dynamic client-side functionality
- **Google Maps API**: Interactive maps and location services
- **HTML5/CSS3**: Modern interface design

### Data Storage
- **SQLite**: Lightweight database for development
- **Geolocation Data**: Real-time location storage and processing

## 🔧 Installation

### Prerequisites
- Python 3.7+
- pip (Python package installer)
- Git

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/raksha-app.git
   cd raksha-app
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your browser and navigate to: `http://127.0.0.1:8080`

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:

```
# Application configuration
SECRET_KEY=your-secure-secret-key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Pushbullet configuration (for notifications)
PUSHBULLET_API_KEY=your-pushbullet-api-key
PUSHBULLET_DEVICE_IDEN=your-pushbullet-device-id
```

### Google Maps API Setup
1. Create a project in Google Cloud Console
2. Enable Maps JavaScript API, Geocoding API, and Places API
3. Create an API key with appropriate restrictions
4. Add the API key to your `.env` file

### Pushbullet Setup
1. Create a Pushbullet account at https://www.pushbullet.com
2. Generate an API key in your account settings
3. Install the Pushbullet app on your mobile device
4. Get your device identifier from the Pushbullet API
5. Add both values to your `.env` file

## 📱 Usage Guide

### User Registration and Setup
1. Create a new account with a valid email and phone number
2. Add emergency contacts through the Contacts page
3. Configure safety zones in the Safety Zones section
4. Enable location permissions in your browser

### Emergency Activation
1. Press the SOS button on the dashboard in case of emergency
2. Your current location will be shared with all emergency contacts
3. Pushbullet notifications will be sent to your emergency contacts
4. Use the Emergency Services page to directly call authorities if needed

### Managing Safety Zones
1. Navigate to the Safety Zones page
2. Click "Add New Zone" and place a pin on the map
3. Set a name, radius, and description for the zone
4. Safety zones will appear on your dashboard map

### Emergency Services
1. Access the Emergency Services page from the navigation menu
2. Browse categorized emergency service numbers
3. Use the search feature to find specific services
4. Tap any service number to directly call from your device

## 🔐 Security Features

- **Data Protection**
  - Password hashing using Werkzeug security
  - Encrypted data transmission
  - Session management with Flask-Login

- **Privacy Measures**
  - Location data only shared during emergencies
  - User consent for all data sharing
  - Automatic session timeouts

- **Best Practices**
  - CSRF protection on all forms
  - Input validation and sanitization
  - Secure cookie handling

## 🤝 Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ for women's safety and empowerment</p>
</div> 
