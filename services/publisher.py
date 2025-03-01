import requests
from services.utils import handle_error
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID


def publish_carousel(img_links, description):
    # Step 1: Create individual item containers for each image
    item_ids = []
    for img_url in img_links:
        payload = {
            "image_url": img_url,
            "is_carousel_item": True,
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
        response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media", data=payload)
        response_data = response.json()
        if "id" in response_data:
            item_ids.append(response_data["id"])
        else:
            return handle_error(f"Error creating item container for {img_url}: {response_data.get('error', {})}")

    # Step 2: Create a carousel container
    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(item_ids),
        "caption": description,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media", data=payload)
    response_data = response.json()
    if "id" not in response_data:
        return handle_error(f"Error creating carousel container: {response_data.get('error', {})}")
        
    # Step 3: Publish the carousel
    payload = {
        "creation_id": response_data["id"],
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media_publish", data=payload)
    response_data = response.json()
    if "id" not in response_data:
        return handle_error(f"Error publishing carousel: {response_data.get('error', {})}")

    return None

def publish_single_image(img_links, description):
    img_url = img_links[0]
    payload = {
        "image_url": img_url,
        "caption": description,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media", data=payload)
    response_data = response.json()
    if "id" not in response_data:
        return handle_error(f"Error creating single image post for {img_url}: {response_data.get('error', {})}")
            
    # Publish the single image
    payload = {
        "creation_id": response_data["id"],
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    response = requests.post(f"https://graph.facebook.com/v17.0/{INSTAGRAM_USER_ID}/media_publish", data=payload)
    response_data = response.json()
    if "id" not in response_data:
        return handle_error(f"Error publishing single image: {response_data.get('error', {})}")
    
    return None
