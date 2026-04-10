from .models import UserSession

def get_user_state(vk_id):
    try:
        session = UserSession.objects.get(vk_id=vk_id)
        return session.state, session.data
    except UserSession.DoesNotExist:
        return None, {}

def set_user_state(vk_id, state, data=None):
    UserSession.objects.update_or_create(
        vk_id=vk_id,
        defaults={'state': state, 'data': data or {}}
    )

def clear_user_state(vk_id):
    UserSession.objects.filter(vk_id=vk_id).delete()
