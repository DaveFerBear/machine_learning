import math
from random import random
'''
This class contains logic for air hockey physics engine
'''
class AirHockeySim(object):

	def __init__(self, player_radius=12, puck_radius=8, rink_dim=(200,400), net_width=50):
		#Gameplay Params
		self._player_radius = player_radius
		self._puck_radius = puck_radius
		self._rink_dim = rink_dim
		self._net_width = net_width

		#Players & Puck
		self.reset()

	def print_status(self):
		print('working')

	def update(self):
		#Check for wall collisions
		for p in (self._p1, self._p2, self._puck):
			if (p._x <= p._r and p._vx < 0) or (p._x >= self._rink_dim[0]-p._r and p._vx > 0):
				p._vx *= -1
			if (p._y <= p._r and p._vy < 0) or (p._y >= self._rink_dim[1]-p._r and p._vy > 0):
				#Check for goal
				if p==self._puck and p._x > (self._rink_dim[0]-self._net_width)/2 and p._x < (self._rink_dim[0]+self._net_width)/2:
					print('GOAALLLL')
					self.reset()
					return
				p._vy *= -1
			p.update()

		#Check for circle collisions
		for p in (self._p1, self._p2):
			if player_distance(p, self._puck) < p._r+self._puck._r:
				v1 = math.sqrt(self._puck._vx**2 + self._puck._vy**2)
				v2 = math.sqrt(p._vx**2 + p._vy**2)
				th1 = math.atan(1.*self._puck._vy/self._puck._vx)
				th2 = math.atan(1.*p._vy/p._vx)
				phi = math.atan(1.*(p._x - self._puck._x)/(p._y - self._puck._y))

				v1x = (-v1*math.cos(th1-phi) +2*v2*math.cos(th2-phi))*math.cos(phi) \
					+ v1*math.sin(th1-phi)*math.cos(phi+math.pi/2.)

				v1y = (-v1*math.cos(th1-phi) +2*v2*math.cos(th2-phi))*math.sin(phi) \
					+ v1*math.sin(th1-phi)*math.sin(phi+math.pi/2.)
 
				self._puck._vx = -v1x
				self._puck._vy = -v1y
				p.update() # deliberately update twice to generate additional "clearance"


	def reset(self):
		self._p1 = Player(self._rink_dim[0]/2., 50, self._player_radius, vx=5*random(), vy=5*random())
		self._p2 = Player(self._rink_dim[0]/2., self._rink_dim[1]-50, self._player_radius, vx=5*random(), vy=5*random())
		self._puck = Player(self._rink_dim[0]/2., self._rink_dim[1]/2., self._puck_radius)

class Player(object):
	def __init__(self, x, y, radius, vx=0.01, vy=0.01):
		self._x = x
		self._y = y
		self._r = radius
		self._vx = vx
		self._vy = vy

	def update(self):
		self._x += self._vx
		self._y += self._vy

	def get_corner_pos(self, shift=0): #rendering helper
		x0 = self._x - self._r + shift
		y0 = self._y - self._r + shift
		x1 = self._x + self._r + shift
		y1 = self._y + self._r + shift
		return x0, y0, x1, y1


def player_distance(a, b):
		return math.sqrt((a._x - b._x)**2 + (a._y - b._y)**2)

