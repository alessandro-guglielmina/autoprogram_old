import pandas as pd
import tkinter as tk
import shutil
import threading
import os
from pathlib import Path
from tkinter import filedialog

from autoprogram import configdataparse as cdp
from autoprogram.openvgp import vgpio
from autoprogram import common

# fam_dir_path = None
# res_prog_name = None
# config_data = None

def try_decorator(target_method):
	"""
	This decorator is added to any confirm function, in order to print the error (if any) on the communication label
	"""
	def wrapper_function(*args, **kwargs):
		try:
			args[0].root.comm_label_write("")
			return target_method(*args, **kwargs)
		except ValueError as ve:
			args[0].root.comm_label_write(ve) # args[0] is self, i.e. the frame object (the page)
	return wrapper_function

# @try_decorator
# def decorated_askdirectory(initialization_page_frame, initialdir):
# 	"""
# 	Description
# 	"""
# 	if not os.path.isdir(initialdir):
# 		raise ValueError("Specified master program directory doesn't exist")
# 	global fam_dir_path
# 	fam_dir_path = Path(filedialog.askdirectory(initialdir=initialdir))
# 	self.browse_entry.insert(0, fam_dir_path.as_posix())

# class SelectModePage(object):
# 	@staticmethod
# 	def page_setup(self):
# 		# Constant root setup
# 		# The root must be set up after the "mode" variable has been created (called in self.next_method())
# 		# Constant frame setup
# 		inp_mode = tk.StringVar()
# 		create_manual_rb = tk.Radiobutton(self, text="Create Manual", variable=inp_mode, value="create_manual")
# 		update_rb = tk.Radiobutton(self, text="Update", variable=inp_mode, value="update")
# 		create_manual_rb.grid(row=0, column=0, padx=10, pady=4)
# 		update_rb.grid(row=1, column=0, padx=10, pady=4)
# 		self.root.root_setup(head_text="Select Mode", next_method=self.next_method, next_method_args=[inp_mode], back_state=tk.DISABLED, next_state=tk.NORMAL)

# 	@staticmethod
# 	# @try_decorator
# 	def next_method(self, inp_mode, InitializationPage):
# 		global mode
# 		mode = inp_mode.get()
# 		self.root.show_page(InitializationPage)

class InitializationPage(object):
	@staticmethod
	def constant_page_setup(initialization_page_frame):
		"""
		Constant frame setup
		The selected directory can be either the family directory
		(create manual mode) or the directory containing the files
		we want to change (update mode)
		"""
		browse_label = tk.Label(initialization_page_frame, text="Select Directory: ", width=16)
		browse_label.grid(row=0, column=0, padx=4, pady=4)
		initialization_page_frame.browse_entry = tk.Entry(initialization_page_frame, width=34)
		initialization_page_frame.browse_entry.grid(row=0, column=1, padx=4, pady=4)
		initialization_page_frame.browse_butt = tk.Button(initialization_page_frame, text="Browse", width=10)
		initialization_page_frame.browse_butt.grid(row=0, column=2, padx=4, pady=4)

	@try_decorator
	def decorated_askdirectory(initialization_page_frame, initialdir):
		"""
		Description
		"""
		if not os.path.isdir(initialdir):
			raise ValueError("Specified master program directory doesn't exist")
		global fam_dir_path
		fam_dir_path = Path(filedialog.askdirectory(initialdir=initialdir))
		initialization_page_frame.browse_entry.insert(0, fam_dir_path.as_posix())

	# @staticmethod
	# def page_setup(self):
	# 	"""
	# 	SelectModePage setup for the root and the frame
	# 	"""
	# 	if mode == "create_manual":
	# 		InitializationPage.constant_page_setup(self) # this must be inside the if loop, otherwise the setup is performed anyway, even if an exception is raised
	# 		tool_name_label = tk.Label(self, text="Tool Name: ")
	# 		tool_name_label.grid(row=1, column=0, padx=4, pady=4)
	# 		self.tool_name_entry = tk.Entry(self, width=34)
	# 		self.tool_name_entry.grid(row=1, column=1, padx=4, pady=4)
	# 		self.browse_butt.config(command=lambda: threading.Thread(target=decorated_askdirectory(self, common.master_progs_dir)).start())
	# 		# Constant root setup (independent from the selected mode)
	# 		self.root.root_setup(head_text="Initialization Page", back_method=self.back_method,\
	# 		next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)
	# 	else:
	# 		raise ValueError("Mode not supported yet")

	# @staticmethod
	# #@try_decorator
	# def next_method(self, InputDataPage):
	# 	self.root.show_page(InputDataPage)
	# 	global res_prog_name
	# 	res_prog_name = self.tool_name_entry.get()

	# @staticmethod
	# #@try_decorator
	# def back_method(self, SelectModePage):
	# 	global mode
	# 	mode = None
	# 	self.root.show_page(SelectModePage)

