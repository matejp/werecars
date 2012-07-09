# -*- coding: utf-8 -*-
import sys
import select
import cPickle
import cStringIO
import time
import math
import json
from collections import deque
from werecars_world import Log
from werecars_world import Box

class Server:
    """
    Werecars strežnik: posluša za dogodke, ki jih pošiljajo igralci.
    Dogodke obdela in vrne stanje sveta.
    """
    
    def addEvent(self, event_obj):
        """Doda nov dogodek na seznam dogodkov."""
        # id = getClientId(websocket)
        
        self.events_queue.append(event_obj)
        event_num = 0
        for event in self.events_queue:
            Log.log("e-" + str(event_num), ": " + str(event))
            event_num += 1
        
    def addClient(self, id, websocket):
        """
        Doda websocket na seznam aktivnih websocket povezav in 
        doda nov client-new dogodek na seznam dogodkov.
        """
        self.m_clientsWS[id] = websocket
        self.events_queue.append(("client-new", id))

    def removeClient(self, websocket):
        """Odstrani websocket iz seznama aktivnih websocket povezav"""
        for id, ws in self.m_clientsWS.iteritems():
            if self.m_clientsWS[id] == websocket:
                Log.log('removeClient', id)
                del self.m_clientsWS[id]
                self.addEvent(("client-dead", id))
                break

    def sendMessage(self, id, *message):
        """Pošlje sporočilo uporabniku z id-jem id"""
        json_message = json.dumps({'type':message[0], 'data': message[1]})
        self.m_clientsWS[id].write_message(unicode(json_message))
    
    def broadcastMessage(self, *message):
        """Pošlje sporočilo vsem uporabnikom"""
        for id, ws in self.m_clientsWS.iteritems():
            self.sendMessage(id, *message)
        
    def newClient(self):
        """Vrne začetno stanje podatkov o avtomovilu za novega igralca"""
        ret = {'type':0, 'angle':0, 'rspeed':0}
        ret['x'], ret['y'], ret['z'], ret['angle'] = self.m_grid.nextStart()
        for axis in ['x', 'y', 'z']:
            ret[axis] += self.m_boxRadius
        ret['angle'] *= math.pi/2
        Log.log("Server", "newClient angle %f" % ret['angle'])
        return ret

    def newInternal(self):
        """Vrne interne podatke za novega igralca ali za igralca, ki je padel iz platforme."""
        return {'sangle':0, 'speed':0, 'zspeed':0}

    def __init__(self, boxfile = 'mini.level', port = 0xABBA):
        """Inicializacija strežnika"""
        self.events_queue = deque()     # = vrsta dogodkov =
        self.m_clients = {}             # = seznam igralcev =
        self.m_clientsWS = {}           # = seznam websocket povezav vsakega igralca =
        self.m_clientStates = {}        # = seznam pritisnjenih tipk vsakega igralca =
        self.m_clientInternal = {}      # = seznam stanj internih parametrov vsakega igralca =
        self.m_clientData = {}          # = seznam podatkov vsakega igralca =
        
        # Konstante
        self.m_floorDistance = 1
        self.m_rotation_factor = 10
        self.m_carHeight = 1
        self.m_carRadius = 3
        self.m_carSize = self.m_carRadius * 2
        self.m_boxRadius = 5
        self.m_boxSize = self.m_boxRadius * 2
        self.m_grid, self.m_gridForClients = Box.readBoxFile(boxfile, self.m_boxSize, self.toBox, self.fromBox)

    def toBox(self, x, y, z):
        return (int(x / self.m_boxSize), int(y / self.m_boxSize), int(z / self.m_boxSize))

    def fromBox(self, x, y, z):
        return (x * self.m_boxSize, y * self.m_boxSize, z * self.m_boxSize)
    
    def run(self):
        calculate_time = 0
        broadcast_time = 0
        score_time = 0

        # ================
        # = Glavna zanka =
        # ================
        # while 1:
        now = time.time()

        # for event in self.m_netServer.waitForEvents(0.01):
        # for event in self.events_queue:
        events_queue_len = len(self.events_queue)
        i = 0
        while i < events_queue_len:
            i += 1
            event = self.events_queue.popleft()
            Log.log("Server", "Received event " + str(event))
            func = event[0]
            if func == "client-message":
                id, message = event[1:3]
                Log.log("Server", "client-message id: %d, message: %s" % (id, str(message)))
                
                try:
                    mfunc = message[0]
                    Log.log("Server", "mfunc %s" % mfunc)
                    if mfunc == "key-state":
                        Log.log("Server", "Client %d message key-state: " % id + str(message))
                        keyState = message[1]
                        # if keyState.has_key('up'):
                        #     Log.log("Server", "up up and away")
                        # if keyState.has_key('left'):
                        #     Log.log("Server", "left left and sideways")
                        assert id in self.m_clients
                        self.m_clientStates[id] = keyState
                    elif mfunc == "my-name":
                        self.m_clientData[id]['name'] = message[1]
                        # Log.log("Server", "my-name %d message " % id + str(message[1]))
                    elif mfunc == "exit":
                        # FIX
                        Log.log("Server", "Stopping server")
                        return
                    else:
                        raise RuntimeError, "Unknown message type " + mfunc
                except:
                    Log.log("Server", "Error in client %d message " % id + str(message))
                    
            elif func == "client-new":
                id = event[1]
                Log.log("Server", "New client %d" % id)
                assert not id in self.m_clients
                self.m_clients[id] = self.newClient()
                self.m_clientStates[id] = {}
                self.m_clientInternal[id] = self.newInternal()
                self.m_clientData[id] = {'score':0}
                self.sendMessage(id, *("your-id", id))
                self.sendMessage(id, *("static-boxes", self.m_gridForClients))
                self.sendMessage(id, *("start-position", self.m_clients[id]))
            elif func == "client-dead":
                id = event[1]
                Log.log("Server", "Client %d is gone" % id)
                assert id in self.m_clients
                del self.m_clients[id]
                del self.m_clientStates[id]
                del self.m_clientInternal[id]
                del self.m_clientData[id]
        # end for event
        
        if now >= calculate_time:
            calculate_time = now + 0.01
        
            for id, client in self.m_clients.iteritems():
                if client['z'] < -290:
                    self.m_clients[id] = self.newClient()
                    self.m_clientInternal[id] = self.newInternal()
                    data = self.m_clientData[id]
                    if data.has_key("oponentid") and data.has_key("oponenttime"):
                        oid = data['oponentid']
                        otime = data['oponenttime']
                        if otime > now and self.m_clientData.has_key(oid):
                            self.m_clientData[oid]['score'] += 1
                        else:
                            data['score'] -= 1
                    else:
                        data['score'] -= 1
  
  
            def decompose(angle, length):
                return (length * math.sin(angle), length * math.cos(angle))
  
            def compose(x, y):
                return (math.atan2(x, y), math.sqrt(x*x + y*y))
  
            alreadyid = {}
  
            zfloor = {}
  
            for id, client in self.m_clients.iteritems():
                internal = self.m_clientInternal[id]
  
                alreadyid[id] = 1
                zfloor[id] = -300
  
                for box in self.m_grid.getVicinity(client['x'], client['y'], client['z']):
                    clash = 0
                    maxdiff = 0
                    for axis in ['x', 'y']:
                        if client[axis] < box[axis] + self.m_boxRadius:
                            diff = math.fabs(box[axis] + self.m_boxRadius - client[axis] - self.m_carRadius)
                        else:
                            diff = math.fabs(box[axis] + self.m_boxRadius - client[axis] + self.m_carRadius)
  
                        if diff < self.m_boxRadius + 0.1:
                            clash += 1
                            if diff > maxdiff:
                                clashaxis = axis
                                maxdiff = diff
  
                    if clash >= 2:
                        ztop = box['z'] + 2*self.m_boxRadius
  
                        if box.has_key('topmost') and client['z'] + 0.1 > ztop:
                            if ztop > zfloor[id]:
                                zfloor[id] = ztop
                                if client['z'] < ztop + self.m_floorDistance:
                                    if box['type'] == 2:
                                        internal['zspeed'] += 40
                                    elif box['type'] == 3:
                                        client['rspeed'] += 0.001
                                    elif box['type'] == 4:
                                        client['rspeed'] -= 0.001
                                    elif box['type'] == 7:
                                        internal['speed'] *= 1.05
  
                                if box['type'] == 8:
                                    internal['zspeed'] *= 0.95
                                    internal['speed'] *= 0.95
                        elif client['z'] + self.m_carHeight > box['z'] and client['z'] < ztop - 0.1:
                            if client['z'] + self.m_carHeight * 0.1 > box['z']:
                                ax = clashaxis
                                if ax == 'x':
                                    ay = 'y'
                                else:
                                    ay = 'x'
  
                                #oldx = client[ax]
  
                                #cfactor = (client[ax] - box[ax] - self.m_boxRadius) / (client[ay] - box[ay] - self.m_boxRadius)
  
                                onleft = client[ax] < box[ax] + self.m_boxRadius                                        
  
                                if box['type'] == 2:
                                    sx, sy = decompose(internal['sangle'], internal['speed'])
                                    bounce = {'x':0, 'y':0}
                                    if onleft:
                                        bounce[ax] -= 2 # default 40
                                    else:
                                        bounce[ax] += 2 # default 40
                                    internal['zspeed'] += 2 # default 10
                                    internal['sangle'], internal['speed'] = compose(sx + bounce['x'], sy + bounce['y'])
                                elif box['type'] == 3:
                                    client['rspeed'] += 0.001
                                elif box['type'] == 4:
                                    client['rspeed'] -= 0.001
                                elif box['type'] == 7:
                                    internal['speed'] *= 1.05
  
  
                                if onleft:
                                    client[ax] = box[ax] - self.m_carRadius
                                else:
                                    client[ax] = box[ax] + 2*self.m_boxRadius + self.m_carRadius
  
                                #mx = math.fabs(client[ax] - oldx)
                                #if client[ay] < box[ay] + self.m_boxRadius:
  
                                #client[ay] += mx * cfactor
  
  #                                 dx = client[ax] - (box[ax] + self.m_boxRadius)
  #                                 dy = client[ay] - (box[ay] + self.m_boxRadius)
  #                                 cangle = math.atan2(dx, dy)
  #                                 move = (self.m_boxRadius + self.m_carRadius) / math.sin(cangle)
  #                                 mx, my = decompose(cangle, move)
  
  #                                 client[ax] += mx
  #                                 client[ay] += my
                            elif maxdiff < self.m_boxRadius * 0.7:
                                client['z'] = box['z'] - self.m_carHeight - 0.1
                                client['zspeed'] = -0.1
  
  
                for oid, oclient in self.m_clients.iteritems():
                    if alreadyid.has_key(oid):
                        continue
  
                    ointernal = self.m_clientInternal[oid]
  
                    x, y, z = client['x'], client['y'], client['z']
                    ox, oy, oz = oclient['x'], oclient['y'], oclient['z']
                    dx = ox - x
                    dy = oy - y
                    dz = oz - z
  
                    dist = math.sqrt(dx*dx + dy*dy)
  
                    if dist < self.m_carSize and math.fabs(dz) < self.m_carHeight:
                        self.m_clientData[id]['oponentid'] = oid
                        self.m_clientData[id]['oponenttime'] = now+5
                        self.m_clientData[oid]['oponentid'] = id
                        self.m_clientData[oid]['oponenttime'] = now+5
  
                        tmp = internal['zspeed']
                        internal['zspeed'] = ointernal['zspeed'] * 0.8
                        ointernal['zspeed'] = tmp * 0.8
  
                        bumpangle = math.atan2(dx, dy)
                        obumpangle = math.atan2(-dx, -dy)
  
                        sx, sy = decompose(internal['sangle'], internal['speed'])
                        bump = internal['speed'] * math.cos(bumpangle - internal['sangle'])
                        bumpx, bumpy = decompose(bumpangle, bump)
                        dbumpx, dbumpy = decompose(bumpangle, 0.8 * bump)
  
                        osx, osy = decompose(ointernal['sangle'], ointernal['speed'])
                        obump = ointernal['speed'] * math.cos(obumpangle - ointernal['sangle'])
                        obumpx, obumpy = decompose(obumpangle, obump)
                        odbumpx, odbumpy = decompose(obumpangle, 0.8 * obump)
  
                        if math.cos(obumpangle - ointernal['sangle']) >= 0:
                            client['rspeed'] += 0.015 * ointernal['speed'] * math.sin(obumpangle - ointernal['sangle'])
  
                        if math.cos(bumpangle - internal['sangle']) >= 0:
                            oclient['rspeed'] += 0.015 * internal['speed'] * math.sin(bumpangle - internal['sangle'])
  
                        sx += odbumpx - bumpx
                        sy += odbumpy - bumpy
                        osx += dbumpx - obumpx
                        osy += dbumpy - obumpy
  
                        internal['sangle'], internal['speed'] = compose(sx, sy)
                        ointernal['sangle'], ointernal['speed'] = compose(osx, osy)
  
                        mx, my = decompose(bumpangle, (self.m_carSize - dist) / 1.98)
  
                        client['x'] -= mx
                        client['y'] -= my
                        oclient['x'] += mx
                        oclient['y'] += my
  
            for id, state in self.m_clientStates.iteritems():
                client = self.m_clients[id]
                internal = self.m_clientInternal[id]
  
                client['z'] += internal['zspeed']
                
                if client['z'] < zfloor[id] + self.m_floorDistance:
                    client['z'] = zfloor[id]
                    onfloor = 1
                else:
                    internal['zspeed'] -= 0.6
                    onfloor = 0
  
                if onfloor:
                    if state.has_key('jump'):
                        internal['zspeed'] += 3 # default: 15
                    else:
                        internal['zspeed'] *= -0.4
  
                    if internal['zspeed'] < 0:
                        internal['zspeed'] = 0
  
                    if state.has_key('down'):
                        rfactor = -self.m_rotation_factor
                    else:
                        rfactor = self.m_rotation_factor
  
                    if state.has_key('left'):
                        client['rspeed'] += 0.0015 * rfactor
                    elif state.has_key('right'):
                        client['rspeed'] -= 0.0015 * rfactor
  
                    client['rspeed'] *= 0.8    # Upočasnitev vrtenja zaradi trenja (0.95)
  
                    if math.fabs(client['rspeed']) < 0.0001:
                        client['rspeed'] = 0
  
                client['angle'] += client['rspeed']
  
                if onfloor:
                    if state.has_key('up'):
                        speedfactor = 0.5
                    elif state.has_key('down'):
                        speedfactor = -0.3
                    else:
                        speedfactor = 0
  
                    dx, dy = decompose(client['angle'], speedfactor)
  
                    internal['speed'] *= 0.85   # Upočasnitev premikanja zaradi trenja (0.97)
                else:
                    dx, dy = 0, 0
  
                sx, sy = decompose(internal['sangle'], internal['speed'])
  
                sx += dx
                sy += dy
  
                internal['sangle'], internal['speed'] = compose(sx, sy)
  
                if internal['speed'] < 0.0001:
                    internal['speed'] = 0
  
                client['x'] += sx
                client['y'] += sy
  
        if now >= broadcast_time:
            broadcast_time = now + 0.03
            # self.m_netServer.broadcastUDPMessage(("cars", self.m_clients))
            self.broadcastMessage(*("cars", self.m_clients))
            #self.m_netServer.broadcastMessage(("cars", 1))
  
        if now >= score_time:
            score_time = now + 3
            scores = []
            for id, data in self.m_clientData.iteritems():
                if data.has_key('name') and data.has_key('score'):
                    # Log.log("Server scores", "Server id %d, data %s: " % (id, {'name': data['name'], 'score': data['score']}))
                    scores.append({'name': data['name'], 'score': data['score']})
                    # Log.log('Server', scores)
            # self.m_netServer.broadcastUDPMessage(("scores", scores))
            self.broadcastMessage(*("scores", scores))