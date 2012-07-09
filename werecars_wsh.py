import sys
sys.path.append("/Users/matej/Documents/Faks/Diploma/werecars/nova_scena/ws_server")
import json
from mod_pywebsocket import msgutil
from datetime import datetime
import time
import threading

from werecars_world.Server import Server
from werecars_world import Log

_GOODBYE_MESSAGE = 'Goodbye'
_counter = 0
_lock = threading.Lock()

# =====================
# = Game logic server =
# =====================
_server = Server('/Users/matej/Documents/Faks/Diploma/werecars/nova_scena/ws_server/levels/werecars_world/mini.level')
# _server = Server('werecars_world/hypercube.level')
# _server = Server('werecars_world/jumpy.level')
# _server = Server('werecars_world/quake.level')

# =======================
# = Websocket functions =
# =======================
def web_socket_do_extra_handshake(request):
    pass  # Always accept.

def web_socket_transfer_data(request):
    global _counter, _lock, _server
    
    _lock.acquire()
    print threading.current_thread(), _counter
    _counter = _counter+1
    _lock.release()
    
    while True:
        line = msgutil.receive_message(request)
        Log.log('web_socket_transfer_data', line)
        
        if line == 'client-new':
            order = json.dumps({'type':'client-new', 'data': 'new client registered with id: %d' % 1})
            msgutil.send_message(request, order)
            Log.log('web_socket_transfer_data', order)
            
            order = json.dumps({'type':'levelcubes', 'data': _server.m_gridForClients})
            msgutil.send_message(request, order)
            Log.log('web_socket_transfer_data', order)
            
            order = json.dumps({'type':'start-position', 'data': _server.newClient()})
            msgutil.send_message(request, order)
            Log.log('web_socket_transfer_data', order)
            
        elif line == _GOODBYE_MESSAGE:
            return
        else:
            order = json.dumps({'type':'count', 'data': 'counter: %s, c = %s' % (_counter, line)})
            msgutil.send_message(request, order)
