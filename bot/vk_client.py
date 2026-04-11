import logging
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll
from django.conf import settings

logger = logging.getLogger(__name__)

vk_session = VkApi(token=settings.VK_TOKEN, api_version='5.199')
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
