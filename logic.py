import json
from model import *
from main import SimpleWebSocket


class Lobby:
    def __init__(self, first_player, socket):
        print('Created new Lobby')
        self.players = []
        self.socket = socket
        self.add_player(first_player)

    def get_players(self):
        return self.players

    def set_players(self, players):
        self.players = players

    def add_player(self, player):
        print('Added Player ' + str(player.get_id()) + ' to lobby')
        self.players.append(player)
        if self.has_required_players():
            self.open_game()
        else:
            self.send_lobby_state_to_players()

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            print('removed player ' + str(player.get_id()) + ' from lobby')
            self.send_lobby_state_to_players()

    def has_required_players(self):
        return len(self.players) >= 2  # TODO when quiz model implemented: make this value generic

    def send_lobby_state_to_players(self):
        msg = json.dumps({'type':'lobby',
                          'lobby': [player.get_id() for player in self.players],
                          'nicks': [player.get_nickname() for player in self.players]})

        self.notify_players(msg)

    def open_game(self):
        print('opening game for ' + str(len(self.players)) + ' players')
        game_id = GamePool.start_game(self.players, self.socket)
        self.close_lobby()

    def close_lobby(self):
        for id, lobby in list(LobbyPool.lobbies.items()):
            if lobby == self:
                del LobbyPool.lobbies[id]
                print("closed lobby")

    def notify_players(self, message):
        self.socket.notify_clients(message)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.get_players() == other.get_players()
        return False

    def __ne__(self, other):
        return self.get_players() != other.get_players()


class LobbyPool:
    lobbies = {}

    @staticmethod
    def join_lobby(player, socket, quiz_id=1):  # TODO update quiz_id when quiz model exists, for now leave this as 1!
        if quiz_id not in LobbyPool.lobbies:
            lobby = Lobby(player, socket)
            LobbyPool.lobbies[quiz_id] = lobby
        else:
            LobbyPool.lobbies[quiz_id].add_player(player)
        return quiz_id

    @staticmethod
    def get_lobby(quiz_id=1):
        return LobbyPool.lobbies[quiz_id]

    @staticmethod
    def leave_lobby(player, quiz_id=1):
        if LobbyPool.lobbies[quiz_id]:
            LobbyPool.lobbies[quiz_id].remove_player(player)
            if not LobbyPool.lobbies[quiz_id].get_players():
                del LobbyPool.lobbies[quiz_id]


class GamePool:
    games = {}

    @staticmethod
    def start_game(players, socket):
        for id in range(0, 1000):
            if id not in GamePool.games:
                game = Game(id, players, socket)
                GamePool.games[id] = game
                GamePool.games[id].start()
                break
        return id

    @staticmethod
    def get_game(game_id):
        return GamePool.games[game_id] if game_id in GamePool.games else None

    @staticmethod
    def remove_game(game_id):
        if game_id in GamePool.games:
            del GamePool.games[game_id]


class Game:
    def __init__(self, id, players, socket):
        self.id = id
        self.players = players
        self.waiting_players = set()

        self.played_questions = 0
        self.jackpot = None  # TODO = Jackpot()
        self.player_ids = [player.get_id() for player in players]
        self.socket = socket
        self.scoreboard = {}
        for player_id in self.player_ids:
            self.scoreboard[player_id] = 0
        self.questions = []
        for i in range(1, 5):
            question = get_question(i)
            if question is not None:
                self.questions.append(question)

    def get_id(self):
        return self.id

    def get_players(self):
        return self.players

    def get_waiting_players(self):
        return self.waiting_players

    def add_waiting_player(self, player_id):
        self.waiting_players.add(player_id)
        self.check_for_next_question()

    def check_for_next_question(self):
        if self.all_players_answered():
            self.waiting_players.clear()
            self.start_next_question()

    def get_played_questions_amount(self):
        return self.played_questions

    def get_scoreboard(self):
        return self.scoreboard

    def start(self):
        msg = json.dumps({'type': 'game_start',
                          'game_id': self.id})
        self.notify_players(msg)
        self.start_round()

    def start_round(self):
        self.start_next_question()

    def get_questions(self):
        return self.questions

    def get_questions_json(self):
        return [question.to_json() for question in self.questions]

    def start_next_question(self):
        end_flag = False
        if self.played_questions == len(self.questions):
            self.end()
            end_flag = True
        if not end_flag:
            next_question = self.questions[self.played_questions].to_json()
            msg = json.dumps({'type': 'question',
                   'question': next_question})
            self.notify_players(msg)
        self.played_questions += 1

    def end(self):
        self.save_end_results()
        self.send_end_results()

    def send_end_results(self):
        msg = json.dumps({'type': 'scoreboard',
                          'scoreboard': self.scoreboard})
        self.notify_players(msg)

    def save_end_results(self):
        # TODO
        pass

    def update_scoreboard(self, player_id, score):
        if player_id in self.scoreboard:
            self.scoreboard[player_id] += score

    def all_players_answered(self):
        return len(self.waiting_players) == len(self.players)

    def notify_players(self, message):
        self.socket.notify_clients(message)