class InputDataPage(object):
	# @staticmethod
	# def page_setup(self):
	# 	"""
	# 	Description
	# 	"""
	# 	try:
	# 		global config_data
	# 		config_data = cdp.ConfigData(fam_dir_path)
	# 	except TypeError:
	# 		raise ValueError("Select a folder")
	# 	InputDataPage.grid_gui_data_entries(self)
	# 	self.root.root_setup(head_text="Input Data Page", back_method=self.back_method,\
	# 	next_method=self.next_method, back_state=tk.NORMAL, next_state=tk.NORMAL)

	@staticmethod
	def grid_gui_data_entries(input_data_page):
		"""
		Description
		"""
		for i, (inp_data_name, inp_data_descr) in enumerate(zip(config_data.input_df.data_name, config_data.input_df.data_descr)):
			inp_data_entry = tk.Entry(input_data_page, width=20, name=cdp.ConfigData.to_widget_name(inp_data_name))
			inp_data_label = tk.Label(input_data_page, width=20, text=inp_data_descr)
			inp_data_entry.grid(row=i, column=1, padx=4, pady=4)
			inp_data_label.grid(row=i, column=0, padx=4, pady=4)

	# @staticmethod
	# #@try_decorator
	# def next_method(self, CreateProgramPage):
	# 	# Acquire input data
	# 	if mode == "create_manual":
	# 		global raw_inp_data
	# 		raw_inp_data = config_data.get_gui_raw_data(self)
	# 		# Save input data inside config_data.input_df
	# 		config_data.save_input_data(raw_inp_data)
	# 		self.root.show_page(CreateProgramPage)
	# 	else:
	# 		raise ValueError("Mode not supported yet")

	# @staticmethod
	# #@try_decorator
	# def back_method(self, InitializationPage):
	# 	global fam_dir_path
	# 	fam_dir_path = None
	# 	self.root.show_page(InitializationPage)

