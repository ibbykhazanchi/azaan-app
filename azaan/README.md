# Azaan App

A Python application that automatically plays azaan audio at Islamic prayer times for Princeton, New Jersey.

## Features

- Fetches accurate prayer times from the Aladhan API
- Plays azaan audio automatically at each prayer time
- Supports all 5 daily prayers (Fajr, Dhuhr, Asr, Maghrib, Isha)
- Updates prayer times daily
- Uses ISNA calculation method
- **Web interface** with real-time countdown to next prayer
- Beautiful responsive UI accessible from any device

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the azaan audio file (`1585301007.mp3`) is in the same directory

3. Run the application:
```bash
python azaan_app.py
```

## Usage

The app will:
- Fetch today's prayer times for Princeton, NJ
- Schedule azaan playback for each prayer time
- Start a web server at `http://localhost:8080`
- Run continuously in the background
- Automatically update prayer times daily at midnight

**Web Interface:** Open `http://localhost:8080` in your browser to see:
- Current prayer times
- Real-time countdown to next prayer
- Beautiful responsive design

Press `Ctrl+C` to stop the application.

## Requirements

- Python 3.6+
- Internet connection (for fetching prayer times)
- Audio output device
- `1585301007.mp3` audio file

## Location

Currently configured for Princeton, New Jersey using the ISNA calculation method. To change location, modify the `city` and `country` variables in `azaan_app.py`.