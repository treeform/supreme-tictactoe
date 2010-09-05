import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from jinja2 import Template
import random

# this is out in serverlet db                    
# its ok to keep it here because we never store the boards
# its just a temparery thing
BOARDS = {}

# winning rows
WINNING_ROWS = [
    # vertical
    [(0,0),(0,1),(0,2)],[(1,0),(1,1),(1,2)],[(2,0),(2,1),(2,2)], 
    # horizontal
    [(0,0),(1,0),(2,0)],[(0,1),(1,1),(2,1)],[(0,2),(1,2),(2,2)], 
    # diagonal
    [(0,0),(1,1),(2,2)],[(0,2),(1,1),(2,0)]]     

# laod the templates and file we will need
BOARD = Template(read('templates/board.html'))
STYLE = read('data/style.css')

class Board:
    """
        board class 
        * does the grid and move keeping
        * player ids
        * player timeouts
        * winning/draw checks
    """
    def __init__(self, id):
        """ 
            create the board 
        """
        self.grid = [[" "]*3 for i in range(3)]
        self.move = 0
        self.finished = None
        # players are tied to the board via id's
        self.player1id = id
        self.player2id = None
        # if players stop responding the board is closed
        self.player1time = None
        self.player2time = None
        
    def mark(self,x,y,mark):  
        """ 
            places a mark, if mark is invalid nothing happens 
        """
        # dont allow out of turn moves
        if self.move == 0 and mark != "X": return
        if self.move == 1 and mark != "O": return
        # dont allow players to overwrite moves        
        if self.grid[x][y] != " ": return
        # makr the move  
        self.grid[x][y] = mark
        # setup next move    
        self.move = (self.move + 1) % 2
        self.finished = self.check()

    def check(self):
        """
            checks for win or draw
        """
        for side in "X","O":
            for row in WINNING_ROWS:
                for x,y in row:
                    if self.grid[x][y] != side:
                        break;
                else:
                    # mark the rows
                    for x,y in row:
                        self.grid[x][y] += "*"
                    return side + " won!"
        # check for draw                           
        for x in range(3):
            for y in range(3):  
                 if self.grid[x][y] == " ":
                        return None
        # no empty space its a draw                        
        return "draw!"

def read(file):
    """ get the whole file and cloes it"""
    with open(file) as file:
        return file.read()

class MainHandler(tornado.web.RequestHandler):
    """
        handles the loading of the main board
    """    
    def get(self):
        self.write(BOARD.render(id=random.randint(0,100000)))

class PickHandler(tornado.web.RequestHandler):
    """
        handles a player picking where to place X or O
    """
    def get(self):
        self.set_header("Content-Type", "text/json")
        id = self.get_argument("id")
        if id not in BOARDS: return
        # board found
        board = BOARDS[id]    
        # get the cordinates 
        xy = self.get_argument("xy")
        x,y = int(xy[0]),int(xy[1])
        # which player/which marl
        if id == board.player1id: 
            mark = "X"
        else: 
            mark = "O"
        # make the mark    
        board.mark(x,y,mark)    

class StatusHandler(tornado.web.RequestHandler):
    """
        player pings this thing every 1 second to 
        get state of the board
    """
    def get(self):
        self.set_header("Content-Type", "text/json")
        
        json = {}
        
        id = self.get_argument("id")
        if id not in BOARDS:
            # board not found look for open board
            for board in BOARDS.itervalues():
                if not board.player2id:
                    BOARDS[id] = board
                    board.player2id = id
                    print "player",id,"joined",board.player1id
                    break
            else:
                # no open board found lets create new one
                BOARDS[id] = Board(id)
                print "created new board",id

        # get information about our board                
        board = BOARDS[id]
        json["grid"] = board.grid
        json["finished"] = board.finished

        # get baord messages
        if board.player2id:
            if board.move == 0 and board.player1id == id:
                json["message"] = "X: your move!"
            elif board.move == 1 and board.player2id == id:
                json["message"] = "O: your move!"
            else:
                if board.player1id == id:
                    json["message"] = "waiting for O to move!"
                else:
                    json["message"] = "waiting for X to move!"
        else:        
            json["message"] = "waiting for some one to connect... "
            
        self.write(json_encode(json))    

class StyleCSS(tornado.web.RequestHandler):
    """ 
        gets hardwired css style
    """
    def get(self):
        self.set_header("Content-Type", "text/css")
        self.write(STYLE)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/pick.json", PickHandler),
    (r"/status.json", StatusHandler),
    (r"/style.css", StyleCSS),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    
