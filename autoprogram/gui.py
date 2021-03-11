import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog # delete
import threading # delete
import os # delete
from pathlib import Path # delete

from autoprogram import common
from autoprogram import helper as hp
from autoprogram import settingsparser as sp
from autoprogram import configdataparse as cdp
# from autoprogram.helper import try_decorator

DEFAULT_MODE = "create_manual"


# def# try_decorator(target_method):
# 	"""
# 	This decorator is added to any confirm function, in order to print the error (if any) on the communication label
# 	"""
# 	def wrapper_function(*args, **kwargs):
# 		try:
# 			args[0].root.comm_label_write("")
# 			return target_method(*args, **kwargs)
# 		except ValueError as ve:
# 			args[0].root.comm_label_write(ve) # args[0] is self, i.e. the frame object (the page)
# 	return wrapper_function

# def reset_comm_label(next_method):
# 	"""
# 	Description
# 	"""
# 	def wrapper_function(*args, **kwargs):
# 		args[0].root.comm_label.config(text="") # args[0] is self, i.e. the frame object (the page)
# 		return next_method(*args, **kwargs)
# 	return wrapper_function


class App(tk.Tk):
	"""
	Description
	"""
	def __init__(self, *args, **kwargs):
		tk.Tk.__init__(self, *args, **kwargs) # tk.Tk.__init__() used in place of super().__init__()
		self.wm_title("autoprogram")
		self.geometry('500x320')
		# Create a menu and its cascades
		root_menu = tk.Menu(self)
		self.config(menu=root_menu)
		file_menu = tk.Menu(root_menu, tearoff=False)
		root_menu.add_cascade(label="File",  menu = file_menu)
		file_menu.add_command(label="Settings", command=self.show_settings_window)
		file_menu.add_command(label="Exit", command=self.quit)
		# The following widgets get their features from the specific page
		# create an heading
		# self.mode = None
		self.head_label = tk.Label(self, width=70, height=3)
		self.head_label.grid(row=0, column=0, columnspan=3)
		# Create the container of the page frames, it's a frame inside the root
		# (it's always the same frame because it's the one in the root)
		# Its size is set to be always the same, regardless what's inside
		self.page_container_frame = tk.Frame(self, height=200, highlightbackground="black", highlightthickness=1)
		self.page_container_frame.grid(sticky="nswe", padx=20, columnspan=3) # set fixed size
		# self.page_container_frame.rowconfigure(0, weight=1)
		# self.page_container_frame.columnconfigure(0, weight=1)
		self.page_container_frame.grid_propagate(0)
		# self.page_container_frame.grid(row=1, column=0, columnspan=3)
		# Create a label for messages
		self.comm_label = tk.Label(self, text="")
		self.comm_label.grid(row=2, column=0, columnspan=3)
		# Create navigation buttons
		self.back_button = tk.Button(self, text="Back", width=10)
		self.back_button.grid(row=3, column=0, padx=20)
		self.next_button = tk.Button(self, text="Next", width=10) # pass the function as thread in order to prevent the app from freezing
		self.next_button.grid(row=3, column=1)
		self.instantiate_page_frames()
		self.show_page(SelectModePage)

	def show_settings_window(self):
		"""
		This method is used in the menu to show settings
		"""
		settings_window = SettingsWindow(self) # instantiate another window, passing the root (self) as argument

	##@try_decorator
	def instantiate_page_frames(self):
		"""
		This method instantiates all the page frames without choice-dependent customization
		"""
		self.pages = {} # create a dictionary with all the page objects (istantiations of respective classes)
		for F in (InitializationPage, SelectModePage, InputDataPage, CreateProgramPage):
			# F(page_container_frame, root), pages must be instantiated in inverse order,
			# because everyone needs the following one to be insantiated before itself
			page_frame = F(self.page_container_frame, self)
			self.pages[F] = page_frame
			page_frame.grid(row=0, column=0, sticky="NSEW")

	def root_setup(self, head_text=None, back_method=None, back_method_args=None, back_state=None, next_method=None, next_method_args=None, next_state=None):
		"""
		Description
		"""
		if back_method_args == None:
			back_method_args = []
		if back_state == None:
			back_state = tk.DISABLED
		if next_method_args == None:
			next_method_args = []
		if next_state == None:
			next_state = tk.DISABLED
		# Head text setup
		self.head_label.config(text=head_text)
		# Back button setup
		self.back_button.config(text="Back", state=back_state)
		if back_method is not None:
			self.back_button.config(command=lambda: threading.Thread(target=back_method, args=back_method_args).start())
		# Next button setup
		self.next_button.config(text="Next", state=next_state)
		if next_method is not None:
			self.next_button.config(command=lambda: threading.Thread(target=next_method, args=next_method_args).start())

	def comm_label_write(self, text):
		"""
		Description
		"""
		self.comm_label.config(text=text)

	def show_page(self, page_name, *args, **kwargs):
		"""
		Description
		"""
		try:
			self.comm_label_write("")
			page = self.pages[page_name]
			page.page_setup(*args, **kwargs)
			page.tkraise()
			page.run(*args, **kwargs)
		except ValueError as ve:
			self.comm_label_write(ve)


