import logging
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll
from django.conf import settings

logger = logging.getLogger(__name__)

def get_vk_session():
    """Ленивая инициализация VK сессии"""
    if not hasattr(settings, 'VK_TOKEN') or not settings.VK_TOKEN:
        logger.warning("VK_TOKEN не настроен")
        return None, None, None
    
    vk_session = VkApi(token=settings.VK_TOKEN, api_version='5.199')
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    return vk_session, vk, longpoll

# Глобальные переменные будут инициализированы при первом использовании
vk_session = None
vk = None
longpoll = None
