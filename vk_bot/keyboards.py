from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def get_empty_keyboard():
    keyboard = VkKeyboard(inline=True)
    return keyboard.get_empty_keyboard()