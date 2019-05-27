# -*- coding: utf-8 -*-
import json


class Answer:
    def __init__(self, content=None, type=False):
        self.content = content
        self.type = type
        self.aid = None

    def get_id(self):
        return self.aid

    def set_id(self, aid):
        self.aid = aid

    def get_content(self):
        return self.content

    def get_type(self):
        return self.type

    def __str__(self):
        return 'ID: ' + str(self.aid) + ' Content: ' + self.content + ' Type: ' + str(self.type)


class Question:
    def __init__(self, questioning=None, topic=None, answers=None, dynamic_difficulty=None, static_difficulty=None, response_time=None, worth=None):
        self.questioning = questioning
        self.topic = topic
        self.answers = answers
        self.dynamic_difficulty = dynamic_difficulty
        self.static_difficulty = static_difficulty
        self.response_time = response_time
        self.worth = worth
        self.qid = get_question_id(questioning)
        if self.qid is None:
            store_question(self)
            self.qid = get_question_id(questioning)


    def get_id(self):
        return self.qid

    def set_id(self, qid):
        self.qid = qid

    def get_questioning(self):
        return self.questioning

    def get_topic(self):
        return self.topic

    def get_answers(self):
        return self.answers

    def get_dynamic_difficulty(self):
        return self.dynamic_difficulty

    def get_static_difficulty(self):
        return self.static_difficulty

    def get_response_time(self):
        return self.response_time

    def get_worth(self):
        return self.worth

    def get_quiz(self):
        return self.quiz

    def set_quiz(self, quiz):
        self.quiz = quiz

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.qid == other.get_id()
        return False

    def __ne__(self, other):
        return self.qid != other.get_id()

    def to_json(self):
        """
        converts question obj to dict, but does not yet dump it to json string because socket dumps it later itself
        """
        return {'answers': [
                            {'id': 1,
                             'content': self.get_answers()[0].get_content(),
                             'type': self.get_answers()[0].get_type()
                            },
                            {'id': 2,
                             'content': self.get_answers()[1].get_content(),
                             'type': self.get_answers()[1].get_type()
                            },
                            {'id': 3,
                             'content': self.get_answers()[2].get_content(),
                             'type': self.get_answers()[2].get_type()
                            },
                            {'id': 4,
                             'content': self.get_answers()[3].get_content(),
                             'type': self.get_answers()[3].get_type()
                            },
                          ],
                        'dynamicDifficulty': self.get_dynamic_difficulty(),
                        'staticDifficulty': self.get_static_difficulty(),
                        'id': self.get_id(),
                        'questioning': self.get_questioning(),
                        'responseTime': self.get_response_time(),
                        'topic': self.get_topic(),
                        'worth': self.get_worth()}

    def __str__(self):
        return 'ID: ' + str(self.qid) + ' Questioning: ' + self.questioning + \
               ' Answers: ' + str([str(answer) for answer in self.answers]) + \
               ' dynamic diff: ' + str(self.dynamic_difficulty) + ' static Diff: ' + str(self.static_difficulty) + \
               ' Response Time: ' + str(self.response_time) + ' Worth: ' + str(self.worth)


class Player:
    def __init__(self, mail=None, nickname=None, password=None):
        self.mail = mail
        self.nickname = nickname
        self.password = password
        self.pid = get_player_id(nickname)
        if self.pid is None:
            store_player(self)
            self.pid = get_player_id(nickname)

    def get_id(self):
        return self.pid

    def set_id(self, pid):
        """
        do not call manually to avoid storage conflicts because ids are system generated
        :param pid:
        :return:
        """
        self.pid = pid

    def get_nickname(self):
        return self.nickname

    def get_mail(self):
        return self.mail

    def get_password(self):
        return self.password

    def __str__(self):
        return 'ID: ' + str(self.pid) + ' Nickname: ' + self.nickname + ' Mail: ' + self.mail + ' Password: ' + self.password

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.pid == other.get_id()
        return False

    def __ne__(self, other):
        return self.pid != other.get_id()


class Quiz:
    def __init__(self, title=None, length=None, min_participants=None):
        self.title = title
        self.length = length
        self.min_participants = min_participants
        self.id = get_quiz_id(title)
        if self.id is None:
            store_quiz(self)
            self.id = get_quiz_id(title)
        self.questions = get_questions_of_quiz(self)

    def get_random_questions(self):
        # for now just use the first |length| questions
        # TODO implement randomly choosing algorithm with consideration of preffering often wrongly answered Questions
        # (needs data from saved games to work though)
        return [self.questions[i] for i in range(self.length + 1)]

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id

    def get_title(self):
        return self.title

    def get_length(self):
        return self.length

    def get_min_participants(self):
        return self.min_participants

    def get_questions(self):
        return self.questions

    def add_question(self, question):
        if question not in self.questions:
            self.questions.append(question)

    def to_json(self):
        return {'title': self.title,
                'length': self.length,
                'min_participants': self.min_participants,
                'id': self.id}


def get_player(id, json_path="players.json"):
    with open(json_path) as f:
        data = json.load(f)
        if int(id) > int(data['highest_id']):
            print('player will be none because id too high')
            return None
        else:
            for player in data['players']:
                if player['id'] == int(id):
                    instance = Player(player['mail'], player['nickname'], player['password'])
                    instance.set_id(player['id'])
                    return instance
            print('player will be none because not found')
            return None


