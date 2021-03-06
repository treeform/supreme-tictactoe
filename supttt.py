
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from jinja2 import Template
import random
import time
import os

settings = {
    "static_path": os.path.join(os.path.dirname(__file__),"static")
}

# this is out in serverlet db                    
# its ok to keep it here because we never store the boards
# its just a temparery thing
BOARDS = {}

# when to time out players and sessions
TIME_OUT = 30

# winning rows
WINNING_ROWS = [
    # vertical
    [(0,0),(0,1),(0,2)],[(1,0),(1,1),(1,2)],[(2,0),(2,1),(2,2)], 
    # horizontal
    [(0,0),(1,0),(2,0)],[(0,1),(1,1),(2,1)],[(0,2),(1,2),(2,2)], 
    # diagonal
    [(0,0),(1,1),(2,2)],[(0,2),(1,1),(2,0)]]     



def read(file):
    """ get the whole file and cloes it"""
    with open(file) as file:
        return file.read()

# laod the templates and file we will need        
BOARD = Template(read('templates/board.html'))

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
        self.player1time = time.time()
        self.player2time = None
        self.ping_time = None
        
    def mark(self,x,y,mark):  
        """ 
            places a mark, if mark is invalid nothing happens 
        """
        # update times
        if mark == "X": self.player1time = time.time()
        if mark == "O": self.player2time = time.time()

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
        return True

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

class MainHandler(tornado.web.RequestHandler):
    """
        handles the loading of the main board
    """    
    def get(self):
        BOARD = Template(read('templates/board.html'))
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
            
        print "picking", id, x,y
        
        # make the mark    
        if board.mark(x,y,mark):
            if mark == "X": 
                print "X has moved, sending message to O"
                board.player2callback()                
            if mark == "O": 
                print "O has moved, sending message to X"
                board.player1callback()
                
        print "updaing",mark, "board"                
        on_response(self, board, id)

class StatusHandler(tornado.web.RequestHandler):
    """
        player pings this thing every 1 second to 
        get state of the board
    """
    @tornado.web.asynchronous
    def get(self):
        
        """
        # clean up unused boards
        for board in list(BOARDS.values()):
            if time.time() - board.ping_time > TIME_OUT:
                if board.player1id in BOARDS: del BOARDS[board.player1id]
                if board.player2id in BOARDS: del BOARDS[board.player2id]
                print "cleard board", board.player1id
        """
                
        self.set_header("Content-Type", "text/json")
        
        id = self.get_argument("id")
        
        print id, "get status!"
        
        if id not in BOARDS:
            # board not found look for open board
            for board in BOARDS.itervalues():
                if not board.player2id:
                    BOARDS[id] = board
                    board.player2id = id
                    board.player1time = time.time()
                    board.player2time = time.time()
                    print "player",id,"joined",board.player1id
                    print "calling player 1"
                    board.player1callback()
                    print "player 2 waits"
                    board.player2callback = self.async_callback(
                        on_response, self, board, id)
                    return
            else:
                # no open board found lets create new one
                board = Board(id)
                BOARDS[id] = board
                print "created new board", id
                print "player 1 waits"
                board.player1callback = self.async_callback(
                    on_response, self, board, id)
                return
        
        
        board = BOARDS[id]
        if id == board.player1id: 
            print "player 1 asks to wait for 2"
            board.player1callback = self.async_callback(
                on_response, self, board, id)
        else: 
            print "player 2 asks to wait for 1"
            board.player2callback = self.async_callback(
                on_response, self, board, id)
            
def on_response(handler, board, id):
    json = {}

    print "on_response", id
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
                
        # check for time out
        if time.time() - board.player1time > TIME_OUT:
            board.finished = "X player left!"

        if time.time() - board.player2time > TIME_OUT:
            board.finished = "O player left!"
    else:        
        json["message"] = "waiting for some one to connect... "

    # get information about our board                         
    json["grid"] = board.grid
    json["finished"] = board.finished

    handler.write(json_encode(json))    
    handler.finish()
 
application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/pick.json", PickHandler),
    (r"/status.json", StatusHandler),
], **settings)

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    
