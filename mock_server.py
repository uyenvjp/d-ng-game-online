#!/usr/bin/env python3
"""
Dungeon Corporation - Mock Backend Server
Replaces dead bigshot-games.xyz backend for local/offline play
"""
from flask import Flask, request, jsonify
import time
import json
import hashlib
from pathlib import Path

app = Flask(__name__)

# Storage paths
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def get_current_timestamp():
    """Return current Unix timestamp"""
    return int(time.time())

def make_response(data, result="complete"):
    """Standard response wrapper"""
    return jsonify({
        "_result": result,
        "_timestamp": get_current_timestamp(),
        **data
    })

@app.route('/timestamp', methods=['GET', 'POST'])
@app.route('/time', methods=['GET', 'POST'])
def get_timestamp():
    """Time synchronization endpoint - critical for game startup"""
    return make_response({
        "timestamp": get_current_timestamp(),
        "serverTime": int(time.time()),
        "timezone": 0,
        "utcOffset": 0,
    })

@app.route('/login', methods=['POST'])
def login():
    """User login - accepts Google Play Games or guest"""
    data = request.form or request.json or {}

    user_id = data.get('_userID') or data.get('_playgamesID') or data.get('_gameID') or 'guest_user'
    user_name = data.get('_userName', 'Player')
    platform = data.get('_platform', 'android')

    # Generate stable login key
    login_key = hashlib.sha256(f"{user_id}{platform}".encode()).hexdigest()[:32]

    # Load or create user save
    save_file = DATA_DIR / f"{user_id}.json"
    if save_file.exists():
        user_data = json.loads(save_file.read_text())
    else:
        # New user - minimal starting data
        user_data = {
            "_userID": user_id,
            "_userName": user_name,
            "_platform": platform,
            "_registTime": get_current_timestamp(),
            "_gameID": user_id,
            "_dataFile": "",  # Empty = new game
            "_isBan": False,
            "_chatBan": False,
            "_maintenance": False,
        }
        save_file.write_text(json.dumps(user_data, indent=2))

    return make_response({
        "_loginKey": login_key,
        "_userID": user_id,
        "_userName": user_name,
        "_gameID": user_data.get("_gameID", user_id),
        "_dataFile": user_data.get("_dataFile", ""),
        "_isBan": False,
        "_chatBan": False,
        "_maintenance": False,
        "_banIgnore": False,
        "_isNewUser": not save_file.exists(),
    })

@app.route('/userdata', methods=['GET', 'POST'])
@app.route('/save', methods=['POST'])
def save_data():
    """Save/load user game data"""
    data = request.form or request.json or {}
    user_id = data.get('_userID') or data.get('_gameID', 'guest_user')

    save_file = DATA_DIR / f"{user_id}.json"

    if request.method == 'POST' and '_dataFile' in data:
        # Save data
        save_content = {
            "_userID": user_id,
            "_dataFile": data.get('_dataFile'),
            "_backUp": data.get('_backUp', ''),
            "_lastSaveTime": get_current_timestamp(),
        }
        if save_file.exists():
            existing = json.loads(save_file.read_text())
            existing.update(save_content)
            save_content = existing

        save_file.write_text(json.dumps(save_content, indent=2))
        return make_response({"_complete": True})

    # Load data
    if save_file.exists():
        user_data = json.loads(save_file.read_text())
        return make_response({
            "_dataFile": user_data.get("_dataFile", ""),
            "_backUp": user_data.get("_backUp", ""),
        })

    return make_response({"_dataFile": "", "_backUp": ""})

@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    """Mock leaderboard - returns empty for offline mode"""
    return make_response({
        "_leaderboard": [],
        "_rank": 0,
        "_score": 0,
        "_totalUsers": 1,
    })

@app.route('/event', methods=['POST'])
@app.route('/events', methods=['POST'])
def events():
    """Receive events - just acknowledge"""
    return make_response({"_eventNo": 0})

@app.route('/userAgreement', methods=['GET'])
@app.route('/userAgreement,', methods=['GET'])
def user_agreement():
    """Terms of service placeholder"""
    return """
    <html><body>
    <h1>Dungeon Corporation - Local Server</h1>
    <p>This is a mock server for offline/local play.</p>
    <p>Original server (bigshot-games.xyz) is no longer operational.</p>
    </body></html>
    """

@app.route('/check', methods=['GET', 'POST'])
def version_check():
    """Version/maintenance check"""
    return make_response({
        "_updateCheck": False,
        "_maintenance": False,
        "_maintenance_exit": False,
    })

@app.route('/', methods=['GET'])
def index():
    return """
    <html><head><title>Dungeon Corp Mock Server</title></head>
    <body>
    <h1>Dungeon Corporation - Mock Backend Server</h1>
    <p>Server running. Endpoints:</p>
    <ul>
    <li>/timestamp - Time sync</li>
    <li>/login - User login</li>
    <li>/userdata - Load save</li>
    <li>/save - Save data</li>
    <li>/leaderboard - Rankings (mock)</li>
    </ul>
    <p>Server time: """ + str(get_current_timestamp()) + """</p>
    </body></html>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("Dungeon Corporation - Mock Server")
    print("Replacing: https://notice.bigshot-games.xyz/")
    print("=" * 60)
    print("\nTo redirect game:")
    print("1. Add to C:\\Windows\\System32\\drivers\\etc\\hosts:")
    print("   127.0.0.1 notice.bigshot-games.xyz")
    print("   127.0.0.1 bigshot-games.xyz")
    print("\n2. Or use APK patching to change WebAccess.Adress")
    print("\nStarting server on http://127.0.0.1:443 (HTTPS port)")
    print("=" * 60)

    # Run on port 8080 (APK patched to http://10.0.2.2:8080)
    app.run(host='0.0.0.0', port=8080, debug=True)
