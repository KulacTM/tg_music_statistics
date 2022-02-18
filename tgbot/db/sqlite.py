import sqlite3


class Database:
    def __init__(self, path_to_db="tgbot/db/main.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        cursor.execute(sql, parameters)

        data = None

        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()

        connection.close()
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE Users (
        id int NOT NULL,
        name varchar(255) NOT NULL,
        PRIMARY KEY (id)
        );
        """
        self.execute(sql, commit=True)

    def add_user(self, id: int, name: str):
        sql = "INSERT INTO Users(id, name) VALUES (?, ?)"
        parameters = (id, name)
        self.execute(sql, parameters=parameters, commit=True)

    def delete_table_users(self):
        self.execute("DROP TABLE Users")

    def add_concert(self, user_id: int, artist: str, date: str, place: str):
        sql = "INSERT INTO Concerts(user_id, artist, date, place) VALUES (?, ?, ?, ?)"
        parameters = (user_id, artist, date, place)
        self.execute(sql, parameters=parameters, commit=True)

    def find_player_stats(self, player_id, opponent_id):
        sql = "SELECT * FROM Stats WHERE player_id = ? AND opponent_id = ?"
        parameters = (player_id, opponent_id)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def find_user_by_id(self, user_id):
        sql = "SELECT * FROM Users WHERE id = ?"
        parameters = (user_id,)
        return self.execute(sql, parameters=parameters, fetchone=True)

    def create_player_stats(self, player_id, opponent_id, total_games, wins, losses, draws, total_points):
        sql = "INSERT INTO Stats(player_id, opponent_id, total_games, wins, losses, draws, total_points) " \
              "VALUES (?,?, ?, ?, ?, ?, ?)"
        parameters = (player_id, opponent_id, total_games, wins, losses, draws, total_points)
        return self.execute(sql, parameters=parameters, commit=True)

    def update_player_stats(self, total_games, wins, losses, draws, total_points, player_id, opponent_id):
        sql = "UPDATE Stats SET total_games = ?, wins = ?, losses = ?, draws = ?, total_points = ? " \
              "WHERE player_id = ? AND opponent_id = ?"
        parameters = (total_games, wins, losses, draws, total_points, player_id, opponent_id)
        self.execute(sql, parameters=parameters, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND".join([
            f"{item} = ?" for item in parameters
        ])
        return sql, tuple(parameters.values())


def logger(statement):
    print(f"Executing: {statement}")
