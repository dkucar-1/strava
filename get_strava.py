#!/usr/bin/env python3
import requests
from strava_auth import get_authorization_code, exchange_token

def get_athlete(token_data):
    url = "https://www.strava.com/api/v3/athlete"
    header = {'Authorization': 'Bearer '+token_data['access_token']}
    return requests.get(url, headers=header).json()

def get_activity(token, activity_id):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    header = {'Authorization': 'Bearer ' + token}
    resp = requests.get(url, headers=header)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Found: {data['name']} on {data['start_date_local']}, {data['distance']}m")
    else:
        print(f"Activity {activity_id} not found: {resp.status_code}")

def put_activities(creds, payload, filename):
    url = 'https://www.strava.com/api/v3/uploads'
    headers = {'Authorization': 'Bearer ' + creds}
    files = {
        'file': (filename, payload.encode('utf-8'), 'application/gpx+xml'),
        'data_type': (None, 'gpx'),
        'name': (None, filename.rsplit('.', 1)[0]),
    }
    resp = requests.post(url, headers=headers, files=files)
    resp.raise_for_status()
    return resp.json()

def process_gpx(filename, creds):
    import re
    with open(filename, 'r') as read_file:
        file = read_file.read()
        pattern = re.compile(r'(.+?)<trk>')
        header = pattern.search(file)
        strava_header = '<?xml version="1.0" encoding="UTF-8"?><gpx creator="StravaGPX" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">'
        if header:
            text = file.removeprefix(header.group(1)).split("<trk>")
            for t in text[1:]:
                name_regex = re.compile(r'<name>(.+?)</name>')
                if name_regex.search(t):
                    name = name_regex.search(t).group(1).strip()
                else:
                    name = 'Unnamed Activity'
                new_text = re.sub(r'(</name>)', r'\1<type>hiking</type>', t) 
                payload = strava_header + '<trk>' + new_text.rstrip()
                if not payload.endswith('</gpx>'):
                    payload += '</gpx>'
                filename = f"{name}.gpx"
                with open(filename, 'w') as write_file:
                    write_file.write(payload)
                print(f"Uploading {filename}...")
                result = put_activities(creds, payload, filename)
                print(f"Upload result: {result}")
    return result

# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    code = get_authorization_code()
    token_data = exchange_token(code)

    file = 'test.gpx'
    result = process_gpx(file, token_data['access_token'])

