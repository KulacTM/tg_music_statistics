import sqlite3

from aiogram import Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from tgbot.config import load_config
from tgbot.db.sql_executor import db
from tgbot.misc import states
from tgbot.keyboards.reply import user_answer, points_list

config = load_config(".env")
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')


async def user_start(message: Message):
    await add_user_to_db(message)


async def add_user_to_db(message):
    try:
        db.add_user(id=message.from_user.id, name=message.from_user.full_name)
    except sqlite3.IntegrityError as err:
        print(err)
    await message.answer(f"Ваш уникальный id - <b>{message.from_user.id}</b>. Используйте его, чтобы подключиться к "
                         f"игре с другими пользователями.")
    await choose_player_num(message)


async def choose_player_num(message):
    num_of_players = ["2"]
    await message.answer("Выберите количество игроков", reply_markup=user_answer(num_of_players))
    await states.GameStates.choose_players_num.set()


async def choose_gamemode(message):
    gamemodes = ["Стандартный"]
    await message.answer("Выберите режим игры", reply_markup=user_answer(gamemodes))
    await states.GameStates.choose_gamemode.set()


async def choose_player(message):
    await message.answer("Введите id игрока, с которым вы хотите сыграть", reply_markup=ReplyKeyboardRemove())
    await states.GameStates.choose_player.set()


async def start_game(message, state: FSMContext):
    # поиск по базе данных
    player = db.find_user_by_id(message.from_user.id)
    opponent = db.find_user_by_id(message.text)
    user_stats = db.find_player_stats(message.from_user.id, message.text)

    await message.answer(f"Ваш оппонент - {opponent[1]}")

    # если статистика не найдена
    if not user_stats:
        db.create_player_stats(message.from_user.id, message.text, 0, 0, 0, 0, 0)
        db.create_player_stats(message.text, message.from_user.id, 0, 0, 0, 0, 0)
        await message.answer(f"На данный момент вы не сыграли с ним ни одной игры. Пора это исправить!",
                             reply_markup=user_answer(["Начать"]))

    # если статистика найдена
    else:
        await message.answer(f"<b>Ваша статистика с данным игроком:</b>\n"
                             f"Сыграно игр - {user_stats[2]}\n"
                             f"Побед - {user_stats[3]}\n"
                             f"Поражений - {user_stats[4]}\n"
                             f"Ничьих - {user_stats[5]}\n"
                             f"Всего очков заработано - {user_stats[6]}\n"
                             , reply_markup=user_answer(["Начать"]))

    # сохраняем данные
    await state.update_data(opponent=opponent)
    await state.update_data(player=player)
    await state.update_data(round=1)
    await state.update_data(player_points=0)
    await state.update_data(opponent_points=0)

    # старт игры
    await states.GameStates.start_standard_game.set()


async def the_game(message, state: FSMContext):
    # получаем данные из состояния
    data = await state.get_data()

    current_round = data.get("round")
    player = data.get("player")
    opponent = data.get("opponent")
    player_points = data.get("player_points")
    opponent_points = data.get("opponent_points")

    max_rounds = 5

    # проверяем не наступил ли конец игры
    if current_round <= max_rounds:
        await message.answer(f"Раунд {current_round}")
        await bot.send_message(opponent[0], f"Раунд {current_round}")

    # напоминалка о смене плейлистов
    if current_round == 11:
        await message.answer(f"Время меняться плейлистами!")

    await count_points(message, state, player, opponent, player_points, opponent_points, current_round, max_rounds)

    if current_round > max_rounds:
        await end_game(player, opponent, message, state)

    # обновляем раунд
    if message.text == "+3" or "+2" or "+1" or "0" or "-1" or "-2" or "+3" or "Начать":
        current_round += 1
    await state.update_data(round=current_round)