class SettingsWindow(tk.Toplevel):
	"""
	Description
	"""
	def __init__(self, root):
		tk.Toplevel.__init__(self, root)
		self.wm_title("settings")
		self.geometry('400x220')
		#self.iconbitmap("images/icon.ico")
		self.master_progs_dir_label = tk.Label(self, text='master programs directory: ').grid(row=0, column=0)
		self.res_progs_dir_label = tk.Label(self, text='result program directory: ').grid(row=1, column=0)
		self.master_progs_dir_entry = tk.Entry(self, width=40)
		self.res_progs_dir_entry = tk.Entry(self, width=40)
		self.master_progs_dir_entry.insert(0, common.master_progs_dir_path)
		self.res_progs_dir_entry.insert(0, common.res_progs_dir_path)
		self.master_progs_dir_entry.grid(row=0, column=1)
		self.res_progs_dir_entry.grid(row=1, column=1)
		self.cancel_button = tk.Button(self, text="Back", width=10, command=self.destroy)
		self.cancel_button.grid(row=2, column=0, pady=10)
		self.apply_button = tk.Button(self, text="Apply", width=10, command=self.save_work_dirs) # pass the function as thread in order to prevent the app from freezing
		self.apply_button.grid(row=2, column=1, pady=10)

	def save_work_dirs(self):
		"""
		Description
		"""
		master_progs_dir_path = self.master_progs_dir_entry.get()
		res_progs_dir_path = self.res_progs_dir_entry.get()
		sp.save_work_dirs(master_progs_dir_path, res_progs_dir_path)


class Page(tk.Frame):
	"""
	Description
	"""
	def __init__(self, container_frame, root):
		"""
		__init__() method defines those widgets that never change through the whole program
		"""
		tk.Frame.__init__(self, container_frame) # tk.Frame is used instead of super(), as tkinter classes are old
		self.root = root

	def page_setup(self, *args, **kwargs):
		pass

	def run(self, *args, **kwargs):
		pass

	def back_method(self):
		pass

	def next_method(self):
		pass


class SelectModePage(Page):
	"""
	Description
	"""
	def __init__(self, container_frame, root):
		super().__init__(container_frame, root)

	def page_setup(self):
		"""
		Create and grid the SelectModePage widgets and eventually set the root (title, buttonl, labels...)
		"""
		inp_mode = tk.StringVar()
		create_manual_rb = tk.Radiobutton(self, text="Create Manual", variable=inp_mode, value="create_manual")
		update_rb = tk.Radiobutton(self, text="Update", variable=inp_mode, value="update")
		create_manual_rb.grid(row=0, column=0, padx=10, pady=4)
		update_rb.grid(row=1, column=0, padx=10, pady=4)
		self.root.root_setup(head_text="Select Mode", next_method=self.next_method, next_method_args=[inp_mode], back_state=tk.DISABLED, next_state=tk.NORMAL)

	#@try_decorator
	def next_method(self, inp_mode):
		# Set the global variable hp.mode
		hp.mode = inp_mode.get()
		self.root.show_page(InitializationPage)


