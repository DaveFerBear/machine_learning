from airhockey import AirHockeySim
try:
    import Tkinter as tk # Python 2
except:
    import tkinter as tk # Python 3

'''
Used to verify tkinter works properly
'''
def test_gui():
	root = tk.Tk()
	canvas = tk.Canvas(root,width=400,height=400)
	canvas.pack()
	circle = canvas.create_oval(50,50,80,80,outline="white",fill="blue")
	def redraw():
	   canvas.after(100,redraw)
	   canvas.move(circle,2,2)
	canvas.after(100,redraw)
	root.mainloop()


'''
Used to verify physics engine working properly
'''
def test_airhockey():
	sim = AirHockeySim()

	# Canvas Boilerplate
	width, height = sim._rink_dim
	BORDER = 25
	root = tk.Tk()
	canvas = tk.Canvas(root, width=width+2*BORDER, height=height+2*BORDER)
	canvas.pack()

	# Draw Rink
	rect = canvas.create_rectangle(BORDER, BORDER, width+BORDER, height+BORDER)

	#Draw Puck and Players
	p1 = canvas.create_oval(sim._p1.get_corner_pos(shift=BORDER))
	p2 = canvas.create_oval(sim._p2.get_corner_pos(shift=BORDER))
	puck = canvas.create_oval(sim._puck.get_corner_pos(shift=BORDER))

	def redraw():
		canvas.after(1,redraw) # wait time (animation speed)
		sim.update()

		canvas.move(p1, sim._p1._vx, sim._p1._vy)
		canvas.move(p2, sim._p2._vx, sim._p2._vy)
		canvas.move(puck, sim._puck._vx, sim._puck._vy)

	redraw()
	root.mainloop()


if __name__ == '__main__':
	ah = AirHockeySim()
	#test_gui()
	test_airhockey()

