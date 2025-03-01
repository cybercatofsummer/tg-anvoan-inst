from services.utils import handle_error
import requests
from config import FACEBOOK_APP_ID, FACEBOOK_SECRET, INSTAGRAM_ACCESS_TOKEN

def get_long_lived_token():
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": FACEBOOK_APP_ID,
        "client_secret": FACEBOOK_SECRET,
        "fb_exchange_token": INSTAGRAM_ACCESS_TOKEN
    }

    response = requests.get("https://graph.facebook.com/v17.0/oauth/access_token", params=params)
    data = response.json()

    if "access_token" in data:
        return data["access_token"]
    else:
        handle_error(f"Error getting long-lived token: {data.get('error', {})}")
        return None

if __name__ == '__main__':
    print('long_live_token => ', get_long_lived_token())
