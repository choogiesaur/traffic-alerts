try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter 
except ImportError:
    # for Python3
    from tkinter import *   ## notice here too
top = Tk()

def buttFunc():
	tkinter.messagebox.showinfo("Hello Python", "Hello World")

b = Button ( top, text="Button Text", command = buttFunc)

b.pack()
top.mainloop()
