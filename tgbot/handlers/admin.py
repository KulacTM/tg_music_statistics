import sqlite3

from aiogram import Dispatcher
from aiogram.types import Message
from .game import add_user_to_db


async def admin_start(message: Message):
    await add_user_to_db(message)


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
