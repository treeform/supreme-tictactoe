import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.escape import json_encode
from jinja2 import Template
import random

class Board:
    
    def __init__(self, id):
        self.grid = [[" "]*3 for i in range(3)]
        self.player1id = id
        self.player2id = None
        self.move = 0
        
    def mark(self,x,y,mark):        
        self.grid[x][y] = mark
        for r in self.grid:
            print " ".join(r)
        self.move = (self.move + 1) % 2
        
    def finished():
        return False

BOARDS = {}

class MainHandler(tornado.web.RequestHandler):
    
    def get(self):
        BOARD = Template(open('templates/board.html').read())
        self.write(BOARD.render(id=random.randint(0,100000)))

class PickHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.set_header("Content-Type", "text/json")
        id = self.get_argument("id")
        if id not in BOARDS: return
        board = BOARDS[id]    
         
        xy = self.get_argument("xy")
        x,y = int(xy[0]),int(xy[1])
        
        if id == board.player1id: 
            mark = "X"
        else: 
            mark = "O"
            
        board.mark(x,y,mark)    

class StatusHandler(tornado.web.RequestHandler):
    
    def get(self):
        self.set_header("Content-Type", "text/json")
        id = self.get_argument("id")
        json = {}
        
        if id not in BOARDS:
            for board in BOARDS.itervalues():
                if not board.player2id:
                    BOARDS[id] = board
                    board.player2id = id
                    print "player",id,"joined",board.player1id
                    break
            else:
                BOARDS[id] = Board(id)
                print "created new board",id
                
        board = BOARDS[id]

        json["grid"] = board.grid

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
            json["message"] = "waiting for some one to connect... "+str(board.player2id)
            
        self.write(json_encode(json))    

class StyleCSS(tornado.web.RequestHandler):
    
    def get(self):
        self.set_header("Content-Type", "text/css")
        STYLE = open('data/style.css').read()
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
    
