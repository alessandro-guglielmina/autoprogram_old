# import os
# from itertools import compress

# from autoprogram import common

# # This function return the user inputs
# def user_input(ch_list = None, ch_ids = None, cast = None, print_list = None): #(ch_list, ch_id, cast, print_list)
# 	# If there is a list of choices
# 	if ch_list is not None and ch_ids is not None:
# 		cast = str
# 		bound_val = True
# 		print_list = ''
# 		for i, j in zip(ch_ids, ch_list):
# 			print_list = print_list + f'Enter {i} for {j}\n'
# 		print_list = [print_list]
# 	# if there isn't
# 	elif cast is not None and print_list is not None:
# 		bound_val = False
# 	else:
# 		raise ValueError('Wrong arguments combination.')
# 	inp_list = []
# 	converted = False
# 	for i in print_list:
# 		os.system('clear')
# 		while True:
# 			try:
# 				inp_i = cast(input(f'{i}\n> ')) # user input call
# 				if bound_val: # (so cast = str and ch_id must be given)
# 					inp_i = inp_i.upper() # the choice must be capital to make the choice case insensitive
# 					if inp_i in ch_ids:
# 						bool_filt = [i == inp_i for i in ch_ids]
# 						ch = list(compress(ch_list, bool_filt))[0] # use boolean indexing on a list
# 						inp_i = ch # inp_val_i is reassigned with the choice corresponding to the chosen index
# 						converted = True
# 					else:
# 						os.system('clear')
# 						print("Input non among the possible choices.\n")
# 				if converted or not bound_val:
# 					os.system('clear')
# 					inp_list.append(inp_i)
# 					print("You have entered: " + str(inp_i) + "\n")
# 					break
# 			except ValueError:
# 				print("Wrong input type\n")
# 	res = inp_list
# 	return res # list([inp1, inp2, ...])


# def select_family(fam_name_list):
# 		fam_name_ids = [str(i + 1) for i in list(range(len(fam_name_list)))]
# 		# Acquire user input
# 		print('Select family:\n')
# 		common.Variables.fam_name = user_input(ch_list = fam_name_list, ch_ids = fam_name_ids)[0] # 'ch_fam'
# 		os.system('clear')

# def print_tool_type():
# 	if common.Variables.tool_type:
# 		print("Tool type is: " + common.Variables.tool_type)
# 	else:
# 		print("Tool type not assigned yet.")


# def select_position(Position):
# 		ch_list = ['confirm', 'repeat', 'move back']
# 		ch_ids = ['C', 'R', 'B']
# 		ch = user_input(ch_list = ch_list, ch_ids = ch_ids)
# 		pos_select = ch[0]
# 		if (pos_select == 'confirm'):
# 			next_pos = Position.follow_pos
# 		elif (pos_select == 'repeat'):
# 			next_pos = Position.current_pos
# 		elif (pos_select == 'move back'):
# 			next_pos = Position.prev_pos
# 		return next_pos


import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import sys

from autoprogram import appmodule as app
from autoprogram import common

LARGE_FONT= ("Verdana", 10)

# root class (tk.Tk is the root)
class AutoprogramApp(tk.Tk):

	def __init__(self, *args, **kwargs):

		tk.Tk.__init__(self, *args, **kwargs)

		# tk.Tk.iconbitmap(self, "icon bitmap path")

		tk.Tk.wm_title(self, "autoprogram")

		tk.Tk.geometry(self,'400x260')

		# create a menu
		root_menu = tk.Menu(self)

		self.config(menu=root_menu)

		file_menu = tk.Menu(root_menu, tearoff=False)

		root_menu.add_cascade(label="File",  menu = file_menu)

		file_menu.add_command(label="Exit", command=self.quit)

		# declare the container of the child frames, it's a frame inside the root (it's always the same frame because it's the one in the root)
		container_frame = tk.Frame(self)

		container_frame.pack(side="top", fill="both", expand = True)

		# container.grid_rowconfigure(0, weight=1)

		# container.grid_columnconfigure(0, weight=1)

		# canvas = tk.Canvas(self, width=2000, height=2000)

		# canvas.place(x=-100, y=220)

		# blackLine = canvas.create_line(0,2,2000,2)

		# canvas.configure(background='gray')

		# canvas_id = canvas.create_text(432,25)

		# canvas.itemconfig(canvas_id, text = "my mail")

		# canvas.insert(canvas_id, 12, "")

		self.frames = {}

		# instantiate each frame
		for F in (InitializePage,):

			frame = F(container_frame, self) # F(parent, controller), container = Frame, self = tk.Tk (root)

			self.frames[F] = frame # the class itself is used as the index to select its instan

			frame.grid(row=0, column=0)

		self.show_frame(InitializePage)

	def show_frame(self, cont):
		# this function shows the selected frame (the index arguent is the class itself)

		frame = self.frames[cont]

		frame.tkraise()


class InitializePage(tk.Frame):

	def __init__(self, container_frame, root):

		# tk.Frame is used instead of super(), as tkinter classes are old
		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

		head_label = tk.Label(self, text="initialization page", font=LARGE_FONT)

		head_label.grid(row=0, column=0, columnspan=2)

		fam_names_list = app.Initialize.get_fam_names()

		# get families names from the master program directory
		self.fam_listbox = tk.Listbox(self, width=20)

		# insert family names into the listbox
		for i, fam_name in enumerate(fam_names_list):

			self.fam_listbox.insert(i, fam_name)

		self.fam_listbox.grid(row=1, column=0, columnspan=1)

		self.tool_name_entry = tk.Entry(self, width=20)

		self.tool_name_entry.insert(0, 'tool name')

		self.tool_name_entry.grid(row=1, column=1, columnspan=1, padx=20)

		self.comm_label = tk.Label(self, text="")

		self.comm_label.grid(row=2, column=0, columnspan=1)

		back_button = tk.Button(self, text="Back", state=tk.DISABLED, width=10)

		back_button.grid(row=3, column=0, padx=60, pady=20)

		confirm_button = tk.Button(self, text="Confirm", width=10, command=lambda: threading.Thread(target=self.confirm_function).start()) # pass the function as thread in order to prevent the app from freezing

		confirm_button.grid(row=3, column=1, pady=20)

	def confirm_function(self):
		"""
			this function is associated to the confirm button, it saves the user inputs into common variables and get other common variables based on those
		"""

		try:

			common.Variables.fam_name = self.fam_listbox.get(tk.ANCHOR)

			common.Variables.tool_name = self.tool_name_entry.get()

			app.Initialize.get_fam_dependent_vars()

			self.comm_label.config(text="")

			# root.show_frame(InsertParametersPage)

		except FileNotFoundError:

			self.comm_label.config(text="Choose a family")


def run():
	app = AutoprogramApp() # istantiate root
	app.mainloop()

# 		button1 = ttk.Button(self, text="Send axis parameters to Visual Components 4.0", command=lambda: controller.show_frame(PageOne))

# 		button1.place(x=65,y=50)
# 70
# 71 button2 = ttk.Button(self, text="Display sensor data",
# 72 command=lambda: controller.show_frame(
# PageThree))
# 73 button2.place(x=65,y=80)
# 74
# 75 button3 = ttk.Button(self, text="Write data to file",
# 76 command=lambda: controller.show_frame(PageTwo)
# )
# 77 button3.place(x=65,y=110)
# 78
# 79 close_button = ttk.Button(self, text="Close",command=self.quit)
# 80
# 81 close_button.place(x=65,y=140)