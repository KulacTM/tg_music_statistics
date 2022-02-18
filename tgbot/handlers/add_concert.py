from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext

from tgbot.misc import states
from tgbot.db.sql_executor import db


async def start_adding_concert(message: types.Message):
    if message.text == "Добавить концерт":
        await message.answer(f"Введите название исполнителя")
        await states.AddConcert().EnterArtist.set()


async def enter_date(message: types.Message, state: FSMContext):
    await state.update_data(artist=message.text)
    await message.answer("Введите дату мероприятия")
    await states.AddConcert.EnterDate.set()


async def enter_place(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("Введите место проведения мероприятия")
    await states.AddConcert.EnterPlace.set()


async def concert_info(message: types.Message, state: FSMContext):
    data = await state.get_data()
    artist = data.get("artist")
    date = data.get("date")
    place = message.text

    await message.answer(f"Ваш концерт успешно добавлен:\n"
                         f"Исполнитель - {artist}\n"
                         f"Дата - {date}\n"
                         f"Место - {place}")

    db.add_concert(message.from_user.id, artist, date, place)

    await state.finish()


def register_concert(dp: Dispatcher):
    dp.register_message_handler(start_adding_concert)
    dp.register_message_handler(enter_date, state=states.AddConcert.EnterArtist)
    dp.register_message_handler(enter_place, state=states.AddConcert.EnterDate)
    dp.register_message_handler(concert_info, state=states.AddConcert.EnterPlace)
