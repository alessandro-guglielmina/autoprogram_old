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


# def confirm_decorator(confirm_function):
# 	"""
# 		this decorator is added to any confirm function, in order to print the error (if any) on the communication label
# 	"""

# 	def wrapper_function(*args, **kwargs):

# 		try:

# 			return confirm_function(*args, **kwargs)

# 		except Exception as e:

# 			args[0].root.comm_label.config(text=f'{e}') # args[0] is self, i.e. the frame object (the page)

# 	return wrapper_function


# root class (tk.Tk is the root)
class AutoprogramApp(tk.Tk):

	def __init__(self, *args, **kwargs):

		tk.Tk.__init__(self, *args, **kwargs)

		# tk.Tk.iconbitmap(self, "icon bitmap path")

		tk.Tk.wm_title(self, "autoprogram")

		tk.Tk.geometry(self,'500x320')

		self.iconbitmap("images/icon.ico")

		# create a menu and its cascades
		root_menu = tk.Menu(self)

		self.config(menu=root_menu)

		file_menu = tk.Menu(root_menu, tearoff=False)

		root_menu.add_cascade(label="File",  menu = file_menu)

		file_menu.add_command(label="Exit", command=self.quit)

		# create the container of the child frames, it's a frame inside the root (it's always the same frame because it's the one in the root)
		container_frame = tk.Frame(self)

		container_frame.grid(row=1, column=0, columnspan=3, pady=20)

		# the following widgets get their features from the specific page
		# create an heading
		self.head_label = tk.Label(self, font=LARGE_FONT)

		self.head_label.grid(row=0, column=0, columnspan=2)

		# create a label for messages
		self.comm_label = tk.Label(self, text="", width=82, anchor=tk.W)

		self.comm_label.grid(row=2, column=0, columnspan=4)

		# create back button
		self.back_button = tk.Button(self, text="Back", state=tk.DISABLED, width=10)

		self.back_button.grid(row=3, column=0, pady=10)

		#create a confirm button
		self.confirm_button = tk.Button(self, text="Confirm", width=10) # pass the function as thread in order to prevent the app from freezing

		self.confirm_button.grid(row=3, column=1, pady=10)

		# create a dictionary with all the page objects (istantiations of respective classes)
		self.frames = {}

		for F in (InitializeFrame, InsertParametersFrame, CreateProgramFrame):

			frame = F(container_frame, self) # F(container_frame, root)

			self.frames[F] = frame

			#frame.grid(row=0, column=0, sticky="NSEW")

		self.show_frame(InitializeFrame)


	def show_frame(self, cont):
		# this function shows the selected frame (the index arguent is the class itself)

		page_frame = self.frames[cont]

		self.comm_label.config(text="")

		self.head_label.config(text=page_frame.head_text)

		self.back_button.config(command=lambda: threading.Thread(target=page_frame.back_function).start(), state=page_frame.back_butt_state)

		self.confirm_button.config(command=lambda: threading.Thread(target=page_frame.confirm_function).start(), state=page_frame.confirm_butt_state)

		page_frame.grid(row=1, column=0, sticky="NSEW")

		page_frame.tkraise()


class InitializeFrame(tk.Frame):

	def __init__(self, container_frame, root):

		# save the root in object variable
		self.root = root

		# save the container frame in object variable
		self.container_frame = container_frame

		# tk.Frame is used instead of super(), as tkinter classes are old
		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

		# save the root in object variable
		self.root = root

		# features to be passed to the root template frame
		self.head_text = "Initialization Page"

		self.back_butt_state = tk.DISABLED

		self.confirm_butt_state = tk.NORMAL

		# create widgets characteristic of the current page
		# get a list of all the families
		fam_names_list = app.Initialize.get_fam_names()

		# get families names from the master program directory
		self.fam_listbox = tk.Listbox(self, width=20)

		# insert family names into the listbox
		for i, fam_name in enumerate(fam_names_list):

			self.fam_listbox.insert(i, fam_name)

		self.fam_listbox.grid(row=1, column=0, columnspan=1, padx=20)

		self.tool_name_entry = tk.Entry(self, width=20)

		self.tool_name_entry.insert(0, 'tool name')

		self.tool_name_entry.grid(row=1, column=1, columnspan=1)


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		pass


	# @confirm_decorator
	def confirm_function(self):
		"""
			this function is associated to the confirm button, it saves the user inputs into common variables and get other common variables based on those
		"""

		common.Variables.fam_name = self.fam_listbox.get(tk.ANCHOR)

		common.Variables.tool_name = self.tool_name_entry.get()

		app.Initialize.get_fam_dependent_vars()

		self.root.frames[InsertParametersFrame].configure_frame()

		self.root.comm_label.config(text="")

		self.root.show_frame(InsertParametersFrame)


class InsertParametersFrame(tk.Frame):

	def __init__(self, container_frame, root):

		# tk.Frame is used instead of super(), as tkinter classes are old
		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

		# save the root in object variable
		self.root = root

		self.back_butt_state = tk.NORMAL

		self.confirm_butt_state = tk.NORMAL


	def configure_frame(self):

		self.head_text = "Input Parameters Page, Family: " + common.Variables.fam_name + ", Name: " + common.Variables.tool_name

		# get a list with all the input descriptions, with the sam order of the input values
		self.descr_list = app.InsertParameters.get_params_descr()

		# get the number of input parameters
		self.params_num = len(self.descr_list)

		# create a list with all the labels containing input descriptions
		self.descr_label_list = [tk.Label(self, text=descr, width=20) for descr in self.descr_list]

		# create a list of entries (its length is equal to descr_list)
		self.entry_list = [tk.Entry(self, width=20) for i in range(self.params_num)]

		# create an entry box and its description for each input parameters
		for descr_label, entry, i in zip(self.descr_label_list, self.entry_list, range(self.params_num)):

			descr_label.grid(row=i, column=0)

			entry.grid(row=i, column=1)


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		self.root.show_frame(InitializeFrame)


	# @confirm_decorator
	def confirm_function(self):

		input_vals = []

		for i, entry in enumerate(self.entry_list):

			input_val = float(entry.get())

			input_vals.append(input_val)

		app.InsertParameters.save_input_params(input_vals)

		self.root.show_frame(CreateProgramFrame)

		self.root.frames[CreateProgramFrame].run()


class CreateProgramFrame(tk.Frame):

	def __init__(self, container_frame, root):

		# tk.Frame is used instead of super(), as tkinter classes are old
		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

		# save the root in object variable
		self.root = root

		# features to be passed to the root template frame
		self.head_text = "Creating the program..."

		self.back_butt_state = tk.NORMAL

		self.confirm_butt_state = tk.NORMAL


	def run(self):

		# function that creates the program, threaded in order to prevent the application from freezing
		app.CreateProgram.run()


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		self.root.show_frame(InsertParametersFrame)


	# @confirm_decorator
	def confirm_function(self):

		self.root.show_frame(InitializeFrame)


def run():
	app = AutoprogramApp() # istantiate root
	app.mainloop()