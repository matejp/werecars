# -*- coding: utf-8 -*-
"""
HTTP in WebSocket strežnik za igro Werecars.
"""
import os
import sys
import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import time
import pprint
from datetime import datetime
from werecars_world.Server import Server
from werecars_world import Log

# ==========================
# = Globalne spremenljivke =
# ==========================
# = števec povezav =
_counter = 0
_lock = threading.Lock()

# =====================
# = Logika igre =
# =====================
_game_level = 'werecars_world/levels/mini.level'
if len(sys.argv) == 2:
    if os.path.exists(sys.argv[1]):
        _game_level = sys.argv[1]
    else:
        print 'Datoteka ' + sys.argv[1] + ' ne obstaja.'
        sys.exit(1)
        
_server = Server(_game_level)

# ====================
# = Pomožne funkcije =
# ====================
def get_id():
    """Vrne unikatno številko"""
    global _counter, _lock
    
    _lock.acquire()
    try:
        id = _counter
        print threading.current_thread(), _counter
        _counter = _counter+1
    finally:
        _lock.release()
    
    return id
    
# =============================================
# = Werecars http in websocket server za igro =
# =============================================
class HttpHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/index.html')
        
class WerecarsWebsocket(tornado.websocket.WebSocketHandler):
    """Websocket strežnik za prenos podatkov o stanju igralcev v igri"""
    def open(self):
        global _server
        Log.log('on_open', 'websocket opened');
        # doda novega igralca na seznam igralcev
        id = get_id()
        _server.addClient(id, self)

    def on_message(self, message):
        global _server
        Log.log('on_message', message)
        
        py_message = json.loads(message) # dekodira json
        Log.log('py_message', py_message);
        Log.log('py_message event', ('client-message', py_message['id'], py_message['type'], py_message['data']));
        # doda dogodek v vrsto dogodkov
        _server.addEvent(('client-message', py_message['id'], (py_message['type'], py_message['data'])))

    def on_close(self):
        _server.removeClient(self)
        Log.log('on_close', 'websocket closed');

# ====================================================================
# = Funkcija pošilja podatke o igralcih ob določenem intervalu =
# ====================================================================
def game_server_run():
   global _server
   _server.run()

settings = {
    'auto_reload': True,
}

application = tornado.web.Application([
    (r'/', HttpHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": os.getcwd()+'/static'}),
    (r'/werecars-ws', WerecarsWebsocket),
], **settings)

if __name__ == "__main__":
    print "Strežnik posluša na vratih 8888\n"
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    
    interval_ms = 100 # milisekunde
    main_loop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(game_server_run, interval_ms, io_loop = main_loop)

    # zažene periodično izvajanje funkcije game_server_run
    scheduler.start()

    # zažene glavno izvajalno zanko
    main_loop.start()