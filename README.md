# Tic-tac-toe game

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting your local server's address (by default localhost:8080.)
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
 
##Game Description:
Tic-Tac-Toe is a simple two player game. Game instructions are available
[here](https://en.wikipedia.org/wiki/Tic-tac-toe). Games can also be created
to use board with size up to 100x100.

The board is represented as a 1-D list of squares with indexes as follows:
[0, 1, 2
 3, 4, 5
 6, 7, 8]

Indexes on bigger boards will follow the pattern. For example below is 5x5 board:

[0, 1, 2, 3, 4
 5, 6, 7, 8, 9
 10, 11, 12, 13, 14
 15, 16, 17, 18, 19
 20, 21, 22, 23, 24]


##Game example:
In the example we have following situation on the board:
| X | O | X
| O | X |
| O |   |

Next move is on user_x which let's say name is Mouse. He can make move to
positions with following indexes: 5, 7, 8. By making his move on index 8 he
will win the game. So calling make_move endpoint with user_name Mouse and
move 8 will result in winning him the game.


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - form.py: Messages definitions.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity definitions and their helpful functions.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