def get_question(id, json_path='questions.json'):
    with open(json_path) as f:
        data = json.load(f)
        if int(id) > int(data['highest_id']):
            return None
        else:
            for question in data['questions']:
                if question['id'] == id:
                    answers = []
                    for answer in question['answers']:
                        answer_instance = Answer(answer['content'], answer['type'])
                        answer_instance.set_id(answer['id'])
                        answers.append(answer_instance)
                    instance = Question(question['questioning'], question['topic'], answers,
                                        question['dynamicDifficulty'], question['staticDifficulty'],
                                        question['responseTime'], question['worth'])
                    instance.set_id(question['id'])
                    return instance
            return None


def get_questions_of_quiz(quiz, json_path='questions.json'):
    question_list = []
    with open(json_path) as f:
        data = json.load(f)
        for question in data['questions']:
            if question['topic'] == quiz.get_title():
                answers = []
                for answer in question['answers']:
                    answer_instance = Answer(answer['content'], answer['type'])
                    answer_instance.set_id(answer['id'])
                    answers.append(answer_instance)
                instance = Question(question['questioning'], question['topic'], answers,
                                    question['dynamicDifficulty'], question['staticDifficulty'],
                                    question['responseTime'], question['worth'])
                instance.set_id(question['id'])
                question_list.append(instance)
    return question_list


def get_quiz(id, json_path='quizzes.json'):
    with open(json_path) as f:
        data = json.load(f)
        if int(id) > int(data['highest_id']):
            return None
        else:
            for quiz in data['quizzes']:
                if quiz['id'] == int(id):
                    instance = Quiz(quiz['title'], quiz['length'], quiz['min_participants'])
                    instance.set_id(quiz['id'])
                    return instance
            return None

def get_all_quizzes(json_path='quizzes.json'):
    quizzes = []
    with open(json_path) as f:
        data = json.load(f)
        for quiz in data['quizzes']:
            instance = Quiz(quiz['title'], quiz['length'], quiz['min_participants'])
            instance.set_id(quiz['id'])
            quizzes.append(instance)
        return quizzes

def store_player(player, json_path='players.json'):
    '''
    stores/adds player to json file, increments highest_id field
    :param player: player to add
    :param json_path: path to json file
    :return: void
    '''
    with open(json_path, 'r') as f:
        data = json.load(f)
        new_id = data['highest_id'] + 1
        data['players'].append({'id': new_id,
                                'nickname': player.get_nickname(),
                                'password': player.get_password(),
                                'mail': player.get_mail()})
        data['highest_id'] = new_id
    with open(json_path, 'w') as f:
        print('stored player ID: ' + str(new_id) + ' to data')
        json.dump(data, f)


def store_question(question, json_path='questions.json'):
    with open(json_path) as f:
        data = json.load(f)
        new_id = data['highest_id'] + 1
        data['questions'].append({'answers': [
                                                {'id': 1,
                                                 'content': question.get_answers()[0].get_content(),
                                                 'type': question.get_answers()[0].get_type()
                                                },
                                                {'id': 2,
                                                 'content': question.get_answers()[1].get_content(),
                                                 'type': question.get_answers()[1].get_type()
                                                },
                                                {'id': 3,
                                                 'content': question.get_answers()[2].get_content(),
                                                 'type': question.get_answers()[2].get_type()
                                                },
                                                {'id': 4,
                                                 'content': question.get_answers()[3].get_content(),
                                                 'type': question.get_answers()[3].get_type()
                                                },
                                             ],
                                  'dynamicDifficulty': question.get_dynamic_difficulty(),
                                  'staticDifficulty': question.get_static_difficulty(),
                                  'id': new_id,
                                  'questioning': question.get_questioning(),
                                  'responseTime': question.get_response_time(),
                                  'topic': question.get_topic(),
                                  'worth': question.get_worth()})
        data['highest_id'] = new_id
    with open(json_path, 'w') as f:
        print('stored Question ID: ' + str(new_id) + ' to data')
        json.dump(data, f)


def store_quiz(quiz, json_path='quizzes.json'):
    with open(json_path) as f:
        data = json.load(f)
        new_id = data['highest_id'] + 1
        data['quizzes'].append({'id': new_id,
                                'title': quiz.get_title(),
                                'length': quiz.get_length(),
                                'min_participants': quiz.get_min_participants()
                                })
        data['highest_id'] = new_id
    with open(json_path, 'w') as f:
        print('stored Quiz ID: ' + str(new_id) + ' to data')
        json.dump(data, f)


def get_player_id(nickname, json_path='players.json'):
    '''
    get the id of a player by nickname
    :param nickname: nickname to search for
    :param json_path: path to json file
    :return: id if player is present, else None
    '''
    with open(json_path) as f:
        data = json.load(f)
        for player in data['players']:
            if player['nickname'] == nickname:
                return player['id']
        return None


def get_question_id(questioning, json_path='questions.json'):
    with open(json_path) as f:
        data = json.load(f)
        for question in data['questions']:
            if question['questioning'] == questioning:
                return question['id']
        return None


def get_quiz_id(title, json_path='quizzes.json'):
    with open(json_path) as f:
        data = json.load(f)
        for quiz in data['quizzes']:
            if quiz['title'] == title:
                return quiz['id']
        return None
