#!/usr/bin/env python3
"""
Azaan App - Plays azaan audio at prayer times for Princeton, NJ
"""

import requests
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
import os
import sys
import argparse
import subprocess
from flask import Flask, render_template, jsonify

class AzaanApp:
    def __init__(self, mock_time=None):
        self.location_name = "Princeton, NJ"
        self.latitude = 40.3573
        self.longitude = -74.6672
        self.method = 2  # ISNA method
        self.audio_file = "azaan.mp3"
        self.prayer_times = {}
        self.prayer_date = None
        self.mock_time = mock_time
        self.mock_start_time = datetime.now() if mock_time else None
        self.played_prayers = set()  # Track which prayers we've already played

        # Check if audio file exists
        if not os.path.exists(self.audio_file):
            print(f"Error: Audio file {self.audio_file} not found!")
            sys.exit(1)
        
        if self.mock_time:
            print(f"🕐 MOCK MODE: Starting with time {self.mock_time.strftime('%H:%M:%S')}")
        
        # Initialize Flask app
        self.flask_app = Flask(__name__)
        self.setup_routes()
    
    def get_current_time(self):
        """Get current time (real or mocked)"""
        if self.mock_time and self.mock_start_time:
            # Calculate elapsed time since mock start and add to mock time
            elapsed = datetime.now() - self.mock_start_time
            return self.mock_time + elapsed
        return datetime.now()
    
    def fetch_prayer_times(self):
        """Fetch today's prayer times from Aladhan API"""
        try:
            url = f"https://api.aladhan.com/v1/timings"
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'method': self.method
            }

            print("Fetching prayer times...")
            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                timings = data['data']['timings']

                self.prayer_times = {
                    'Fajr': timings['Fajr'],
                    'Dhuhr': timings['Dhuhr'],
                    'Asr': timings['Asr'],
                    'Maghrib': timings['Maghrib'],
                    'Isha': timings['Isha']
                }
                self.prayer_date = data['data']['date']['readable']

                print(f"Prayer times for {self.location_name}:")
                for prayer, time in self.prayer_times.items():
                    print(f"  {prayer}: {time}")

                return True
            else:
                print(f"Error fetching prayer times: {response.status_code}")
                return False

        except Exception as e:
            print(f"Error fetching prayer times: {e}")
            return False
    
    def play_azaan(self, prayer_name):
        """Play the azaan audio file using afplay"""
        try:
            print(f"\n🕌 Time for {prayer_name} prayer! Playing azaan...")
            # Use afplay to play the audio file (blocks until complete)
            result = subprocess.run(['afplay', self.audio_file], check=True)
            print(f"Azaan for {prayer_name} completed.")

        except subprocess.CalledProcessError as e:
            print(f"Error playing azaan: {e}")
        except Exception as e:
            print(f"Error playing azaan: {e}")
    
    def schedule_prayers(self):
        """Schedule azaan to play at each prayer time"""
        if not self.prayer_times:
            print("No prayer times available. Fetching...")
            if not self.fetch_prayer_times():
                print("Failed to fetch prayer times. Exiting.")
                return False
        
        # Clear existing schedule
        schedule.clear()
        
        for prayer, time_str in self.prayer_times.items():
            schedule.every().day.at(time_str).do(self.play_azaan, prayer)
            print(f"Scheduled {prayer} azaan at {time_str}")
        
        # Schedule to fetch new prayer times at midnight
        schedule.every().day.at("00:01").do(self.fetch_and_reschedule)
        
        return True
    
    def fetch_and_reschedule(self):
        """Fetch new prayer times and reschedule"""
        print("\nFetching new prayer times for today...")
        if self.fetch_prayer_times():
            self.schedule_prayers()
            print("Prayer times updated and rescheduled.")
        else:
            print("Failed to update prayer times.")
    
    def get_next_prayer(self):
        """Get the next prayer time and countdown"""
        if not self.prayer_times:
            return None, None, None
        
        now = self.get_current_time()
        current_time = now.time()
        
        # Convert prayer times to datetime objects for today
        prayer_list = []
        for prayer, time_str in self.prayer_times.items():
            prayer_time = datetime.strptime(time_str, "%H:%M").time()
            prayer_datetime = datetime.combine(now.date(), prayer_time)
            prayer_list.append((prayer, prayer_datetime))
        
        # Sort by time
        prayer_list.sort(key=lambda x: x[1])
        
        # Find next prayer
        for prayer, prayer_datetime in prayer_list:
            if prayer_datetime.time() > current_time:
                time_diff = prayer_datetime - now
                return prayer, prayer_datetime.strftime("%H:%M"), time_diff
        
        # If no prayer today, next prayer is tomorrow's Fajr
        tomorrow = now + timedelta(days=1)
        fajr_tomorrow = datetime.combine(tomorrow.date(), 
                                       datetime.strptime(self.prayer_times['Fajr'], "%H:%M").time())
        time_diff = fajr_tomorrow - now
        return "Fajr", self.prayer_times['Fajr'], time_diff
    
    def setup_routes(self):
        """Setup Flask routes"""
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self.flask_app.route('/api/prayer-times')
        def api_prayer_times():
            next_prayer, next_time, time_diff = self.get_next_prayer()
            
            # Calculate countdown in seconds
            countdown_seconds = 0
            if time_diff:
                countdown_seconds = int(time_diff.total_seconds())
            
            return jsonify({
                'prayer_times': self.prayer_times,
                'date': self.prayer_date,
                'location': self.location_name,
                'next_prayer': {
                    'name': next_prayer,
                    'time': next_time,
                    'countdown_seconds': countdown_seconds
                }
            })
    
    def run_web_server(self):
        """Run the Flask web server"""
        print("🌐 Starting web server on http://localhost:8080")
        self.flask_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    
    def check_prayer_times_mock(self):
        """Check if it's time for any prayer (for mock mode)"""
        now = self.get_current_time()
        current_time_str = now.strftime("%H:%M")

        for prayer, time_str in self.prayer_times.items():
            # Check if current time matches prayer time (within same minute)
            if current_time_str == time_str and prayer not in self.played_prayers:
                self.played_prayers.add(prayer)
                self.play_azaan(prayer)

    def run(self):
        """Main application loop"""
        print("🕌 Azaan App Starting...")
        print(f"Location: {self.location_name}")

        # Initial setup
        if not self.schedule_prayers():
            return

        print("\n📅 Next prayer times:")
        now = self.get_current_time().time()
        for prayer, time_str in self.prayer_times.items():
            prayer_time = datetime.strptime(time_str, "%H:%M").time()
            if prayer_time > now:
                print(f"  Next: {prayer} at {time_str}")
                break

        print("🌐 Starting web server on http://localhost:8080")
        print("\n🔄 App is running. Press Ctrl+C to stop.")
        print("Waiting for prayer times...")

        # Start web server in a separate thread
        web_thread = threading.Thread(target=self.run_web_server, daemon=True)
        web_thread.start()

        try:
            # Check more frequently when in mock mode for testing
            check_interval = 1 if self.mock_time else 60
            while True:
                if self.mock_time:
                    # In mock mode, manually check prayer times
                    self.check_prayer_times_mock()
                else:
                    # In normal mode, use schedule library
                    schedule.run_pending()
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Azaan App stopped.")

