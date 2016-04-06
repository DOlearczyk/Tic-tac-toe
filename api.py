import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache, mail
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from models import User, Game, Score
from form import StringMessage, NewGameForm, GameForm, MakeMoveForm, \
    ScoreForms, GameForms, UserForm, UserForms
from utils import get_by_urlsafe, check_winner, check_full

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1), )
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_GAMES_PLAYED = 'GAMES_PLAYED'


@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeAPI(remote.Service):
    """Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.get_user_by_name(request.user_name):
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        if not mail.is_email_valid(request.email):
            raise endpoints.BadRequestException(
                'Bad email address!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(response_message=UserForms,
                      path='user/ranking',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return all Users ranked by their not lose percentage"""
        users = User.query(User.total_played > 0).fetch()
        users = sorted(users, key=lambda x: x.points,
                       reverse=True)
        return UserForms(items=[user.to_form() for user in users])

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user_x = User.get_user_by_name(request.user_x)
        user_o = User.get_user_by_name(request.user_o)
        # Check if users exist
        if not (user_x and user_o):
            wrong_user = user_x if not user_x else user_o
            raise endpoints.NotFoundException(
                'User %s does not exist!' % wrong_user.name)
        # Check if board size is valid. It should be within 3-100 range.
        board_size = 3
        if request.board_size:
            if request.board_size < 3 or request.board_size > 100:
                raise endpoints.BadRequestException(
                    'Invalid board size! Must be between'
                    ' 3 and 100')
            board_size = request.board_size
        game = Game.new_game(user_x.key, user_o.key, board_size)

        return game.to_form()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='user/games',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all User's active games"""
        user = User.get_user_by_name(request.user_name)
        if not user:
            raise endpoints.BadRequestException('User not found!')
        games = Game.query(ndb.OR(Game.user_x == user.key,
                                  Game.user_o == user.key)). \
            filter(Game.game_over == False)
        return GameForms(items=[game.to_form() for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Delete a game. Game must not have ended to be deleted"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and not game.game_over:
            game.key.delete()
            return StringMessage(message='Game with key: {} deleted.'.
                                 format(request.urlsafe_game_key))
        elif game and game.game_over:
            raise endpoints.BadRequestException('Game is already over!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')

        user = User.get_user_by_name(request.user_name)
        if user.key != game.next_move:
            raise endpoints.BadRequestException('It\'s not your turn!')

        # Just a dummy signifier, what type of symbol is going down
        x = True if user.key == game.user_x else False

        move = request.move
        # Verify move is valid
        size = game.board_size * game.board_size - 1
        if move < 0 or move > size:
            raise endpoints.BadRequestException('Invalid move! Must be between'
                                                '0 and %s ')
        if game.board[move] != '':
            raise endpoints.BadRequestException('Invalid move!')

        game.board[move] = 'X' if x else 'O'
        # Append a move to the history
        game.history.append(('X' if x else 'O', move))
        game.next_move = game.user_o if x else game.user_x
        # Check if there's a winner
        winner = check_winner(game.board, game.board_size)
        # If there's winner end game
        if winner:
            game.end_game(user.key)
        else:
            # If there's no winner and game board is full end game with tie
            if check_full(game.board):
                # Game tied
                game.end_game()
            else:
                # If game is still ongoing, send remainder email to player
                taskqueue.add(url='/tasks/send_move_email',
                              params={'user_key': game.next_move.urlsafe(),
                                      'game_key': game.key.urlsafe()})
        game.put()
        # If game is over, update memcache
        if game.game_over:
            taskqueue.add(url='/tasks/update_finished_games')
        return game.to_form()

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a Game's move history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        return StringMessage(message=str(game.history))

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.get_user_by_name(request.user_name)
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(ndb.OR(Score.user_x == user.key,
                                    Score.user_o == user.key))
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/finished_games',
                      name='get_finished_games',
                      http_method='GET')
    def get_finished_games(self, request):
        """Get the cached number of games finished"""
        return StringMessage(
            message=memcache.get(MEMCACHE_GAMES_PLAYED) or '')

    @staticmethod
    def _update_finished_games():
        """Populates memcache with the number of games finished"""
        games = Game.query(Game.game_over == True).fetch()
        if games:
            count = len(games)
            memcache.set(MEMCACHE_GAMES_PLAYED,
                         'The games finished number is %s' % count)


api = endpoints.api_server([TicTacToeAPI])
