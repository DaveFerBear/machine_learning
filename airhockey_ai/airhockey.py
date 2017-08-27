import math
'''
This class contains logic for air hockey physics engine
'''
class AirHockeySim(object):

	def __init__(self, player_radius=12, puck_radius=8, rink_dim=(200,400), net_width=20):
		#Gameplay Params
		self._player_radius = player_radius
		self._puck_radius = puck_radius
		self._rink_dim = rink_dim
		self._net_width = net_width

		#Players & Puck
		self._p1 = Player(rink_dim[0]/2., 50, player_radius)
		self._p2 = Player(rink_dim[0]/2., rink_dim[1]-50, player_radius)
		self._puck = Player(rink_dim[0]/2., rink_dim[1]/2., puck_radius)

	def print_status(self):
		print('working')

	def update(self):
		#Check for wall collisions
		for p in (self._p1, self._p2, self._puck):
			if p._x <= p._r or p._x >= self._rink_dim[0]-p._r:
				p._vx *= -1
			if p._y <= p._r or p._y >= self._rink_dim[1]-p._r:
				p._vy *= -1
			p.update()

		#Check for circle collisions
		for p in (self._p1, self._p2):
			if player_distance(p, self._puck) < p._r+self._puck._r:
				print('Collision')


class Player(object):
	def __init__(self, x, y, radius, vx=1, vy=1):
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

