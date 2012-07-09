"""
This is a simple example of WebSocket + Tornado + Redis Pub/Sub usage.
Do not forget to replace YOURSERVER by the correct value.
Keep in mind that you need the *very latest* version of your web browser.
You also need to add Jacob Kristhammar's websocket implementation to Tornado:
Grab it here:
    http://gist.github.com/526746
Or clone my fork of Tornado with websocket included:
    http://github.com/kizlum/tornado
Oh and the Pub/Sub protocol is only available in Redis 2.0.0:
    http://code.google.com/p/redis/downloads/detail?name=redis-2.0.0-rc4.tar.gz

Tested with Chrome 6.0.490.1 dev under OS X.

For questions / feedback / coffee -> @kizlum or thomas@pelletier.im.
Have fun.
"""
import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
# import redis


# This is ugly but I did not want to create multiple files for a so trivial
# example.
TEMPLATE = """
<!DOCTYPE>
<html>
<head>
    <title>Sample test</title>
    <script>
    var socket = null;

    var addressBox = null;
    var logBox = null;
    var messageBox = null;

    function addToLog(log) {
      logBox.value += log + '\\n'
      // Large enough to keep showing the latest message.
      logBox.scrollTop = 1000000;
    }

    function send() {
      socket.send(messageBox.value);
      addToLog('> ' + messageBox.value);
      messageBox.value = '';
    }

    function connect() {
      socket = new WebSocket(addressBox.value);

      socket.onopen = function () {
        addToLog('Opened');
      };
      socket.onmessage = function (event) {
        addToLog('< ' + event.data);
      };
      socket.onerror = function () {
        addToLog('Error');
      };
      socket.onclose = function (event) {
        var logMessage = 'Closed (';
        if ((arguments.length == 1) && ('CloseEvent' in window) &&
            (event instanceof CloseEvent)) {
          logMessage += 'wasClean = ' + event.wasClean;
          // code and reason are present only for
          // draft-ietf-hybi-thewebsocketprotocol-06 and later
          if ('code' in event) {
            logMessage += ', code = ' + event.code;
          }
          if ('reason' in event) {
            logMessage += ', reason = ' + event.reason;
          }
        } else {
          logMessage += 'CloseEvent is not available';
        }
        addToLog(logMessage + ')');
      };

      addToLog('Connect ' + addressBox.value);
    }

    function closeSocket() {
      socket.close();
    }

    function init() {
      var scheme = window.location.protocol == 'https:' ? 'wss://' : 'ws://';
      var defaultAddress = scheme + window.location.host + '/echo';

      addressBox = document.getElementById('address');
      logBox = document.getElementById('log');
      messageBox = document.getElementById('message');

      addressBox.value = defaultAddress;

      if (!('WebSocket' in window)) {
        addToLog('WebSocket is not available');
      }
    }
    </script>
</head>
<body onload="init()">

    <form action="#" onsubmit="connect(); return false;">
    <input type="text" id="address" size="40">
    <input type="submit" value="connect">
    <input type="button" value="close" onclick="closeSocket();">
    </form>

    <textarea id="log" rows="10" cols="40" readonly></textarea>

    <form action="#" onsubmit="send(); return false;">
    <input type="text" id="message" size="40">
    <input type="submit" value="send">
    </form>

</body>
</html>
"""
PLAYERS = []

class HttpHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(TEMPLATE)

    # def post(self):
    #     data = self.request.arguments['data'][0]
        # r = redis.Redis(host='localhost', db=2)
        # r.publish('test_realtime', data)

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        PLAYERS.append(self)
        print "open"

    def on_message(self, message):
        print "message"
        self.write_message(u"You said: " + message)

    def on_close(self):
        PLAYERS.remove(self)
        print "close"

settings = {
    'auto_reload': True,
}

application = tornado.web.Application([
    (r'/', HttpHandler),
    (r'/echo/?', EchoWebSocket),
], **settings)

def echo_tick():
    c = 0;
    for player in PLAYERS:
        player.write_message(unicode("Tick %d" % c))
        print "Tick %d" % c
        c += 1

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)

    #milliseconds 
    interval_ms = 1000 
    main_loop = tornado.ioloop.IOLoop.instance() 
    scheduler = tornado.ioloop.PeriodicCallback(echo_tick, interval_ms, io_loop = main_loop)

    #start your period timer 
    scheduler.start()

    #start your loop 
    main_loop.start()