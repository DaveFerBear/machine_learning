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

		#Players
		self._p1 = Player(rink_dim[0]/2., 100, player_radius)
		self._p2 = Player(rink_dim[0]/2., rink_dim[1]-100, player_radius)

		self._puck = Player(rink_dim[0]/2., rink_dim[1]/2., puck_radius)

	def print_status(self):
		print('working')

class Player(object):
	def __init__(self, x, y, radius, vx=0, vy=0):
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