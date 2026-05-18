"""
VK API клиент для работы с ВКонтакте.
Отправка сообщений, загрузка файлов, управление ботом.
"""

import requests
import vk_api
from vk_api.vk_api import VkUpload
from django.conf import settings
from typing import Optional, Dict, Any, List


class VKClient:
    """
    Клиент для работы с VK API.
    
    Поддерживает:
    - Отправку текстовых сообщений
    - Отправку сообщений с вложениями
    - Загрузку файлов по URL
    - Получение информации о пользователе
    """
    
    def __init__(self):
        """Инициализация клиента."""
        self.api_version = getattr(settings, 'VK_API_VERSION', '5.131')
        self.service_token = getattr(settings, 'VK_SERVICE_TOKEN', '')
        self.app_id = getattr(settings, 'VK_APP_ID', '')
        
        # Инициализация vk_api
        self.vk_session = None
        self.vk = None
        
        if self.service_token:
            self.vk_session = vk_api.VkApi(token=self.service_token)
            self.vk = self.vk_session.get_api()
    
    def send_message(
        self,
        user_id: int,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Отправить сообщение пользователю.
        
        Args:
            user_id: ID пользователя ВКонтакте
            message: Текст сообщения
            attachments: Список вложений (фото, документы)
            
        Returns:
            bool: True если успешно
        """
        if not self.vk:
            return False
        
        try:
            params = {
                'peer_id': user_id,
                'message': message,
                'random_id': 0,  # Будет заменен на уникальное значение
            }
            
            if attachments:
                params['attachment'] = ','.join(attachments)
            
            self.vk.messages.send(**params)
            return True
            
        except Exception as e:
            print(f'Ошибка отправки сообщения: {e}')
            return False
    
    def send_keyboard(
        self,
        user_id: int,
        keyboard: Dict[str, Any],
        message: str
    ) -> bool:
        """
        Отправить сообщение с клавиатурой.
        
        Args:
            user_id: ID пользователя
            keyboard: JSON клавиатуры
            message: Текст сообщения
            
        Returns:
            bool: True если успешно
        """
        if not self.vk:
            return False
        
        import json
        import random
        
        try:
            self.vk.messages.send(
                peer_id=user_id,
                message=message,
                keyboard=json.dumps(keyboard),
                random_id=random.randint(0, 2**31)
            )
            return True
            
        except Exception as e:
            print(f'Ошибка отправки клавиатуры: {e}')
            return False
    
    def download_file(self, url: str, filename: str) -> Optional[str]:
        """
        Скачать файл по URL.
        
        Args:
            url: URL файла
            filename: Имя для сохранения
            
        Returns:
            str: Путь к сохраненному файлу или None
        """
        from django.conf import settings
        import os
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем в media/layouts/
            save_dir = os.path.join(settings.MEDIA_ROOT, 'layouts')
            os.makedirs(save_dir, exist_ok=True)
            
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            print(f'Ошибка скачивания файла: {e}')
            return None
    
    def upload_photo(self, file_path: str, peer_id: int) -> Optional[str]:
        """
        Загрузить фото и получить attachment ID.
        
        Args:
            file_path: Путь к файлу
            peer_id: ID получателя
            
        Returns:
            str: Attachment ID (photo-XXXX_YYYY) или None
        """
        if not self.vk_session:
            return None
        
        try:
            upload = VkUpload(self.vk_session)
            
            # Загружаем фото
            photo = upload.photo_messages(
                photo=file_path,
                peer_id=peer_id
            )
            
            if photo:
                photo_obj = photo[0]
                return f"photo{photo_obj['owner_id']}_{photo_obj['id']}"
            
            return None
            
        except Exception as e:
            print(f'Ошибка загрузки фото: {e}')
            return None
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о пользователе.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            dict: Информация о пользователе или None
        """
        if not self.vk:
            return None
        
        try:
            user = self.vk.users.get(
                user_ids=[user_id],
                fields=['first_name', 'last_name', 'photo_100']
            )
            
            if user:
                return user[0]
            
            return None
            
        except Exception as e:
            print(f'Ошибка получения информации о пользователе: {e}')
            return None
    
    def send_notification_to_admin(self, message: str) -> bool:
        """
        Отправить уведомление администратору.
        
        Args:
            message: Текст уведомления
            
        Returns:
            bool: True если успешно
        """
        admin_vk_id = getattr(settings, 'ADMIN_VK_ID', None)
        
        if not admin_vk_id:
            return False
        
        return self.send_message(admin_vk_id, message)
