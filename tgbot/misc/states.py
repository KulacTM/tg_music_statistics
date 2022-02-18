from aiogram.dispatcher.filters.state import StatesGroup, State


class GameStates(StatesGroup):
    choose_players_num = State()
    choose_gamemode = State()
    choose_player = State()
    start_standard_game = State()
