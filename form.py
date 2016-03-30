from protorpc import messages

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    board = messages.StringField(2, required=True)
    board_size = messages.IntegerField(3, required=True)
    user_x = messages.StringField(4, required=True)
    user_o = messages.StringField(5, required=True)
    next_move = messages.StringField(6, required=True)
    game_over = messages.BooleanField(7, required=True)
    winner = messages.StringField(8)
    tie = messages.BooleanField(9)


class GameForms(messages.Message):
    """Container for multiple GameForm"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_x = messages.StringField(1, required=True)
    user_o = messages.StringField(2, required=True)
    board_size = messages.IntegerField(3)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    user_name = messages.StringField(1, required=True)
    move = messages.IntegerField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    date = messages.StringField(1, required=True)
    user_x = messages.StringField(2, required=True)
    user_o = messages.StringField(3, required=True)
    result = messages.StringField(4)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)


class UserForm(messages.Message):
    """User Form"""
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    wins = messages.IntegerField(3, required=True)
    ties = messages.IntegerField(4, required=True)
    total_played = messages.IntegerField(5, required=True)
    not_lose_percentage = messages.FloatField(6, required=True)
    points = messages.IntegerField(7)


class UserForms(messages.Message):
    """Container for multiple User Forms"""
    items = messages.MessageField(UserForm, 1, repeated=True)