class InitializationPage(Page):
	"""
	In this page the user set the tool name and reference family
	"""
	def __init__(self, container_frame, root):
		super().__init__(container_frame, root)

	def page_setup(self):
		"""
		Create and grid the InitializationPage widgets and eventually set the root (title, buttonl, labels...)
		"""
		if hp.mode == "create_manual":
			hp.InitializationPage.constant_page_setup(self) # this must be inside the if loop, otherwise the setup is performed anyway, even if an exception is raised
			tool_name_label = tk.Label(self, text="Tool Name: ")
			tool_name_label.grid(row=1, column=0, padx=4, pady=4)
			self.tool_name_entry = tk.Entry(self, width=34)
			self.tool_name_entry.grid(row=1, column=1, padx=4, pady=4)
			self.browse_butt.config(command=lambda: threading.Thread(target=hp.InitializationPage.decorated_askdirectory(self, common.master_progs_dir)).start())
			# Constant root setup (independent from the selected mode)
			self.root.root_setup(head_text="Initialization Page", back_method=self.back_method,\
			next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)
		else:
			raise ValueError("Mode not supported yet")

	#@try_decorator
	def next_method(self):
		self.root.show_page(InputDataPage)
		# Set the global variable hp.res_prog_name
		hp.res_prog_name = self.tool_name_entry.get()

	#@try_decorator
	def back_method(self):
		# Set the global variable hp.mode
		hp.mode = None
		self.root.show_page(SelectModePage)


class InputDataPage(Page):
	"""
	This page allow the user to enter input data
	"""
	def __init__(self, container_frame, root):
		super().__init__(container_frame, root)

	def page_setup(self):
		"""
		Description
		"""
		try:
			# Set the global variable hp.config_data
			hp.config_data = cdp.ConfigData(hp.fam_dir_path)
		except TypeError:
			raise ValueError("Select a folder")
		hp.InputDataPage.grid_gui_data_entries(self)
		self.root.root_setup(head_text="Input Data Page", back_method=self.back_method,\
		next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)

	#@try_decorator
	def next_method(self):
		if hp.mode == "create_manual":
			# Set the global variable hp.raw_inp_data
			hp.raw_inp_data = hp.config_data.get_gui_raw_data(self)
			# Save input data inside config_data.input_df
			hp.config_data.save_input_data(hp.raw_inp_data)
			self.root.show_page(CreateProgramPage)
		else:
			raise ValueError("Mode not supported yet")

	#@try_decorator
	def back_method(self):
		# Set the global variable hp.fam_dir_path
		hp.fam_dir_path = None
		self.root.show_page(InitializationPage)


class CreateProgramPage(Page):
	"""
	Description
	"""
	def __init__(self, container_frame, root):
		super().__init__(container_frame, root)

	def page_setup(self):
		"""
		Description
		"""
		self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		next_method=self.next_method, back_state=tk.DISABLED, next_state=tk.DISABLED)
		self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
		self.progress_bar.grid(row=1, column=2, padx=40, pady=40)

	def run(self):
		"""
		This code runs while the CreateProgramPage is displayed
		"""
		# Set diameter value
		hp.config_data.set_diam_val()
		# Select the master program and copy it to the result directory
		res_prog = hp.CreateProgramPage.get_res_prog()

		with res_prog:
			# 1) Value scaling
			res_prog.scale_tool(hp.config_data.diam_name, hp.config_data.diam_val)
			self.progress_bar['value']=20
			# 2) update values update
			hp.config_data.update_input_data(res_prog)
			self.progress_bar['value']=40
			# 3) Relationships update
			hp.config_data.update_relationships_data(res_prog)
			self.progress_bar['value']=70
			# 4) Function values update
			hp.config_data.update_function_data(res_prog)
			self.progress_bar['value']=100

		self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		next_method=self.next_method, next_state=tk.NORMAL, back_state=tk.NORMAL)
		self.root.comm_label_write("Program created!")

	#@try_decorator
	def next_method(self):
		self.root.show_page(SelectModePage)

	#@try_decorator
	def back_method(self):
		# Set the global variable hp.fam_dir_path
		hp.raw_inp_data = None
		self.root.show_page(InputDataPage)

	# def configure_root_and_next_page(self):
	# 	"""
	# 		this function has to be called after the user has chosen the family, in order to set up the parameter entries for the following page 
	# 	"""

		# self.root.comm_label.config(text="")
		# self.root.head_label.config(text=page_frame.head_text)
		# self.root.back_button.config(command=lambda: threading.Thread(target=self.root.show_frame(InsertParametersFrame).start(), state=page_frame.back_butt_state)
		# self.root.next_button.config(command=lambda: threading.Thread(target=page_frame.confirm_function).start(), state=page_frame.confirm_butt_state)

	# 	insert_params_frame = self.root.frames[InsertValuesPage]
	# 	self.root.frames[InsertParametersFrame].head_text = "Input Parameters Page, Family: " + common.fam_name + ", Name: " + common.tool_name
	# 	# Forget all the previously istantiated widgets
	# 	try:
	# 		for descr_label, entry in zip(self.root.frames[InsertValuesPage].descr_label_list, self.root.frames[InsertParametersFrame].entry_list):
	# 			descr_label.grid_forget()
	# 			entry.grid_forget()
	# 	except AttributeError:
	# 		pass # if an AttributeError is raised, it means no widget needs to be reset

	# 	# get a list with all the input descriptions, with the same order of the input values
	# 	insert_params_frame.descr_list = app.InsertParameters.get_params_descr()

	# 	# get the number of input parameters
	# 	insert_params_frame.params_num = len(insert_params_frame.descr_list)

	# 	# create a list with all the labels containing input descriptions
	# 	insert_params_frame.descr_label_list = [tk.Label(insert_params_frame, text=descr, width=20) for descr in insert_params_frame.descr_list]

	# 	# create a list of entries (its length is equal to descr_list)
	# 	insert_params_frame.entry_list = [tk.Entry(insert_params_frame, width=20) for i in range(insert_params_frame.params_num)]

	# 	# create an entry box and its description for each input parameters
	# 	for descr_label, entry, i in zip(insert_params_frame.descr_label_list, insert_params_frame.entry_list, range(insert_params_frame.params_num)):

	# 		descr_label.grid(row=i, column=0)

	# 		entry.grid(row=i, column=1)

	# back_function and confirm_function are to be passed to the back and confirm buttons
