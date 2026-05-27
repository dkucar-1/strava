#!/usr/bin/env python3
import requests, logging, sys
from requests.exceptions import HTTPError
from strava_auth import get_authorization_code, exchange_token

def get_athlete(token_data) -> dict:
    url = "https://www.strava.com/api/v3/athlete"
    header = {'Authorization': 'Bearer '+token_data['access_token']}
    return requests.get(url, headers=header).json()

def get_activity(token, activity_id) -> dict:
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    header = {'Authorization': 'Bearer ' + token}
    resp = requests.get(url, headers=header)
    if resp.status_code == 200:
        data = resp.json()
        logging.info(f"Found: {data['name']} on {data['start_date_local']}, {data['distance']}m")
    else:
        logging.warning(f"Activity {activity_id} not found: {resp.status_code}")

def put_activities(creds, payload, name) -> tuple:
    url = 'https://www.strava.com/api/v3/uploads'
    headers = {'Authorization': 'Bearer ' + creds}
    files = {
        'file': (name + '.gpx', payload.encode('utf-8'), 'application/gpx+xml'),
        'data_type': (None, 'gpx'),
        'name': (None, name),
    }
    try:
        resp = requests.post(url, headers=headers, files=files)
        resp.raise_for_status()
    except HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    return resp.status_code, resp.content

def parse_gpx(filename) -> dict:
    import re
    activities = {}
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
                    name = name_regex.search(t).group(1).strip().replace('/', '-')
                else:
                    name = 'Unnamed Activity'
                new_text = re.sub(r'(</name>)', r'\1<type>hiking</type>', t) 
                payload = strava_header + '<trk>' + new_text.rstrip()
                if not payload.endswith('</gpx>'):
                    payload += '</gpx>'
                activities[name] = payload
    return activities

def upload_gpx(filename, creds) -> None:
    activities = parse_gpx(filename)
    for name, payload in activities.items():
            filename = f"{name}.gpx"
            with open(filename, 'w') as write_file:
                write_file.write(payload)
                result = put_activities(creds, payload, name)
                if result[0] > 399:
                    logging.error(f"Failed to upload {filename}: {result[1]}")
                else:
                    logging.info(f"Successfully uploaded {filename}")

# ── Main ───────────────────────────────────────────────────────────────────
def main(args) -> None:
    logging.basicConfig(level=logging.INFO)
    code = get_authorization_code()
    token_data = exchange_token(code)

    filename = args[1] if len(args) > 1 else exit("Nothing to do.\nUsage: get_strava.py <gpx_file>")
    upload_gpx(filename, token_data['access_token'])

if __name__ == "__main__":
    main(sys.argv)