#!/usr/bin/env python3

import requests
import json
import argparse

def send_sms_via_pushbullet(api_key, device_iden, number, message):
    """
    Send SMS message using Pushbullet's API
    
    Parameters:
    api_key (str): Your Pushbullet API key
    device_iden (str): The identifier of the device you want to send from
    number (str): The phone number you want to send the SMS to
    message (str): The message content
    """
    
    # Pushbullet API endpoint for sending SMS
    url = "https://api.pushbullet.com/v2/texts"
    
    # Headers including authorization
    headers = {
        "Access-Token": api_key,
        "Content-Type": "application/json"
    }
    
    # Payload data
    data = {
        "data": {
            "target_device_iden": device_iden,
            "addresses": [number],
            "message": message
        }
    }
    
    # Make the API request
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # Check if request was successful
    if response.status_code == 200:
        print(f"SMS sent successfully to {number}")
        return True
    else:
        print(f"Failed to send SMS. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def list_devices(api_key):
    """List all available devices in your Pushbullet account"""
    
    url = "https://api.pushbullet.com/v2/devices"
    headers = {"Access-Token": api_key}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        devices = response.json().get("devices", [])
        print("Available devices:")
        for device in devices:
            if device.get("active"):
                print(f"  Device: {device.get('nickname', 'Unknown')}")
                print(f"  Iden: {device.get('iden')}")
                print(f"  Has SMS: {device.get('has_sms', False)}")
                print("  ---")
        return devices
    else:
        print(f"Failed to retrieve devices. Status code: {response.status_code}")
        return []

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Send SMS messages via Pushbullet")
    parser.add_argument("--api-key", required=True, help="Your Pushbullet API key")
    parser.add_argument("--list-devices", action="store_true", help="List available devices")
    parser.add_argument("--device", help="Device identifier to send from")
    parser.add_argument("--number", help="Phone number to send SMS to")
    parser.add_argument("--message", help="Message content to send")
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_devices(args.api_key)
    elif args.device and args.number and args.message:
        send_sms_via_pushbullet(args.api_key, args.device, args.number, args.message)
    else:
        if not args.list_devices:
            print("Error: You must either use --list-devices or provide --device, --number, and --message")
            parser.print_help()