async def count_points(message, state, player, opponent, player_points, opponent_points, current_round, max_rounds):
    # кто кому загадывает
    if current_round % 2 == 0:  # раунд ведет оппонент
        if message.text == "+3":
            opponent_points += 3
        if message.text == "+2":
            opponent_points += 2
        if message.text == "+1":
            opponent_points += 1
        if message.text == "-3":
            opponent_points -= 3
        if message.text == "-2":
            opponent_points -= 2
        if message.text == "-1":
            opponent_points -= 1
        elif message.text == "Начать" or "0":
            pass
        else:
            return
        await state.update_data(opponent_points=opponent_points)

        if current_round <= max_rounds:
            await message.answer(f"Текущий счёт:\n\n"
                                 f"У вас  {player_points} б.\n"
                                 f"У вашего оппонента {opponent[1]}  {opponent_points} б.")
            await bot.send_message(opponent[0], f"Текущий счёт:\n\n"
                                                f"У вас  {opponent_points} б.\n"
                                                f"У вашего оппонента {player[1]}  {player_points} б.")

            await message.answer(f"Игрок <b>{opponent[1]}</b> загадывает вам трек\n\n"
                                 f"Какую оценку он вам поставил?", reply_markup=points_list())
            await bot.send_message(opponent[0], "Вы загадываете трек вашему оппоненту")

    elif current_round % 2 != 0:  # раунд ведет игрок
        if message.text == "+3":
            player_points += 3
        if message.text == "+2":
            player_points += 2
        if message.text == "+1":
            player_points += 1
        if message.text == "-3":
            player_points -= 3
        if message.text == "-2":
            player_points -= 2
        if message.text == "-1":
            player_points -= 1
        elif message.text == "Начать" or "0":
            pass
        else:
            return
        await state.update_data(player_points=player_points)

        if current_round <= max_rounds:
            await message.answer(f"Текущий счёт:\n\n"
                                 f"У вас {player_points} б.\n"
                                 f"У вашего оппонента {opponent[1]}  {opponent_points} б.")
            await bot.send_message(opponent[0], f"Текущий счёт:\n\n"
                                                f"У вас  {opponent_points} б.\n"
                                                f"У вашего оппонента {player[1]}  {player_points} б.")

            await message.answer(f"Вы загадываете трек своему оппоненту\n\n"
                                 f"Какую оценку заслуживает {opponent[1]}?", reply_markup=points_list())
            await bot.send_message(opponent[0], "Вам загадывает трек ваш оппонент")


async def end_game(player, opponent, message, state):
    data = await state.get_data()

    player_points = data.get("player_points")
    opponent_points = data.get("opponent_points")

    player_stats = []
    opponent_stats = []
    player_stats_tuple = db.find_player_stats(player[0], opponent[0])
    opponent_stats_tuple = db.find_player_stats(opponent[0], player[0])

    # Конвертация tuple в list
    for stat in player_stats_tuple:
        player_stats.append(stat)
    for stat in opponent_stats_tuple:
        opponent_stats.append(stat)

    # total points & games
    player_stats[2] += 1
    opponent_stats[2] += 1
    player_stats[6] += player_points
    opponent_stats[6] += opponent_points

    # wins losses draws
    if player_points > opponent_points:
        player_stats[3] += 1
        opponent_stats[4] += 1
        await message.answer(f"Игра завершена\n\n"
                             f"Побеждаете вы со счётом {player_points} б.\n"
                             f"Ваш оппонент набирает {opponent_points} б.", reply_markup=ReplyKeyboardRemove())
        await bot.send_message(opponent[0], f"Игра завершена\n\n"
                                            f"Побеждает ваш оппонент со счётом {player_points} б.\n"
                                            f"Вы набираете {opponent_points} б.")

    elif opponent_points > player_points:
        opponent_stats[3] += 1
        player_stats[4] += 1
        await message.answer(f"Игра завершена\n\n"
                             f"Побеждает ваш оппонент со счётом {opponent_points} б.\n"
                             f"Вы набираете  {player_points} б.", reply_markup=ReplyKeyboardRemove())
        await bot.send_message(opponent[0], f"Игра завершена\n\n"
                                            f"Побеждаете вы со счетом {opponent_points} б.\n"
                                            f"Ваш оппонент набирает {player_points} б.")
    else:
        await message.answer(f"Игра завершена\n\n"
                             f"Ничья! Вы оба набрали по {player_points} б.\n",
                             reply_markup=ReplyKeyboardRemove())
        await bot.send_message(opponent[0], f"Игра завершена\n\n"
                                            f"Ничья! Вы оба набрали по {player_points} б.\n")
        player_stats[5] += 1
        opponent_stats[5] += 1

    db.update_player_stats(player_stats[2], player_stats[3], player_stats[4], player_stats[5], player_stats[6],
                           player_stats[0], player_stats[1])
    db.update_player_stats(opponent_stats[2], opponent_stats[3], opponent_stats[4], opponent_stats[5],
                           opponent_stats[6],
                           opponent_stats[0], opponent_stats[1])

    await message.answer("Чтобы начать новую игру, наберите /start")
    await bot.send_message(opponent[0], "Для начала новой игры один из игроков должен набрать /start")
    await state.finish()


def register_game_handlers(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_message_handler(choose_gamemode, state=states.GameStates.choose_players_num)
    dp.register_message_handler(choose_player, state=states.GameStates.choose_gamemode)
    dp.register_message_handler(start_game, state=states.GameStates.choose_player)
    dp.register_message_handler(the_game, state=states.GameStates.start_standard_game)
