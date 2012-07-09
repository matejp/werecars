# -*- coding: utf-8 -*-
import array
import cPickle
import Log
"""
BOX:
type: 20,21,22,23 - start Boxes
"""
class BoxGrid:
	def __init__(self, x, y, z, trans, itrans):
		self.m_data = array.array('b', [0] * (x*y*z))
		self.m_x = x
		self.m_y = y
		self.m_z = z
		self.m_trans = trans
		self.m_itrans = itrans
		self.m_start = []

	def addStart(self, x, y, z, angle):
		self.m_start.append((x,y,z, angle))
		Log.log("Box", "Added start point %d,%d,%d %d" % (x,y,z,angle))

	def nextStart(self):
		if len(self.m_start) == 0:
			x,y,z = self.m_itrans(0,0,0)
			return (x,y,z,0)
		ret = self.m_start.pop(0)
		self.m_start.append(ret)
		x,y,z = self.m_itrans(ret[0], ret[1], ret[2])
		return (x,y,z,ret[3])

	def getBox(self, x, y, z):
		if x < 0 or y < 0 or z < 0 or x >= self.m_x or y >= self.m_y or z >= self.m_z:
			return 0
		return self.m_data[x + self.m_x * (y + self.m_y * z)]

	def setBox(self, x, y, z, val):
		self.m_data[x + self.m_x * (y + self.m_y * z)] = val

	def getVicinity(self, x_, y_, z_):
		# Log.log("getVicinity", '----------------------------------------------------------')
		# Log.log("getVicinity", "%d,%d,%d" % (x_,y_,z_))
		x, y, z = self.m_trans(x_, y_, z_)
		ret = []
		for i in [x-1, x, x+1]:
			for j in [y-1, y, y+1]:
				for k in [z+1, z, z-1]:
					b = self.getBox(i, j, k)
					if b != 0:
						box = {'type':b}
						if self.getBox(i, j, k+1) == 0:
							box['topmost'] = 1
						box['x'], box['y'], box['z'] = self.m_itrans(i, j, k)
						# Log.log("getVicinity", box)
						ret.append(box)
						
		return ret

	def getDim():
		return (self.m_x, self.m_y, self.m_z)
	
	def __str__(self):
	    return 'BoxGrid class print function'

	def __repr__(self):
	    return 'BoxGrid class print function'

def readBoxFile(name, boxsize, trans, itrans):
	"""Load game level"""
	boxes = cPickle.load(file(name, 'rb'))

	mx = {'x': 0, 'y': 0, 'z': 0}
	for box in boxes:
		for what in ['x', 'y', 'z']:
			if box[what] < 0:
				raise RuntimeError, "Negative index"

			if box[what] > mx[what]:
				mx[what] = box[what]

	grid = BoxGrid(mx['x']+1, mx['y']+1, mx['z']+1, trans, itrans)
	forclient = []
	for box in boxes:
		if box['type'] >= 20 and box['type'] < 24:
		    # Koordinate tipa 20,21,22,23 predstavljajo začetne položaje igralcev
		    # in se ne prikažejo na zaslonu.
			grid.addStart(box['x'], box['y'], box['z'], box['type']-20)
		else:
		    # Koordinate kock, iz katerih je sestavljena platforma za igro.
		    # Koordinate, ki se posredujejo uporabniku za izris levela.
			grid.setBox(box['x'], box['y'], box['z'], box['type'])
			fc = {}
			fc['x'], fc['y'], fc['z'] = itrans(box['x'], box['y'], box['z'])
			fc['type'] = box['type']
			fc['size'] = boxsize
            # Log.log("toBox Orig:", "x:%4d, y:%4d, z:%4d size:%4d" % (box['x'], box['y'], box['z'], boxsize))
            # Log.log("toBox new :", "x:%4d, y:%4d, z:%4d size:%4d" % (fc['x'], fc['y'], fc['z'], fc['size']))
			forclient.append(fc)

	return (grid, forclient)
