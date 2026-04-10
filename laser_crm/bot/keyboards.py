import json
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def create_inline_keyboard(buttons):
    keyboard = VkKeyboard(inline=True)
    for row in buttons:
        for btn in row:
            keyboard.add_callback_button(
                btn['label'],
                color=btn.get('color', VkKeyboardColor.PRIMARY),
                payload=json.dumps(btn.get('payload', {}))
            )
        keyboard.add_line()
    return keyboard.get_keyboard()

def create_regular_keyboard(buttons, one_time=True):
    keyboard = VkKeyboard(one_time=one_time)
    for row in buttons:
        for btn in row:
            keyboard.add_button(btn['label'], color=btn.get('color', VkKeyboardColor.PRIMARY))
        keyboard.add_line()
    return keyboard.get_keyboard()