class CreateProgramPage(object):
	"""
		In this page the program is updated with data from the user and from the tables
		"""
	# @staticmethod
	# def get_res_prog():
	# 	"""
	# 	This method select the master program based on the excel sheet
	# 	"""
	# 	master_prog_name = config_data.get_master_prog_name(config_data.diam_val)
	# 	master_prog_path = fam_dir_path.joinpath(master_prog_name)
	# 	res_prog_path = common.res_progs_dir.joinpath(res_prog_name + common.vgp_suffix)
	# 	try:
	# 		shutil.copyfile(master_prog_path, res_prog_path) # copy the master program file to the result directory
	# 	except FileNotFoundError as fnfe:
	# 		raise ValueError(f"No such result directory: {common.res_progs_dir}")
	# 	res_prog = vgpio.VgpProgram(res_prog_path, config_data.diam_name)
	# 	return res_prog
	@staticmethod
	def set_diam_val():
		"""
		This method set the variable self.diam_val to the diameter value inserted by the user
		"""
		filt = config_data.input_df.data_name == config_data.diam_name
		# Set the global variable diam_val
		global diam_val
		diam_val = float(config_data.input_df.loc[filt, "inp_val"].values[0])

	@staticmethod
	def set_low_up_res_prog_paths():
		"""
		This method sets the lower, upper and result program paths as global variables
		"""
		def get_diam_val(prog_path):
			"""
			This method returns the diameter value of the program path passed as argument
			"""
			with vgpio.VgpProgram(prog_path, config_data.diam_name) as prog:
				return prog.initial_diam

		prog_paths =pd.Series(fam_dir_path.glob('*' + common.vgp_suffix))
		prog_diam_vals = pd.Series(prog_paths.apply(get_diam_val))
		fam_progs_df = pd.DataFrame({"path": prog_paths, "diam_val": prog_diam_vals})
		# Enclosing and master programs selection
		# Lower program
		low_filt = fam_progs_df["diam_val"] <= diam_val
		low_progs_df = fam_progs_df.loc[low_filt, :].reset_index(drop=True)
		low_prog_path = low_progs_df.loc[(low_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		# Upper program
		up_filt = fam_progs_df["diam_val"] >= diam_val
		up_progs_df = fam_progs_df.loc[up_filt, :].reset_index(drop=True)
		up_prog_path = up_progs_df.loc[(up_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		# Master program
		master_prog_path = fam_progs_df.loc[(fam_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		# Copy the master program to the result program path
		res_prog_path = common.res_progs_dir.joinpath(res_prog_name + common.vgp_suffix)
		try:
			shutil.copyfile(master_prog_path, res_prog_path) # copy the master program file to the result directory
		except FileNotFoundError as fnfe:
			raise ValueError(f"No such result directory: {common.res_progs_dir}")

		global low_prog, up_prog, res_prog
		low_prog, up_prog, res_prog = vgpio.VgpProgram(low_prog_path, config_data.diam_name), vgpio.VgpProgram(up_prog_path, config_data.diam_name), vgpio.VgpProgram(res_prog_path, config_data.diam_name)

	# @staticmethod
	# def page_setup(self):
		# """
		# Description
		# """
		# self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		# next_method=self.next_method, back_state=tk.DISABLED, next_state=tk.DISABLED)
		# progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=200, mode='determinate')
		# progress_bar.grid(row=1, column=2, padx=40, pady=40)
		# prog_created_label = tk.Label(self, width=20, text="Program created!")
		# prog_created_label.grid(row=2, column=2, padx=40, pady=40)
		# # Set diameter value
		# config_data.set_diam_val()
		# # Select the master program and copy it to the result directory
		# res_prog = CreateProgramPage.get_res_prog()

		# with res_prog:
		# 	# 1) Value scaling
		# 	res_prog.scale_tool(hp.config_data.diam_name, hp.config_data.diam_val)
		# 	progress_bar['value']=20
		# 	# 2) update values update
		# 	hp.config_data.update_input_data(res_prog)
		# 	progress_bar['value']=40
		# 	# 3) Relationships update
		# 	hp.config_data.update_relationships_data(res_prog)
		# 	progress_bar['value']=70
		# 	# 4) Function values update
		# 	hp.config_data.update_function_data(res_prog)
		# 	progress_bar['value']=100

		# self.root.root_setup(head_text="Create Program Page", back_method=self.back_method,\
		# next_method=self.next_method, next_state=tk.NORMAL)

	# @staticmethod
	# #@try_decorator
	# def next_method(self, SelectModePage):
	# 	self.root.show_page(CreateProgramPage)

	# @staticmethod
	# #@try_decorator
	# def back_method(self, InputDataPage):
	# 	global raw_inp_data
	# 	raw_inp_data = None
	# 	self.root.show_page(InputDataPage)

##########################################################################################à

# # from pathlib import Path
# # import glob
# # import os
# # import time
# # import sqlite3
# # import numpy as np
# # import pandas as pd
# # import shutil
# # from itertools import compress
# # import re
# # import math
# import tkinter as tk

# # from autoprogram import common
# # from autoprogram import wbmodule as wbm
# # from autoprogram import progmodule as pm

# pd.options.mode.chained_assignment = None  # default='warn'


# class SelectFamily(object):
# 	"""
# 	Description
# 	"""
# 	@staticmethod
# 	def get_fam_names():

# 		try:

# 			return [str(fam_dir.name) for fam_dir in common.Variables.master_progs_dir.iterdir() if fam_dir.is_dir()]

# 		except FileNotFoundError:

# 			raise ValueError(f'No such a master programs directory: {common.Variables.master_progs_dir.__str__()}')


# 	# Get common data dependent on the chosen family
# 	@staticmethod
# 	def get_fam_dependent_vars():

# 		# assign this global variables after pushing the confirm button and not while starting the application  (even if it doesn't depend on the family choice),
# 		# otherwise a wrong master programs directory path would make the application crash!!!
	

# 		# get family directory
# 		fam_prog_dir = Path(common.Variables.master_progs_dir/common.Variables.fam_name)

# 		# get the master programs list
# 		common.Variables.fam_master_list = list(fam_prog_dir.glob('*' + common.Variables.vgp_suffix))

# 		# assign the configuration file
# 		common.Variables.config_file_wb =  wbm.WorkBook(Path(fam_prog_dir/common.Variables.config_file_wb_filename))

# 		# get the parameter name associated with the diameter (needed to select the master program)
# 		common.Variables.diam_name = common.Variables.config_file_wb.wb[common.Variables.diam_name_sh_name]['diam_name'][0]

# 		# get the common data from the configuration file
# 		common.Variables.data = cls.get_common_data()


# 	# with this method, all the common data (addresses, relations, descriptions, ...) are collected, depending on the selected family
# 	@staticmethod
# 	def get_common_data():
# 		# this function gets the addresses and the descriptions of the parameters that has to be configured (by user input or relationship)

# 		# get val_names and rels from the configuration values workbook
# 		config_val_names = common.Variables.config_file_wb.get_whole_column(common.Variables.config_vals_sh_name,'val_name')

# 		config_rels = common.Variables.config_file_wb.get_whole_column(common.Variables.config_vals_sh_name, 'rel')

# 		config_val_addr = common.Variables.values_database_wb.get_values_multi_ids(common.Variables.database_sh_name, 'val_name', 'val_addr', config_val_names)

# 		config_val_descr = common.Variables.values_database_wb.get_values_multi_ids(common.Variables.database_sh_name, 'val_name', 'val_descr', config_val_names)

# 		# Sect-percs and vals are set to None
# 		config_sect_percs = np.array([None for i in config_val_names])

# 		config_vals = np.array([None for i in config_val_names])

# 		# Build the common data DataFrame
# 		res = pd.DataFrame({'val_name': pd.Series(config_val_names, dtype='str'),

# 		             		'rel': pd.Series(config_rels, dtype='str'),

# 		             		'val_addr': pd.Series(config_val_addr, dtype='str'),

# 		             		'val_descr': pd.Series(config_val_descr, dtype='str'),

# 		             		'sect_perc': pd.Series(config_sect_percs, dtype='object'),

# 		             		'val': pd.Series(config_vals, dtype='object')})


# 		if not common.Variables.diam_name in res.val_name.tolist():

# 			raise ValueError('Diameter value missing among the configuration values.')
			
# 		return res # DataFrame('val_addr', 'val_type', 'val_descr')


# # This is the program phase in which the user defines the geometrical parameter of the tool
# class InsertParameters(object):

# 	# get a list with all the input descriptions, with the sam order of the input values
# 	@classmethod
# 	def get_params_descr(cls):

# 		# Create printing list
# 		all_rel = common.Variables.data.rel.to_numpy()

# 		all_descr = common.Variables.data.val_descr.to_numpy()

# 		# print(all_rel)
# 		# print(all_descr)

# 		inp_vals_filter = np.equal(all_rel, None) # input values are those not having any relationship with others

# 		descr_list = all_descr[inp_vals_filter]

# 		# print(descr_list)

# 		return descr_list # [descr1, descr2, ...]

# 	@classmethod
# 	def save_input_params(cls, input_vals): # (cls, [inp_val1, inp_val2, ...])

# 		input_vals = [[i] for i in input_vals] # makes all the values lists (iterables)

# 		# Input values have no relation, this feature is used to reference them among common data
# 		common.Variables.data.loc[common.Variables.data.rel.isnull(), 'val'] = input_vals # write user input values in common.Variables.data (isnull() needed to reference None values)

# 		# Save the diameter value in a common variable in order to be easily accessed while choosing the master program
# 		common.Variables.diam = common.Variables.data.loc[common.Variables.data.val_name == common.Variables.diam_name, 'val'].values[0][0] # dereference all values with .values as ndarray and then with [0]


# # This is the program phase in which the program makes computation to get the result program
# class CreateProgram(object):

# 	@classmethod
# 	def run(cls):

# 		cls.select_master_prog()

# 		cls.scale_values()

# 		cls.update_input_values()

# 		cls.apply_relations()

# 		cls.apply_functions()


# 	# In this step the rogram chooses the master program, i.e. the one having the closest diameter
# 	@classmethod
# 	def select_master_prog(cls):

# 		diam = common.Variables.diam

# 		diam_arr = np.empty((1, 0), dtype = float)

# 		fam_progs = common.Variables.fam_master_list

# 		for i in fam_progs:

# 			prog_path_i = Path(i)

# 			# Open a context manager with the db composition of prog_i+ to open a connection with the vgp program (database)
# 			with  pm.VgpProg(prog_path_i) as prog_i:

# 				diam_i = prog_i.get_values_from_names([common.Variables.diam_name]).val.values[0] # float, DataFrame.val.values is a 1-sized numpy array

# 			diam_arr = np.append(diam_arr, diam_i)

# 		# Data to be sorted
# 		delta_diam = diam_arr - diam

# 		#fam_progs already assigned 
# 		data = pd.DataFrame({'diam': pd.Series(diam_arr, dtype= 'float'),

# 							'delta_diam': pd.Series(delta_diam, dtype= 'float'),

# 							'fam_progs': pd.Series(fam_progs, dtype= 'str')})

# 		# Separate positive and negative delta diameters data in two different DataFrames
# 		up = data.loc[data.delta_diam > 0, :]

# 		low = data.loc[data.delta_diam <= 0, :]

# 		# Absolute value of delta diameters (in-place operation)
# 		np.absolute(up.delta_diam.values, out = up.delta_diam.values)

# 		np.absolute(low.delta_diam.values, out = low.delta_diam.values)

# 		# If there isn't the upper program or the lower one, an error message is raised
# 		if up.delta_diam.values.size == 0 or low.delta_diam.values.size == 0:

# 			raise ValueError("No master programs for the selected diameter")

# 		else:

# 			pass

# 		# Sort data by delta diameter
# 		up.sort_values(by = ['delta_diam'], inplace = True, ignore_index = True) # change directly itself without producing a copy

# 		low.sort_values(by = ['delta_diam'], inplace = True, ignore_index = True)

# 		# Get upper and lower program filenames and diameters
# 		common.Variables.up_prog_filename = Path(up.fam_progs[0])

# 		common.Variables.low_prog_filename = Path(low.fam_progs[0])

# 		common.Variables.up_diam = up.diam[0]

# 		common.Variables.low_diam = low.diam[0]

# 		# Get the master program filename, i.e. the one having the closest diameter among up and low programs
# 		poss_master_progs = up[['delta_diam', 'fam_progs']][0:1].append(low[['delta_diam', 'fam_progs']][0:1])

# 		poss_master_progs.sort_values(by = 'delta_diam', inplace = True, ignore_index = True)

# 		master_prog_filename = poss_master_progs.fam_progs[0]

# 		# Generate target program filename
# 		partial_res_prog_filename = common.Variables.res_prog_dir.joinpath(common.Variables.tool_name)

# 		common.Variables.res_prog_filename = partial_res_prog_filename.with_suffix(common.Variables.vgp_suffix)

# 		try:

# 			# Copy the master program with the target program name (create the target program)
# 			shutil.copyfile(master_prog_filename, common.Variables.res_prog_filename)

# 			# Instantiate the result program object
# 			common.Variables.res_prog = pm.VgpProg(common.Variables.res_prog_filename)

# 		except FileNotFoundError:

# 			raise ValueError(f'No such a result program directory: {common.Variables.res_prog_dir.__str__()}')


# 	@classmethod
# 	def scale_values(cls):

# 		with common.Variables.res_prog as res_prog:

# 			 res_prog.scale_prog_values()


# 	# pdate input values first, so if an input value is read from the program while applying relations, it is up to date
# 	@classmethod
# 	def update_input_values(cls):

# 		with common.Variables.res_prog as res_prog:

# 			 res_prog.update_input_values()


# 	@classmethod	
# 	def apply_relations(self):

# 		for i, row in common.Variables.data.iterrows(): # row is the pd.Series corresponding to a specific row

# 			if row.rel is not None: # row.rel is a string

# 				arg_names = re.findall(r'\$(.*?)\$', row.rel) # get a list with all the arg names (strings between $$)

# 				with common.Variables.res_prog as res_prog:

# 					arg_vals = res_prog.get_values_from_names(arg_names) # return a DataFrame whose colimns are sect_perc and val of the values substituted in the relation

# 					arg_vals = arg_vals.val.to_list() # take only the val (that are np.arrays)

# 					arg_vals = [i[0] for i in arg_vals] # dereference the arrays, take only the value inside them

# 					rel_exp = 'val = ' + row.rel # added 'val = ' in order to assign the result of the expression in a variable, thus can be retrieved once exec has been executed (exec doesn't return anything)

# 					for arg_name, arg_val in zip(arg_names, arg_vals):

# 						rel_exp = re.sub(r'\${}\$'.format(arg_name), str(arg_val), rel_exp) # substitute the val names in the expression with their actual value, one at each for cycle

# 					local_dict = {}

# 					try:

# 						exec(rel_exp, globals(), local_dict)

# 					except SyntaxError:

# 						raise ValueError('Wrong syntax in the configuration values.')

# 					row.val = [local_dict['val']] # the value must be an iterable, thus we add parentheses

# 					res_prog.update_values_from_addr([row.val_addr],  pd.DataFrame([[row.sect_perc, row.val]], columns = ['sect_perc', 'val']))

# 			else:

# 				pass


# 	@classmethod	
# 	def apply_functions(self):

# 		funct_vals_sh_names = [common.Variables.funct_vals_1_sh_name, common.Variables.funct_vals_2_sh_name]

# 		funct_vals_sheets = []

# 		for funct_vals_sh_name in funct_vals_sh_names:

# 			try:

# 				funct_vals_sh =  common.Variables.config_file_wb.wb[funct_vals_sh_name] # DataFrame with the first page of function values

# 				funct_vals_sheets.append(funct_vals_sh)

# 			except KeyError:

# 				pass # function values sheets are not mandatory

# 		# parse function values sheets only if any
# 		if len(funct_vals_sheets) > 0:

# 			for funct_val_sheet in funct_vals_sheets:

# 				funct_arg_name = funct_val_sheet.columns[0] # takes the first column heading, i.e. the function argument (most times the tool diameter)

# 				with common.Variables.res_prog as res_prog: # context manager opening the program

# 					funct_arg_val = res_prog.get_values_from_names([funct_arg_name]).val[0][0] # take function argument value (i.e. the val component)

# 					diff = funct_val_sheet[funct_arg_name].astype(float).sub(funct_arg_val) # config file argument values - actual program value

# 					idx = diff[diff < 0].idxmax() # take the index of the gratest smaller argument value in the config file argument column

# 					funct_val_names = funct_val_sheet.columns[1:] # take all the headings but the first one (that is the argument value)

# 					funct_val_names = [i for i in funct_val_names if not ('UNNAMED' in i.upper())] # takes only the actual result values headings, not the empty colums (whose heading is imported as 'unnamed')

# 					columns = ['sect_perc', 'val']

# 					comp_funct_vals = pd.DataFrame(columns = columns, dtype = object) # complete function values (just to be updated in the program)

# 					for funct_val_name in funct_val_names:

# 						raw_funct_val = funct_val_sheet.loc[idx, funct_val_name] # take the raw text value from the spreadsheet

# 						try:

# 							funct_val = np.array(raw_funct_val.split(common.Variables.separator)).astype(float) # array of floats from the spreadsheet

# 							# convert m/s to mm/s if it's a cutting speed
# 							if 'SPEED' in funct_val_name.upper():

# 								funct_val = funct_val*1000

# 							# convert mm/min to mm/s if it's a feed rate
# 							if 'FEED' in funct_val_name.upper():

# 								funct_val = funct_val/60

# 							# otherwise the values are already correct
# 							else:

# 								pass

# 						except ValueError:

# 							raise ValueError(f'Wrong function value format in the function values sheet: column {funct_val_name}, row {idx}') # if there is some format error, raise a ValueError

# 						comp_funct_vals = comp_funct_vals.append({'sect_perc' : None, 'val' : funct_val}, ignore_index = True)

# 					res_prog.update_values_from_names(funct_val_names, comp_funct_vals)

# 		else:

# 			pass