import tornado.ioloop
import tornado.web
import tornado.websocket
import json
from logic import *
from model import *


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class QuizHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument('id', None)
        if id is None:
            quizzes = get_all_quizzes()
            self.write(json.dumps([quiz.to_json() for quiz in quizzes]))
        else:
            quiz = get_quiz(id)
            self.write(json.dumps(quiz.to_json()))


class LoginHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        username = data['username']
        player_id = get_player_id(username)
        if player_id:
            self.write({'p_id': player_id})
        else:
            self.write({'p_id': -1})


class SimpleWebSocket(tornado.websocket.WebSocketHandler):
    connections = set()
    pid = ''

    def open(self, p_id):
        self.connections.add(self)
        self.pid = p_id

    def on_message(self, message):
        msg = json.loads(message)
        print("incoming message: " + message)
        if 'type' in msg:  # 'type' always needs to be in an incoming message
            if msg['type'] == 'login':
                username = msg['user']
                player_id = get_player_id(username)
                self.pid = player_id if player_id is not None else -1  # -1 indicates login error
                auth_msg = json.dumps({'type': 'login',
                                       'p_id': self.pid})
                self.write_message(auth_msg)  # authentification message only to this one client
            elif msg['type'] == 'user_message':
                self.notify_clients(json.dumps(msg))
            elif msg['type'] == 'join_lobby':
                player_id = msg['p_id']
                quiz_id = msg['q_id']
                player = get_player(player_id)
                # TODO when quiz model implemented: quiz_id needs to be supplied
                LobbyPool.join_lobby(player, self, quiz_id)  # TODO when quiz model implemented: quiz_id as 3rd parameter
            elif msg['type'] == 'leave_lobby':
                player_id = msg['p_id']
                player = get_player(player_id)
                LobbyPool.leave_lobby(player)
            elif msg['type'] == 'answered_question':
                if all(key in msg for key in ('game_id', 'q_id', 'played_question')):  # we now also need game_id, q_id and played_question for answer signal
                    player_id = msg['p_id']
                    game_id = msg['game_id']
                    question_id = msg['q_id']
                    GamePool.get_game(game_id).update_scoreboard(player_id, msg['played_question']['score'])
                    GamePool.get_game(game_id).add_waiting_player(player_id)
                    if msg['played_question']['is_correct'] == False:
                        GamePool.get_game(game_id).get_jackpot().increase_payout_chance(1)
                        GamePool.get_game(game_id).get_jackpot().add_points(200)  # TODO make this generic to questions worth, need to send this with the msg
                    if msg['played_question']['is_correct'] == True and msg['played_question']['is_jackpot'] == True:
                        GamePool.get_game(game_id).get_jackpot().payed_out()
                    # TODO when PlayedQuestion Model exists: check if keys for pq exists, generate pq, add pq tp game
            else:
                print('Could not resolve "type" key: ' + msg['type'])

        else:
            print('Message Error, keys "type"  and/or "p_id" not supplied in incoming message')

    def notify_clients(self, message):
        for client in self.connections:
            client.write_message(message)

    def on_close(self):
        self.connections.remove(self)
        print('connection to client ' + str(self.pid) + " closed by client")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/quizzes", QuizHandler),
        (r"/login", LoginHandler),
        (r"/websocket", SimpleWebSocket),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css/"},),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "./img/"},),
        (r"/websocket/p_id/(.*)", SimpleWebSocket)
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
