from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_answer(buttons):
    keyboard_markup = []
    for button in buttons:
        keyboard_markup.append([KeyboardButton(text=button)], )
    menu = ReplyKeyboardMarkup(
        keyboard=keyboard_markup,
        # resize_keyboard=True
    )
    return menu


def points_list():
    keyboard_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="+3"),
                KeyboardButton(text="+2"),
                KeyboardButton(text="+1"),
            ],
            [
                KeyboardButton(text="0")
            ],
            [
                KeyboardButton(text="-1"),
                KeyboardButton(text="-2"),
                KeyboardButton(text="-3"),
            ],
        ],
        resize_keyboard=True
    )
    return keyboard_markup
