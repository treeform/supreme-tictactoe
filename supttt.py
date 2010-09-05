import tornado.httpserver
import tornado.ioloop
import tornado.web
from jinja2 import Template

class MainHandler(tornado.web.RequestHandler):
    
    def get(self):
        BOARD = Template(open('templates/board.html').read())
        self.write(BOARD.render(world="tic tac toe"))

class StyleCSS(tornado.web.RequestHandler):
    
    def get(self):
        self.set_header("Content-Type", "text/css")
        STYLE = open('data/style.css').read()
        self.write(STYLE)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/style.css", StyleCSS),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
