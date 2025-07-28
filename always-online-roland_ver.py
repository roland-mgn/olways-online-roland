import sys
import json
import time
import requests
import websocket
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

status = "online"
custom_status = "youtube.com/@SealedSaucer"  # You can change this dynamically
usertoken = os.getenv("DISCORD_TOKEN")  # Get the token from an environment variable for better security

# Ensure the token is provided
if not usertoken:
    logger.error("[ERROR] Discord token is missing. Please set it in your environment.")
    sys.exit(1)

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

def validate_token():
    """Validate the provided Discord token."""
    try:
        validate = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
        if validate.status_code != 200:
            logger.error("[ERROR] Your token might be invalid. Please check it again.")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERROR] Request failed: {e}")
        sys.exit(1)

validate_token()

userinfo = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]
logger.info(f"Logged in as {username}#{discriminator} ({userid}).")

def onliner(token, status):
    """Connect to Discord's Gateway and maintain online status."""
    try:
        ws = websocket.create_connection("wss://gateway.discord.gg/?v=9&encoding=json")
        start = json.loads(ws.recv())
        heartbeat = start["d"]["heartbeat_interval"]
        logger.info("Connected to Discord Gateway.")

        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 10",
                    "$browser": "Google Chrome",
                    "$device": "Windows",
                },
                "presence": {"status": status, "afk": False},
            },
            "s": None,
            "t": None,
        }
        ws.send(json.dumps(auth))
        logger.info("Sent authentication request.")

        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [
                    {
                        "type": 4,
                        "state": custom_status,
                        "name": "Custom Status",
                        "id": "custom",
                    }
                ],
                "status": status,
                "afk": False,
            },
        }
        ws.send(json.dumps(cstatus))
        logger.info(f"Custom status set to: {custom_status}")

        online = {"op": 1, "d": "None"}
        time.sleep(heartbeat / 1000)  # Wait for the next heartbeat interval
        ws.send(json.dumps(online))

    except websocket.WebSocketException as e:
        logger.error(f"[ERROR] WebSocket connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] An unexpected error occurred: {e}")
        return False

    return True

def run_onliner():
    """Run the bot to keep the status online."""
    while True:
        if not onliner(usertoken, status):
            logger.error("Reconnecting...")
            time.sleep(5)  # Wait for a few seconds before trying again
        else:
            time.sleep(50)  # Keep the status updated every 50 seconds

if __name__ == "__main__":
    run_onliner()