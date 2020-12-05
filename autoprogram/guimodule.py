import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading

from autoprogram import appmodule as app
from autoprogram import settingsmodule as sm
from autoprogram import common

LARGE_FONT= ("Verdana", 10)


def try_decorator(confirm_function):
	"""
		this decorator is added to any confirm function, in order to print the error (if any) on the communication label
	"""

	def wrapper_function(*args, **kwargs):

		try:

			return confirm_function(*args, **kwargs)

		except Exception as e:

			args[0].root.comm_label.config(text=f'{e}') # args[0] is self, i.e. the frame object (the page)

	return wrapper_function


# root class (tk.Tk is the root)
class AutoprogramApp(tk.Tk):

	def __init__(self, *args, **kwargs):

		tk.Tk.__init__(self, *args, **kwargs)

		self.wm_title("autoprogram")

		self.geometry('500x320')

		self.iconbitmap("images/icon.ico")

		self.root = self # needed to use the try decorator on methods, as the object must have a root variable

		# create a menu and its cascades
		root_menu = tk.Menu(self)

		self.config(menu=root_menu)

		file_menu = tk.Menu(root_menu, tearoff=False)

		root_menu.add_cascade(label="File",  menu = file_menu)

		file_menu.add_command(label="Settings", command=self.show_settings_window)

		file_menu.add_command(label="Exit", command=self.quit)

		# create the container of the child frames, it's a frame inside the root (it's always the same frame because it's the one in the root)
		self.container_frame = tk.Frame(self)

		self.container_frame.grid(row=1, column=0, columnspan=3, pady=20)

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

		# instantiate page frame objects
		self.instantiate_page_frames()


	#@try_decorator
	def instantiate_page_frames(self):
		"""
		function that instantiate all the page frames
		"""

		self.frames = {} # create a dictionary with all the page objects (istantiations of respective classes)

		for F in (InitializeFrame, InsertParametersFrame, CreateProgramFrame):

			frame = F(self.container_frame, self) # F(container_frame, root)

			self.frames[F] = frame

			frame.grid(row=0, column=0, sticky="NSEW")

		self.show_frame(InitializeFrame)	


	def show_settings_window(self):

			settings_window = SettingsWindow(self) # instantiate another window, passing the root as argument


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


	def configure_insert_params_frame(self):
		"""
			this function has to be called after the user has chosen the family, in order to set up the parameter entries for the following page 
		"""

		insert_params_frame = self.root.frames[InsertParametersFrame]

		insert_params_frame.root.frames[InsertParametersFrame].head_text = "Input Parameters Page, Family: " + common.Variables.fam_name + ", Name: " + common.Variables.tool_name

		# forget all the previous widgets
		try:

			for descr_label, entry in zip(insert_params_frame.root.frames[InsertParametersFrame].descr_label_list, insert_params_frame.root.frames[InsertParametersFrame].entry_list):

				descr_label.grid_forget()

				entry.grid_forget()

		except AttributeError:

			pass #if an AttributeError is raised, it means that no widget needs to be reset

		# get a list with all the input descriptions, with the same order of the input values
		insert_params_frame.descr_list = app.InsertParameters.get_params_descr()

		# get the number of input parameters
		insert_params_frame.params_num = len(insert_params_frame.descr_list)

		# create a list with all the labels containing input descriptions
		insert_params_frame.descr_label_list = [tk.Label(insert_params_frame, text=descr, width=20) for descr in insert_params_frame.descr_list]

		# create a list of entries (its length is equal to descr_list)
		insert_params_frame.entry_list = [tk.Entry(insert_params_frame, width=20) for i in range(insert_params_frame.params_num)]

		# create an entry box and its description for each input parameters
		for descr_label, entry, i in zip(insert_params_frame.descr_label_list, insert_params_frame.entry_list, range(insert_params_frame.params_num)):

			descr_label.grid(row=i, column=0)

			entry.grid(row=i, column=1)


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		pass


	#@try_decorator
	def confirm_function(self):
		"""
			this function is associated to the confirm button, it saves the user inputs into common variables and get other common variables based on those
		"""

		common.Variables.fam_name = self.fam_listbox.get(tk.ANCHOR)

		common.Variables.tool_name = self.tool_name_entry.get()

		app.Initialize.get_fam_dependent_vars()

		self.configure_insert_params_frame()

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


	def create_program(self):

		self.root.comm_label.config(text='creating the program...')

		# function that creates the program, threaded in order to prevent the application from freezing
		app.CreateProgram.run()

		self.root.comm_label.config(text='program created!')


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		self.root.show_frame(InitializeFrame)


	#@try_decorator
	def confirm_function(self):

		input_vals = []

		for i, entry in enumerate(self.entry_list):

			input_val = float(entry.get())

			input_vals.append(input_val)

		app.InsertParameters.save_input_params(input_vals)

		self.root.show_frame(CreateProgramFrame)

		# the create program process is triggered when the confirm button of the previous page is pushed
		self.create_program()


class CreateProgramFrame(tk.Frame):

	def __init__(self, container_frame, root):

		# tk.Frame is used instead of super(), as tkinter classes are old
		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

		# save the root in object variable
		self.root = root

		# features to be passed to the root template frame
		self.head_text = "Create Program Page"

		self.back_butt_state = tk.NORMAL

		self.confirm_butt_state = tk.NORMAL


	# back_function and confirm_function are to be passed to the back and confirm buttons
	def back_function(self):

		self.root.show_frame(InsertParametersFrame)


	#@try_decorator
	def confirm_function(self):

		self.root.show_frame(InitializeFrame)


class SettingsWindow(tk.Toplevel):

	def __init__(self, root):

		tk.Toplevel.__init__(self, root)

		self.wm_title("settings")

		self.geometry('400x220')

		self.iconbitmap("images/icon.ico")

		self.master_progs_dir_label = tk.Label(self, text='master programs directory: ').grid(row=0, column=0)

		self.res_prog_dir_label = tk.Label(self, text='result program directory: ').grid(row=1, column=0)

		self.master_progs_dir_entry = tk.Entry(self, width=40)

		self.res_prog_dir_entry = tk.Entry(self, width=40)

		self.master_progs_dir_entry.insert(0, common.Variables.master_progs_dir_path)

		self.res_prog_dir_entry.insert(0, common.Variables.res_prog_dir_path)

		self.master_progs_dir_entry.grid(row=0, column=1)

		self.res_prog_dir_entry.grid(row=1, column=1)

		self.cancel_button = tk.Button(self, text="Cancel", width=10, command=self.destroy)

		self.cancel_button.grid(row=2, column=0, pady=10)

		self.apply_button = tk.Button(self, text="Apply", width=10, command=self.save_work_dirs) # pass the function as thread in order to prevent the app from freezing

		self.apply_button.grid(row=2, column=1, pady=10)

	
	def save_work_dirs(self):

		master_progs_dir_path = self.master_progs_dir_entry.get()

		res_prog_dir_path = self.res_prog_dir_entry.get()

		sm.save_work_dirs(master_progs_dir_path, res_prog_dir_path)


def run():
	app = AutoprogramApp() # instantiate root
	app.mainloop()