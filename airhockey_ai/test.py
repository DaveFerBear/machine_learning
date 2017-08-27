from airhockey import AirHockeySim
try:
    import Tkinter as tk # this is for python2
except:
    import tkinter as tk # this is for python3

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

def test_airhockey():
	hockey = AirHockeySim()

if __name__ == '__main__':
	ah = AirHockeySim()
	test_gui()