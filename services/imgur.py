import requests
from services.utils import handle_error
from services.downloader import cleanup_telegram_images
from config import IMGUR_CLIENT_ID, IMGUR_ENDPOINT, IMGUR_DELETE_ENDPOINT

def upload_to_imgur(image_paths):
    res = {
        "imgur_links": [],
        "deletehash": [],
        "success": False,
        "message": ""
    }

    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }

    for image_path in image_paths:
        with open(image_path, 'rb') as image_file:
            files = {
                'image': image_file
            }
            response = requests.post(IMGUR_ENDPOINT, headers=headers, files=files)
            response_data = response.json()
            
            if response.status_code == 200:
                res["imgur_links"].append(response_data['data']['link'])
                res["deletehash"].append(response_data['data']['deletehash'])
                res["success"] = True
            else:
                res["success"] = False
                res["message"] = response_data.get('data', {}).get('error', '')
                delete_from_imgur(res["deletehash"])
                break

    cleanup_telegram_images(image_paths)
                
    return res

def delete_from_imgur(deletehashes):
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    
    for deletehash in deletehashes:
        response = requests.delete(IMGUR_DELETE_ENDPOINT.format(deletehash=deletehash), headers=headers)
        
        if response.status_code != 200:
            handle_error(f"Error deleting image with deletehash {deletehash} from Imgur: {response.text}")
