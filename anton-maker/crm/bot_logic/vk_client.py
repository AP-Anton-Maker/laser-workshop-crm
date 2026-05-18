"""
VK API клиент для работы с сообщениями и файлами.
"""

import os
import logging
import requests
from typing import Optional, List, Dict, Any
from django.conf import settings

logger = logging.getLogger('crm.bot')


class VKClient:
    """
    Клиент для работы с VK API.
    Отправка сообщений, загрузка файлов, управление клавиатурами.
    """
    
    API_VERSION = '5.131'
    BASE_URL = 'https://api.vk.com/method'
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.VK_TOKEN
        if not self.token:
            logger.warning("VK Token не настроен")
    
    def _request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Выполнение запроса к VK API."""
        url = f"{self.BASE_URL}/{method}"
        params['v'] = self.API_VERSION
        params['access_token'] = self.token
        
        try:
            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"VK API error: {data['error']}")
                return None
            
            return data.get('response')
        except Exception as e:
            logger.error(f"VK request failed: {e}")
            return None
    
    def send_message(
        self, 
        user_id: int, 
        message: str, 
        keyboard: Optional[Dict] = None,
        attachment: Optional[str] = None,
    ) -> bool:
        """
        Отправка сообщения пользователю.
        
        Args:
            user_id: ID пользователя ВКонтакте
            message: Текст сообщения
            keyboard: JSON-клавиатура
            attachment: Вложения (фото, документы)
            
        Returns:
            True если успешно
        """
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': 0,
        }
        
        if keyboard:
            params['keyboard'] = str(keyboard).replace("'", '"')
        
        if attachment:
            params['attachment'] = attachment
        
        result = self._request('messages.send', params)
        return result is not None
    
    def download_file(self, url: str, filename: str) -> Optional[str]:
        """
        Скачивание файла из ВКонтакте.
        
        Args:
            url: URL файла
            filename: Имя для сохранения
            
        Returns:
            Путь к сохраненному файлу или None
        """
        from django.conf import settings
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            media_dir = settings.MEDIA_ROOT / 'layouts'
            media_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = media_dir / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"File downloaded: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def upload_photo(self, user_id: int, photo_path: str) -> Optional[str]:
        """
        Загрузка фото для отправки пользователю.
        
        Args:
            user_id: ID получателя
            photo_path: Путь к файлу
            
        Returns:
            Строка вложения для messages.send
        """
        # Получаем URL для загрузки
        upload_data = self._request('photos.getMessagesUploadServer', {
            'peer_id': user_id,
        })
        
        if not upload_data or 'upload_url' not in upload_data:
            return None
        
        # Загружаем фото
        with open(photo_path, 'rb') as f:
            upload_response = requests.post(
                upload_data['upload_url'],
                files={'photo': f}
            ).json()
        
        # Сохраняем фото
        save_data = self._request('photos.saveMessagesPhoto', {
            'photo': upload_response.get('photo', ''),
            'server': upload_response.get('server', 0),
            'hash': upload_response.get('hash', ''),
        })
        
        if save_data and len(save_data) > 0:
            return f"photo{save_data[0]['owner_id']}_{save_data[0]['id']}"
        
        return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе."""
        data = self._request('users.get', {
            'user_ids': user_id,
            'fields': 'first_name,last_name,photo_100',
        })
        
        if data and len(data) > 0:
            return data[0]
        return None
