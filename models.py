from datetime import date
from google.appengine.ext import ndb
from form import UserForm, GameForm, ScoreForm


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    wins = ndb.IntegerProperty(default=0)
    ties = ndb.IntegerProperty(default=0)
    total_played = ndb.IntegerProperty(default=0)

    @property
    def points(self):
        """User points"""
        return self.wins*3+self.ties

    @property
    def win_percentage(self):
        """User win percentage"""
        if self.total_played > 0:
            return float(self.wins) / float(self.total_played)
        else:
            return 0

    @property
    def not_lose_percentage(self):
        """User win plus tie percentage"""
        if self.total_played > 0:
            return (float(self.wins) + float(self.ties)) / float(
                self.total_played)

    def to_form(self):
        return UserForm(name=self.name,
                        email=self.email,
                        wins=self.wins,
                        ties=self.ties,
                        total_played=self.total_played,
                        not_lose_percentage=self.not_lose_percentage,
                        points=self.points)

    @classmethod
    def get_user_by_name(cls, username):
        """Gets User by his name. Return None on no User found"""
        return User.query(User.name == username).get()

    def update_stats(self):
        """Adds game to user and update."""
        self.total_played += 1
        self.put()

    def add_win(self):
        """Add a win"""
        self.wins += 1
        self.update_stats()

    def add_tie(self):
        """Add a tie"""
        self.ties += 1
        self.update_stats()

    def add_loss(self):
        """Add a loss. Used as additional method for extensibility."""
        self.update_stats()


class Game(ndb.Model):
    """Game object"""
    board = ndb.PickleProperty(required=True)
    board_size = ndb.IntegerProperty(required=True, default=3)
    next_move = ndb.KeyProperty(required=True)  # The User whose turn it is
    user_x = ndb.KeyProperty(required=True, kind='User')
    user_o = ndb.KeyProperty(required=True, kind='User')
    game_over = ndb.BooleanProperty(required=True, default=False)
    winner = ndb.KeyProperty()
    tie = ndb.BooleanProperty(default=False)
    history = ndb.PickleProperty(required=True)

    @classmethod
    def new_game(cls, user_x, user_o, board_size=3):
        """Creates and returns a new game"""
        game = Game(user_x=user_x,
                    user_o=user_o,
                    next_move=user_x)
        game.board = ['' for _ in range(board_size*board_size)]
        game.history = []
        game.board_size = board_size
        game.put()
        return game

    def to_form(self):
        """Returns a GameForm representation of the Game"""
        form = GameForm(urlsafe_key=self.key.urlsafe(),
                        board=str(self.board),
                        board_size=self.board_size,
                        user_x=self.user_x.get().name,
                        user_o=self.user_o.get().name,
                        next_move=self.next_move.get().name,
                        game_over=self.game_over,
                        )
        if self.winner:
            form.winner = self.winner.get().name
        if self.tie:
            form.tie = self.tie
        return form

    def end_game(self, winner=None):
        """Ends the game"""
        self.game_over = True
        if winner:
            self.winner = winner
        else:
            self.tie = True
        self.put()
        if winner:
            result = 'user_x' if winner == self.user_x else 'user_o'
        else:
            result = 'tie'
        # Add the game to the score 'board'
        score = Score(date=date.today(), user_x=self.user_x,
                      user_o=self.user_o, result=result)
        score.put()

        # Update the user models
        if winner:
            winner.get().add_win()
            loser = self.user_x if winner == self.user_o else self.user_o
            loser.get().add_loss()
        else:
            self.user_x.get().add_tie()
            self.user_o.get().add_tie()


class Score(ndb.Model):
    """Score object"""
    date = ndb.DateProperty(required=True)
    user_x = ndb.KeyProperty(required=True)
    user_o = ndb.KeyProperty(required=True)
    result = ndb.StringProperty(required=True)

    def to_form(self):
        return ScoreForm(date=str(self.date),
                         user_x=self.user_x.get().name,
                         user_o=self.user_o.get().name,
                         result=self.result)
