// SOS functionality
let watchId = null;
let hasLocationPermission = false;

// Check for location permission on page load
document.addEventListener('DOMContentLoaded', () => {
    checkLocationPermission();
    
    // Create SOS Modal if it doesn't exist
    if (!document.getElementById('sosModal')) {
        createSOSModal();
    }
    
    // Audio element for SOS alert
    if (!window.sirenSound) {
        window.sirenSound = new SirenSound();
    }
});

// SirenSound class
class SirenSound {
    constructor() {
        // Create a simple siren oscillator instead of using an audio file
        this.audioContext = null;
        this.oscillator = null;
        this.gainNode = null;
        this.isPlaying = false;
    }
    
    play() {
        if (this.isPlaying) return;
        
        try {
            // Initialize Web Audio API
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create oscillator
            this.oscillator = this.audioContext.createOscillator();
            this.oscillator.type = 'sine';
            
            // Create gain node for volume control
            this.gainNode = this.audioContext.createGain();
            this.gainNode.gain.value = 0.5;
            
            // Connect nodes
            this.oscillator.connect(this.gainNode);
            this.gainNode.connect(this.audioContext.destination);
            
            // Start oscillator with siren effect
            this.oscillator.start();
            
            // Create siren effect by modulating frequency
            let direction = 1;
            let frequency = 400;
            
            const createSirenEffect = () => {
                if (!this.isPlaying) return;
                
                // Change frequency in a pattern
                frequency += direction * 5;
                if (frequency > 800) {
                    direction = -1;
                } else if (frequency < 400) {
                    direction = 1;
                }
                
                if (this.oscillator) {
                    this.oscillator.frequency.value = frequency;
                }
                
                // Continue the siren effect
                setTimeout(createSirenEffect, 20);
            };
            
            this.isPlaying = true;
            createSirenEffect();
            
        } catch (err) {
            console.error("Error playing siren sound:", err);
        }
    }
    
    stop() {
        if (!this.isPlaying) return;
        
        try {
            if (this.oscillator) {
                this.oscillator.stop();
                this.oscillator.disconnect();
                this.oscillator = null;
            }
            
            if (this.gainNode) {
                this.gainNode.disconnect();
                this.gainNode = null;
            }
            
            if (this.audioContext) {
                this.audioContext.close().catch(err => console.error(err));
                this.audioContext = null;
            }
            
            this.isPlaying = false;
        } catch (err) {
            console.error("Error stopping siren sound:", err);
        }
    }
}

// Create SOS confirmation modal
function createSOSModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'sosModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'sosModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title" id="sosModalLabel">Confirm SOS Alert</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to send an emergency SOS alert to all your contacts?</p>
                    <p><strong>This will share your current location with your emergency contacts.</strong></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="confirmSOS()">Send SOS Alert</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Check location permission
function checkLocationPermission() {
    if ("geolocation" in navigator) {
        navigator.permissions.query({ name: 'geolocation' }).then(permissionStatus => {
            if (permissionStatus.state === 'granted') {
                hasLocationPermission = true;
                startLocationTracking();
            } else if (permissionStatus.state === 'prompt') {
                // Will prompt the user when we try to get location
                document.getElementById('locationStatus').innerHTML = 'Click the SOS button to enable location services';
            } else if (permissionStatus.state === 'denied') {
                hasLocationPermission = false;
                document.getElementById('locationStatus').innerHTML = 
                    '<span class="text-danger">Location services are disabled. Please enable them in your browser settings.</span>';
            }
            
            // Listen for changes in permission
            permissionStatus.onchange = function() {
                checkLocationPermission();
            };
        });
    } else {
        document.getElementById('locationStatus').innerHTML = 
            '<span class="text-danger">Geolocation is not supported by your browser</span>';
    }
}

function startLocationTracking() {
    if ("geolocation" in navigator) {
        watchId = navigator.geolocation.watchPosition(
            updateLocationStatus,
            handleLocationError,
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        document.getElementById('locationStatus').innerHTML = 
            '<span class="text-danger">Geolocation is not supported by your browser</span>';
    }
}

function updateLocationStatus(position) {
    hasLocationPermission = true;
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    
    // Update global variable for access in other functions
    window.currentLocation = {
        lat: latitude,
        lng: longitude
    };
    
    document.getElementById('locationStatus').innerHTML = 
        `<span class="text-success">Location available</span>`;
}

function handleLocationError(error) {
    hasLocationPermission = false;
    let errorMessage = 'Error getting location: ';
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '<span class="text-danger">Location permission denied. Please enable location services in your browser settings.</span>';
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '<span class="text-danger">Location information is unavailable. Please check your device settings.</span>';
            break;
        case error.TIMEOUT:
            errorMessage = '<span class="text-danger">The request to get location timed out. Please try again.</span>';
            break;
        case error.UNKNOWN_ERROR:
            errorMessage = '<span class="text-danger">An unknown error occurred while getting location.</span>';
            break;
    }
    document.getElementById('locationStatus').innerHTML = errorMessage;
}

function triggerSOS() {
    // Try to get location permission if we don't have it
    if (!hasLocationPermission) {
        navigator.geolocation.getCurrentPosition(
            position => {
                hasLocationPermission = true;
                window.currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                showSOSModal();
            },
            error => {
                handleLocationError(error);
                alert('Unable to get your location. Please enable location services in your browser settings and try again.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        showSOSModal();
    }
}

function showSOSModal() {
    // Get the modal element
    const modalElement = document.getElementById('sosModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Play siren sound
    if (window.sirenSound) {
        window.sirenSound.play();
    }
    
    // Add event listener to stop sound when modal is closed
    modalElement.addEventListener('hidden.bs.modal', () => {
        if (window.sirenSound) {
            window.sirenSound.stop();
        }
    });
}

function confirmSOS() {
    if (!window.currentLocation) {
        alert('Unable to get your location. Please enable location services.');
        return;
    }
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('sosModal'));
    modal.hide();
    
    const sosButton = document.getElementById('sosButton');
    const originalText = sosButton.innerHTML;
    sosButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    sosButton.disabled = true;
    
    fetch('/sos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            latitude: window.currentLocation.lat,
            longitude: window.currentLocation.lng
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
            sosButton.innerHTML = '<i class="fas fa-exclamation-triangle"></i> SOS';
        } else {
            alert('SOS alert sent successfully! Your emergency contacts have been notified.');
            
            // Show success animation
            sosButton.innerHTML = '<i class="fas fa-check"></i> Sent!';
            setTimeout(() => {
                sosButton.innerHTML = originalText;
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error sending SOS:', error);
        alert('Failed to send SOS alert: ' + error.message);
        sosButton.innerHTML = originalText;
    })
    .finally(() => {
        sosButton.disabled = false;
        if (window.sirenSound) {
            window.sirenSound.stop();
        }
    });
} 