def main():
    parser = argparse.ArgumentParser(description='Azaan App - Prayer times with audio alerts')
    parser.add_argument('--mock-time', type=str, help='Mock current time for testing (format: HH:MM)')
    parser.add_argument('--test-in', type=int, help='Test mode: trigger azaan in X seconds')
    
    args = parser.parse_args()
    
    mock_time = None
    if args.mock_time:
        try:
            # Parse mock time and set it to today's date
            mock_hour, mock_minute = args.mock_time.split(':')
            today = datetime.now().date()
            mock_time = datetime.combine(today, datetime.strptime(args.mock_time, "%H:%M").time())
            print(f"🕐 Mock time set to: {args.mock_time}")
        except ValueError:
            print("❌ Invalid time format. Use HH:MM (e.g., 14:30)")
            sys.exit(1)
    
    elif args.test_in:
        # For test mode, we need to fetch prayer times first to calculate proper mock time
        print(f"🧪 Test mode: Setting up azaan to trigger in {args.test_in} seconds...")
        
        # Create temporary app to fetch prayer times
        temp_app = AzaanApp()
        if temp_app.fetch_prayer_times():
            # Find the next prayer time
            next_prayer, next_time, _ = temp_app.get_next_prayer()
            if next_prayer and next_time:
                # Parse the next prayer time
                next_prayer_time = datetime.strptime(next_time, "%H:%M").time()
                today = datetime.now().date()
                next_prayer_datetime = datetime.combine(today, next_prayer_time)
                
                # If prayer time has passed today, use tomorrow
                if next_prayer_datetime <= datetime.now():
                    next_prayer_datetime += timedelta(days=1)
                
                # Set mock time to be X seconds before that prayer
                mock_time = next_prayer_datetime - timedelta(seconds=args.test_in)
                print(f"📅 Next prayer: {next_prayer} at {next_time}")
                print(f"🕐 Mock time set to: {mock_time.strftime('%H:%M:%S')}")
                print(f"⏰ {next_prayer} azaan will trigger in {args.test_in} seconds")
            else:
                print("❌ Could not determine next prayer time")
                sys.exit(1)
        else:
            print("❌ Could not fetch prayer times for test mode")
            sys.exit(1)
    
    app = AzaanApp(mock_time=mock_time)
    app.run()

if __name__ == "__main__":
    main()