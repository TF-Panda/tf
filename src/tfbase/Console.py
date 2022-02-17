from tkinter import *

from panda3d.core import loadPrcFileData

class Console:

    def __init__(self):
        base.startTk()

        self.window = Tk()
        self.frame = Frame(self.window)
        self.lbl = Label(text="Enter PRC data:", master=self.frame)
        self.lbl.grid(row=0, column=0)
        self.entry = Entry(width=50, master=self.frame)
        self.entry.grid(row=1, column=0)
        self.submit = Button(text='Submit', master=self.frame)
        self.submit.grid(row=2, column=0)
        self.frame.pack()
        self.submit.bind("<Button-1>", self.handleSubmit)

    def cleanup(self):
        self.lbl.destroy()
        self.entry.destroy()
        self.submit.destroy()
        self.frame.destroy()
        self.window.destroy()

        self.lbl = None
        self.entry = None
        self.submit = None
        self.frame = None
        self.window = None

    def handleSubmit(self, blah):
        loadPrcFileData('console', self.entry.get())
