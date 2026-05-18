import vk_api
from vk_api.vk_api import VkUpload
from django.conf import settings
import requests
import os


class VKClient:
    def __init__(self):
        self.vk = vk_api.VkApi(token=settings.VK_TOKEN)
        self.api = self.vk.get_api()

    def send_message(self, user_id, text, keyboard=None):
        message_data = {
            'user_id': user_id,
            'message': text,
            'random_id': 0,
        }
        if keyboard:
            message_data['keyboard'] = keyboard
        self.api.messages.send(**message_data)

    def download_file(self, url, filename):
        media_root = settings.MEDIA_ROOT
        layouts_dir = os.path.join(media_root, 'layouts')
        os.makedirs(layouts_dir, exist_ok=True)
        
        filepath = os.path.join(layouts_dir, filename)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
