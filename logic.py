# -*- coding: utf-8 -*-
import json
import random
from model import *


class Lobby:
    def __init__(self, quiz, first_player, socket):
        print('Created new Lobby')
        self.players = []
        self.socket = socket
        self.quiz = quiz
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
        return len(self.players) >= self.quiz.get_min_participants()  # TODO when quiz model implemented: make this value generic

    def send_lobby_state_to_players(self):
        msg = json.dumps({'type': 'lobby',
                          'lobby': [player.get_id() for player in self.players],
                          'nicks': [player.get_nickname() for player in self.players]})

        self.notify_players(msg)

    def open_game(self):
        print('opening game for ' + str(len(self.players)) + ' players')
        GamePool.start_game(self.quiz, self.players, self.socket)
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
            quiz = get_quiz(quiz_id)
            lobby = Lobby(quiz, player, socket)
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
    def start_game(quiz, players, socket):
        for id in range(0, 1000):
            if id not in GamePool.games:
                game = Game(id, quiz, players, socket)
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
    def __init__(self, id, quiz, players, socket):
        self.id = id
        self.players = players
        self.quiz = quiz
        self.waiting_players = set()

        self.played_questions = 0
        self.jackpot = Jackpot()
        self.player_ids = [player.get_id() for player in players]
        self.socket = socket
        self.scoreboard = {}
        self.item_table = ItemTable()
        for player_id in self.player_ids:
            self.scoreboard[player_id] = 0
        self.questions = self.quiz.get_random_questions()

    def get_id(self):
        return self.id

    def get_players(self):
        return self.players

    def get_item_table(self):
        return self.item_table

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

    def get_jackpot(self):
        return self.jackpot

    def start_next_question(self):
        end_flag = False
        if self.played_questions == len(self.questions):
            self.end()
            end_flag = True
        elif self.played_questions == (len(self.questions) - 1):
            self.jackpot.set_active(True)
        else:
            self.jackpot.random_activation()

        if not end_flag:
            next_question = self.questions[self.played_questions].to_json()
            # assign an item to a random wrong answer
            rand_index = random.randint(1, len(next_question['answers']) - 1)
            next_question['answers'][rand_index]['assigned_effect'] = Item().get_effect()

            msg = json.dumps({'type': 'question',
                              'question': next_question,
                              'jackpot': {
                                            'amount': self.jackpot.get_amount(),
                                            'is_active': self.jackpot.get_is_active()},
                              'scoreboard': self.scoreboard
                              })
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


class Jackpot:
    def __init__(self):
        self.inital_points = 1000
        self.initial_payout_chance = 10
        self.amount = self.inital_points
        self.payout_chance = self.initial_payout_chance
        self.payout_counter = 0
        self.is_active = False

    def get_initial_points(self):
        return self.inital_points

    def get_amount(self):
        return self.amount

    def set_amount(self, amount):
        self.amount = amount

    def get_payout_counter(self):
        return self.payout_counter

    def get_is_active(self):
        return self.is_active

    def set_active(self, bool_active):
        self.is_active = bool_active

    def get_payout_chance(self):
        return self.payout_chance

    def fill(self):
        """
        called after payout, fills jackpot with initial points
        """
        self.amount = self.inital_points

    def clear(self):
        """
        empties the jackpot
        """
        self.is_active = False
        self.amount = 0

    def payed_out(self):
        """
        called after payout, resets payout chance and refills initial inital points
        """
        self.clear()
        self.fill()
        self.payout_chance = self.initial_payout_chance
        self.payout_counter += 1

    def increase_payout_chance(self, value):
        """
        increase payout chance by value
        :param value: value to increase payout chance
        """
        self.payout_chance += value

    def random_activation(self):
        """
        randomly determine the jackpot activation
        """
        payout_threshold = 100 - self.payout_chance
        random_int = random.randint(0, 100) + 1
        if random_int >= payout_threshold:
            self.is_active = True

    def add_points(self, points):
        self.amount += points


class Item:
    def __init__(self):
        self.possible_effects = ['scoreX2', 'scoreX5', 'score/2', 'shuffle_question', 'jackpot', 'bomb', 'move_answers', 'hide_scoreboard', 'get_points_save']  # further possibilites: jackpot next question, freeze other players,
        self.debug = ['move_answers']
        self.effect = random.choice(self.possible_effects)

    def get_effect(self):
        return self.effect


class ItemTable:
    def __init__(self):
        self.player_items = {}  # {item:{p_id1:quantity1,p_id2:quantity2,...},...}

    def get_player_items(self):
        return self.player_items

    def add_item(self, item, p_id):
        if item not in self.player_items:
            self.player_items[item] = {}
            self.player_items[item][p_id] = 1
        else:
            if p_id not in self.player_items[item]:
                self.player_items[item][p_id] = 1
            else:
                self.player_items[item][p_id] += 1

    def check_and_activate_item(self, item, p_id):
        if item not in self.player_items:
            return False
        else:
            if p_id not in self.player_items[item]:
                return False
            else:
                if self.player_items[item][p_id] > 0:
                    self.player_items[item][p_id] -= 1
                    return True

    def clean(self):
        for element in self.player_items:
            for k, v in self.player_items[element].items():
                if v <= 0:
                    del self.player_items[element][k]
            if not element:
                del self.player_items[element]
