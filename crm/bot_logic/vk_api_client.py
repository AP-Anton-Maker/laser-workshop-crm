import os
import requests
from django.conf import settings

class VKClient:
    def __init__(self):
        self.token = settings.VK_TOKEN
        self.api_url = "https://api.vk.com/method"
        self.version = "5.131"

    def _request(self, method, data):
        """Внутренний метод для отправки запросов к API ВК."""
        data['access_token'] = self.token
        data['v'] = self.version
        response = requests.post(f"{self.api_url}/{method}", data=data)
        return response.json()

    def send_message(self, user_id, text, keyboard=None):
        """Отправляет текстовое сообщение (с клавиатурой или без)."""
        payload = {
            'peer_id': user_id,
            'message': text,
            'random_id': 0,
        }
        
        if keyboard:
            payload['keyboard'] = keyboard
            
        return self._request('messages.send', payload)

    def download_file(self, url, file_name):
        """
        Скачивает файл по URL и сохраняет в data/media/layouts/.
        Возвращает относительный путь для сохранения в БД.
        """
        base_dir = os.path.join(settings.MEDIA_ROOT, 'layouts')
        os.makedirs(base_dir, exist_ok=True)
        
        file_path = os.path.join(base_dir, file_name)
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            relative_path = os.path.join('layouts', file_name)
            return relative_path
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
