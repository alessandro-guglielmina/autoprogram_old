import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import threading
import os
from pathlib import Path
import logging

from autoprogram import common
from autoprogram import helper as hp
from autoprogram import settingsparser as sp
from autoprogram import configdataparse as cdp
from autoprogram.openvgp import vgpio

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("gui_log")
DEFAULT_MODE = "create_manual"


class App(tk.Tk):
	"""
	Description
	"""
	def __init__(self, *args, **kwargs):
		tk.Tk.__init__(self, *args, **kwargs) # tk.Tk.__init__() used in place of super().__init__()
		self.wm_title(common.root_header)
		self.geometry('600x580')
		# Create a menu and its cascades
		root_menu = tk.Menu(self)
		self.config(menu=root_menu)
		file_menu = tk.Menu(root_menu, tearoff=False)
		root_menu.add_cascade(label="File",  menu = file_menu)
		file_menu.add_command(label="Settings", command=self.show_settings_window)
		file_menu.add_command(label="Exit", command=self.quit)
		# The following widgets get their features from the specific page
		# create an heading
		self.head_label = tk.Label(self, width=70, height=3)
		self.head_label.grid(row=0, column=0, columnspan=3)
		# Create the container of the page frames, it's a frame inside the root
		# (it's always the same frame because it's the one in the root)
		# Its size is set to be always the same, regardless what's inside
		self.page_container_frame = tk.Frame(self, height=400, highlightbackground="black", highlightthickness=1)
		self.page_container_frame.grid(sticky="nswe", padx=10, columnspan=3) # set fixed size
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
			page_frame.grid(row=0, column=0)

	def root_setup(self, head_text=None, back_method=None, back_method_args=None, back_state=None, next_method=None, next_method_args=None, next_state=None):
		"""
		This method configures the root frame (title and navigation buttons), if arguments are not passed no action is performed (things remain as before)
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
		This method is used either when the Next or the Back button is pushed,
		it selects the page, then triggers the page_setup() method, then perform what's inside the
		run() method (if any)
		"""
		try:
			self.comm_label_write("")
			page = self.pages[page_name]
			page.page_setup(*args, **kwargs)
			page.tkraise()
			page.run(*args, **kwargs)
		except ValueError as ve:
			self.root_setup(next_state=tk.NORMAL, back_state=tk.NORMAL)
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
	In this page the user select te mode
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
		inp_mode.set(DEFAULT_MODE) # DEFAULT_MODE (global variable) mode by default
		create_manual_rb.grid(row=0, column=0, columnspan=3)
		update_rb.grid(row=1, column=0, columnspan=3)
		self.root.root_setup(head_text="Select Mode", next_method=self.next_method, next_method_args=[inp_mode], back_state=tk.DISABLED, next_state=tk.NORMAL)

	@hp.try_decorator
	def next_method(self, inp_mode):
		# Set the global variable hp.mode
		hp.mode = inp_mode.get()
		hp.forget_all_widgets(self)
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
			LOGGER.info("Setting the initialization page in create_manual mode")
			hp.InitializationPage.constant_page_setup(self) # this must be inside the if loop, otherwise the setup is performed anyway, even if an exception is raised
			self.tool_name_label = tk.Label(self, text="Tool Name: ")
			self.tool_name_label.grid(row=1, column=0, padx=4, pady=4)
			self.tool_name_entry = tk.Entry(self, width=34)
			self.tool_name_entry.grid(row=1, column=1, padx=4, pady=4)
			self.browse_butt.config(command=lambda: threading.Thread(target=hp.InitializationPage.set_fam_dir_path(self, common.master_progs_dir)).start())
			# Constant root setup (independent from the selected mode)
			self.root.root_setup(head_text="Initialization Page: Create Manual Mode", back_method=self.back_method,\
			next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)
		elif hp.mode == "update":
			LOGGER.info(f"Getting the user input data")
			hp.InitializationPage.constant_page_setup(self) # this must be inside the if loop, otherwise the setup is performed anyway, even if an exception is raised
			self.browse_butt.config(command=lambda: threading.Thread(target=hp.InitializationPage.set_fam_dir_path(self, common.master_progs_dir)).start())
			# Constant root setup (independent from the selected mode)
			self.root.root_setup(head_text="Initialization Page: Update Mode", back_method=self.back_method,\
			next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)
		else:
			raise ValueError("Mode not supported yet")

	@hp.try_decorator
	def next_method(self):
		hp.InitializationPage.set_config_data()
		hp.forget_all_widgets(self)
		if hp.mode == "create_manual":
			# Set the global variable hp.res_prog_name
			hp.res_prog_name = self.tool_name_entry.get()
			self.root.show_page(InputDataPage)
		elif hp.mode == "update":
			self.root.show_page(CreateProgramPage)
		else:
			raise ValueError(f"No such a mode{hp.mode}")

	def back_method(self):
		# Set the global variable hp.mode
		hp.mode = None
		hp.forget_all_widgets(self)
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
		hp.InputDataPage.grid_gui_data_entries(self)
		self.root.root_setup(head_text="Input Data Page", back_method=self.back_method,\
		next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)

	@hp.try_decorator
	def next_method(self):
		if hp.mode == "create_manual":
			hp.forget_all_widgets(self)
			# Set the global variable hp.raw_inp_data
			hp.raw_inp_data = hp.InputDataPage.get_gui_raw_data(self,hp.config_data.inp_df.data_name)
			# Save raw input data inside hp.config_data.inp_df
			hp.config_data.save_raw_inp_data(hp.raw_inp_data)
			self.root.show_page(CreateProgramPage)
		else:
			raise ValueError("This page cannot be called in any mode but create_manual")

	def back_method(self):
		# Set the global variable hp.fam_dir_path
		hp.fam_dir_path = None
		hp.forget_all_widgets(self)
		self.root.show_page(InitializationPage)