# 	def back_method(self):
# 		pass

# 	#@try_decorator
# 	def next_method(self):
# 		"""
# 			This method is associated to the confirm button, it saves the user inputs into common variables
# 			and get other common variables based on those
# 		"""
# 		fam_name = self.fam_listbox.get(tk.ANCHOR)
# 		tool_name = self.tool_name_entry.get()
# 		app.Initialize.get_fam_dependent_vars()
# 		self.configure_insert_params_frame()
# 		self.root.comm_label.config(text="")
# 		self.root.show_frame(InsertParametersFrame)


# class InsertParametersFrame(tk.Frame):

# 	def __init__(self, container_frame, root):

# 		# tk.Frame is used instead of super(), as tkinter classes are old
# 		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

# 		# save the root in object variable
# 		self.root = root

# 		self.back_butt_state = tk.NORMAL

# 		self.confirm_butt_state = tk.NORMAL


# 	def create_program(self):

# 		self.root.comm_label.config(text='creating the program...')

# 		# function that creates the program, threaded in order to prevent the application from freezing
# 		app.CreateProgram.run()

# 		self.root.comm_label.config(text='program created!')


# 	# back_function and confirm_function are to be passed to the back and confirm buttons
# 	def back_function(self):

# 		self.root.show_frame(InitializeFrame)


# 	#@try_decorator
# 	def confirm_function(self):

# 		input_vals = []

# 		for i, entry in enumerate(self.entry_list):

# 			input_val = float(entry.get())

# 			input_vals.append(input_val)

# 		app.InsertParameters.save_input_params(input_vals)

# 		self.root.show_frame(CreateProgramFrame)

# 		# the create program process is triggered when the confirm button of the previous page is pushed
# 		self.create_program()


# class CreateProgramFrame(tk.Frame):

# 	def __init__(self, container_frame, root):

# 		# tk.Frame is used instead of super(), as tkinter classes are old
# 		tk.Frame.__init__(self, container_frame) # instantiate itself inside the container frame (in the root)

# 		# save the root in object variable
# 		self.root = root

# 		# features to be passed to the root template frame
# 		self.head_text = "Create Program Page"

# 		self.back_butt_state = tk.NORMAL

# 		self.confirm_butt_state = tk.NORMAL


# 	# back_function and confirm_function are to be passed to the back and confirm buttons
# 	def back_function(self):

# 		self.root.show_frame(InsertParametersFrame)


# 	#@try_decorator
# 	def confirm_function(self):

# 		self.root.show_frame(InitializeFrame)


def main():
	app = App() # instantiate root
	app.mainloop()