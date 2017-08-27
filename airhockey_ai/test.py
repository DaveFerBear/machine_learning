from airhockey import AirHockeySim

def test_gui():
	try:
	    import Tkinter as tk # this is for python2
	except:
	    import tkinter as tk # this is for python3

	root=tk.Tk()
	canvas=tk.Canvas(root,width=400,height=400)
	canvas.pack()
	circle=canvas.create_oval(50,50,80,80,outline="white",fill="blue")

	def redraw():
	   canvas.after(100,redraw)
	   canvas.move(circle,5,5)
	canvas.after(100,redraw)
	root.mainloop()



if __name__ == '__main__':
	ah = AirHockeySim()
	test_gui()