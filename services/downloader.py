import os
from telegram import Update
from core.data_manager import DataManager

def save_telegram_images(manager: DataManager) -> list:
    saved_image_paths = []
    
    current_directory = os.getcwd()
    image_folder_path = os.path.join(current_directory, 'temp_images')
    
    if not os.path.exists(image_folder_path):
        os.makedirs(image_folder_path)

    for image_id in manager.images:
        file = manager.bot.get_file(image_id)
        local_path = os.path.join(image_folder_path, f"{image_id}.jpg")
        file.download(local_path)
        saved_image_paths.append(local_path)
    
    return saved_image_paths

def cleanup_telegram_images(saved_image_paths):
    for image_path in saved_image_paths:
        os.remove(image_path)