class CreateProgramPage(Page):
	"""
	Description
	"""
	def __init__(self, container_frame, root):
		super().__init__(container_frame, root)

	def page_setup(self):
		"""
		This code runs before the CreateProgramPage is displayed
		"""
		self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		next_method=self.next_method, back_state=tk.DISABLED, next_state=tk.DISABLED)
		self.progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode="determinate")
		self.progress_bar.grid(row=0, column=1, padx=4, pady=40)

	def run(self):
		"""
		This code runs while the CreateProgramPage is displayed
		"""
		self.progress_bar['value']=10
		# process to create a program
		if hp.mode == "create_manual":
			# Set diameter value
			hp.CreateProgramPage.set_diam_val()
			self.progress_bar['value']=20
			# Select the master program and copy it to the result directory
			#res_prog = hp.CreateProgramPage.get_res_prog()
			hp.CreateProgramPage.set_low_up_res_prog_paths()
			self.progress_bar['value']=40
			with hp.res_prog as res_prog:
				# 1) Value scaling
				if hp.low_prog and hp.up_prog: # tool scaling make sense only if a result program isn't a master itself (i.e. hp.low_prog and hp.up_prog haven't been set to None)
					hp.CreateProgramPage.scale_tool()
				self.progress_bar['value']=50
				# 2) update input values
				hp.config_data.update_input_data(res_prog)
				self.progress_bar['value']=70
				# 3) Relationships update
				hp.config_data.update_relationships_data(res_prog)
				self.progress_bar['value']=90
				# # 4) Function values update
				hp.config_data.update_function_data(res_prog)
		# process to update many programs in a directory
		elif hp.mode == "update":
			update_prog_path_list = hp.CreateProgramPage.get_update_prog_list()
			for update_prog_path in update_prog_path_list:
				LOGGER.info(f"Updating the program at {update_prog_path}")
				with vgpio.VgpProgram(update_prog_path, hp.config_data.diam_name) as update_prog:
					# 1) Relationships update
					hp.config_data.update_relationships_data(update_prog)
					# 2) Function values update
					hp.config_data.update_function_data(update_prog)
		self.progress_bar['value']=100

		self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		next_method=self.next_method, next_state=tk.NORMAL, back_state=tk.NORMAL)
		self.root.comm_label_write("Program created successfully!")
		LOGGER.info("Program created succesfully!")
		if vgpio.not_updated_names:
			LOGGER.warning("Not updated data names:")
			[LOGGER.warning(name) for name in vgpio.not_updated_names]


	@hp.try_decorator
	def next_method(self):
		# Set the global variable vgpio.not_updated_names
		vgpio.not_updated_names =[]
		hp.forget_all_widgets(self)
		self.root.show_page(SelectModePage)

	def back_method(self):
		# Set the global variable vgpio.not_updated_names
		vgpio.not_updated_names =[]
		hp.forget_all_widgets(self)
		if hp.mode == "create_manual":
			# Set the global variable hp.raw_inp_data
			hp.raw_inp_data = None
			self.root.show_page(InputDataPage)
		else:
			self.root.show_page(InitializationPage)


def main():
	app = App() # instantiate root
	app.mainloop()