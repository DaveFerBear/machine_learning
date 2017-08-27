'''
This class contains logic for air hockey physics engine
'''
class AirHockeySim(object):

	def __init__(self, player_radius=5, puck_radius=4, rink_dim=(100,200), net_width=20):
		#Gameplay params
		self._player_radius = player_radius
		self._puck_radius = puck_radius
		self._rink_dim = rink_dim
		self._net_width = net_width

		#Players
		self._p1 = Player(rink_dim[0]/2., 10)
		self._p2 = Player(rink_dim[0]/2., rink_dim[1]-10)
		
	def print_status(self):
		print('working')



class Player(object):
	def __init__(self, x, y, vx=0, vy=0):
		self._x = x
		self._y = y
		self._vx = vx
		self._vy = vy

	def update():
		self._x += self._vx
		self._y += self._vy