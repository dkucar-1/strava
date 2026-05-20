#!/usr/bin/env python3
"""
Strava OAuth2 Token Flow
========================
Gets a Strava API access token with the scopes you need,
using a lightweight local HTTP server to capture the redirect.

Usage:
  1. Set your CLIENT_ID and CLIENT_SECRET below (or use env vars).
  2. Run: python strava_auth.py
  3. A browser window opens — log in to Strava and click Authorize.
  4. The script captures the code, exchanges it for tokens, and prints them.
"""


import http.server
import urllib.parse
import webbrowser
import requests


def read_env():
    read_file = open('.env', 'r')
    for line in read_file:
        if line.startswith('export client_id='):
            client_id = line.split('=')[1].strip().strip("'")
        elif line.startswith('export client_secret='):
            client_secret = line.split('=')[1].strip().strip("'")
    return {'client_id': client_id, 'client_secret': client_secret}

def get_strava_vars():
    creds = read_env()
    strava_vars = {'CLIENT_ID': creds['client_id'], 'CLIENT_SECRET': creds['client_secret']} 

    # Scopes you want — adjust as needed
    strava_vars['SCOPES'] = "read_all,profile:read_all,activity:read_all,activity:write"

    # Local server to catch the redirect
    strava_vars['REDIRECT_HOST'] = "localhost"
    strava_vars['REDIRECT_PORT'] = 8080
    strava_vars['REDIRECT_URI'] = f"http://{strava_vars['REDIRECT_HOST']}:{strava_vars['REDIRECT_PORT']}/exchange_token"

    return strava_vars


# ── Step 1: Open browser for authorization ─────────────────────────────────
def get_authorization_code():
    """Starts a local server, opens the Strava auth page, and waits for the redirect."""
    strava_vars = get_strava_vars()
    SCOPES = strava_vars['SCOPES']
    REDIRECT_HOST = strava_vars['REDIRECT_HOST']
    REDIRECT_PORT = strava_vars['REDIRECT_PORT']
    REDIRECT_URI = strava_vars['REDIRECT_URI']
    CLIENT_ID = strava_vars['CLIENT_ID']
    auth_code = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if "code" in params:
                auth_code["code"] = params["code"][0]
                auth_code["scope"] = params.get("scope", [""])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<h2>Authorization successful!</h2>"
                    b"<p>You can close this tab and return to the terminal.</p>"
                )
            elif "error" in params:
                auth_code["error"] = params["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h2>Authorization denied.</h2>")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # suppress console noise


    server = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)

    # Build the authorization URL
    auth_url = (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&approval_prompt=force"
        f"&scope={SCOPES}"
    )

    print(f"Opening browser for Strava authorization...\n")
    print(f"If it doesn't open automatically, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    chrome = webbrowser.get("open -a /Applications/Google\\ Chrome.app %s")
    chrome.open(auth_url)
    print("Waiting for redirect from Strava...")

    # Handle exactly one request (the redirect)
    server.handle_request()
    server.server_close()

    if "error" in auth_code:
        raise SystemExit(f"Authorization failed: {auth_code['error']}")
    if "code" not in auth_code:
        raise SystemExit("No authorization code received.")

    print(f"Authorization code received.")
    print(f"Granted scopes: {auth_code.get('scope', 'N/A')}\n")
    return auth_code["code"]

# ── Step 2: Exchange code for tokens ───────────────────────────────────────
def exchange_token(code):
    """POSTs the authorization code to Strava and returns the token response."""
    strava_vars = get_strava_vars()
    CLIENT_ID = strava_vars['CLIENT_ID']
    CLIENT_SECRET = strava_vars['CLIENT_SECRET']
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    )
    response.raise_for_status()
    return response.json()


# ── Step 3 (bonus): Refresh an expired token ───────────────────────────────
def refresh_access_token(refresh_token):
    """Uses a refresh token to get a new access token (handy for later)."""
    strava_vars = get_strava_vars()
    CLIENT_ID = strava_vars['CLIENT_ID']
    CLIENT_SECRET = strava_vars['CLIENT_SECRET']
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    response.raise_for_status()
    return response.json()

