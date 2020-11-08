from pathlib import Path
import glob
import os
import time
import sqlite3
import numpy as np
import pandas as pd
import shutil
from itertools import compress

from autoprogram import common
from autoprogram import uimodule as ui
from autoprogram import wbmodule as wbm
from autoprogram import progmodule as pm

pd.options.mode.chained_assignment = None  # default='warn'

# This class is the blueprint for all the positions (i.e. all the program phases)
class Position(object):

	prev_pos = None
	current_pos = None
	follow_pos = None

	@classmethod
	def activate(cls):
		print("The activate method isn't initialized in this is-a-position class.")
		sys.exit(1)

	@classmethod
	def select_position(cls):
		ch_list = ['confirm', 'repeat', 'move back']
		ch_ids = ['C', 'R', 'B']
		ch = ui.user_input(ch_list = ch_list, ch_ids = ch_ids)
		pos_select = ch[0]
		if (pos_select == 'confirm'):
			next_pos = cls.follow_pos
		elif (pos_select == 'repeat'):
			next_pos = cls.current_pos
		elif (pos_select == 'move back'):
			next_pos = cls.prev_pos
		return next_pos

# This is the first program step in which the information carrier is initialized with the familiy name (provided by the user)
class Initialize(Position):

	prev_pos = 'initialize'
	current_pos = prev_pos
	follow_pos = 'insert_parameters'

	@classmethod
	def activate(cls):
		try:
			cls.insert_preliminary_data()
			cls.get_fam_dependent_vars()
			cls.get_tool_type()
			cls.get_val_addr()
			cls.get_common_data()
			return cls.select_position()
		except Exception as e:
			print(e)
			return cls.current_pos

	# Get the family names from the family directories inside the master programs directory
	@classmethod
	def get_fam_names(cls):
		return [str(fam_dir.name) for fam_dir in common.Variables.master_progs_dir.iterdir() if fam_dir.is_dir()]

	# Get the family name from user
	@classmethod
	def insert_preliminary_data(cls):
		# Acquire tool name
		# common.Variables.tool_name = input('Insert tool name:\n>')
		common.Variables.tool_name = 'res_prog'
		# Create array containing all family names (string format)
		fam_name_list = cls.get_fam_names() # ['fam1', 'fam2', ...]
		# Select family
		ui.select_family(fam_name_list)

	# Get common data dependent on the chosen family
	@classmethod
	def get_fam_dependent_vars(cls):
		fam_prog_dir = Path(common.Variables.master_progs_dir/common.Variables.fam_name)
		common.Variables.fam_prog_list = list(fam_prog_dir.glob('*' + common.Variables.vgp_suffix))
		common.Variables.config_vals_wb =  wbm.WorkBook(Path(fam_prog_dir/common.Variables.config_vals_wb_filename))
		common.Variables.cutting_params_wb_path = wbm.WorkBook(Path(fam_prog_dir/common.Variables.cutting_params_wb_filename))

	# Get the tool type from the family name (which must contain the tool type, e.g. 'drill', 'mill', ...)
	@classmethod
	def get_tool_type(cls):
		if 'DRILL' in common.Variables.fam_name.upper():
			common.Variables.tool_type = 'drill'
		elif 'MILL' in common.Variables.fam_name.upper():
			common.Variables.tool_type = 'mill'
		elif 'REAMER' in Variables.fam_name.upper():
			common.Variables.tool_type = 'reamer'
		else:
			raise ValueError('No such a tool type.')
		ui.print_tool_type()

	# Get the common data needed in the following steps (val_name, rel, val_addr, val_descr, sect_perc, val)
	@classmethod
	def get_common_data(cls):
		common.Variables.data = wbm.get_common_data()

	# Initialize the names of some features, depending on the tool type
	@classmethod
	def get_val_addr(cls):

		# Update diam and flute names depending on file suffix and tool type
		if common.Variables.tool_type == 'drill':

			common.Variables.diam_addr = common.Variables.drill_diam_addr

		elif common.Variables.tool_type == 'mill':

			pass

		else:

			raise ValueError('No such a tool type.')


# This is the program phase in which the user defines the geometrical parameter of the tool
class InsertParameters(Position):

	prev_pos = 'initialize'
	current_pos = 'insert_parameters'
	follow_pos = 'create_program'

	@classmethod
	def activate(cls):
		cls.insert_parameter_values()
		cls.update_diam_val()
		return cls.select_position()

	# Write user inputs in the value column
	@classmethod
	def insert_parameter_values(cls):
		# Create printing list
		all_rel = common.Variables.data.rel.tolist()
		all_descr = common.Variables.data.val_descr.tolist()
		inp_vals_filt = [i == None for i in all_rel]
		descr_list = list(compress(all_descr, inp_vals_filt)) # use boolean indexing with lists
		print_list = [f'Enter {i}: ' for i in descr_list]
		# Get user input
		print('Insert parameters:\n')
		inp_vals = ui.user_input(cast = float, print_list = print_list)
		# Input values have no relation, this feature is used to reference them among common data
		common.Variables.data.loc[common.Variables.data.rel.isnull(), 'val'] = inp_vals # isnull() needed to reference None values

	# Save the diameter value in a common variable in order to be easily accessed while choosing the master program
	@classmethod
	def update_diam_val(cls):
		common.Variables.diam = common.Variables.data.loc[common.Variables.data.val_addr == common.Variables.diam_addr, 'val'].values[0] # dereference all values with .values as ndarray and then with [0]


# This is the program phase in which the program makes computation to get the result program
class CreateProgram(Position):

	prev_pos = 'insert_parameters'
	current_pos = 'create_program'
	follow_pos = 'end'

	@classmethod
	def activate(cls):
		cls.select_master_prog()
		cls.scale_values()
		cls.update_input_values()
		cls.apply_relations()
		return cls.select_position()

	# In this step the rogram chooses the master program, i.e. the one having the closest diameter
	@classmethod
	def select_master_prog(cls):
		diam = common.Variables.diam
		diam_arr = np.empty((1, 0), dtype = float)
		fam_progs = common.Variables.fam_prog_list
		for i in fam_progs:
			prog_path_i = Path(i)
			# Open a context manager with the db composition of prog_i+ to open a connection with the vgp program (database)
			with  pm.prog_select(prog_path_i) as prog_i:
				diam_i = prog_i.get_values_from_addr([common.Variables.diam_addr]).val.values[0] # float, DataFrame.val.values is a 1-sized numpy array
			diam_arr = np.append(diam_arr, diam_i)
		# Data to be sorted
		delta_diam = diam_arr - diam
		#fam_progs already assigned 
		data = pd.DataFrame({
							'diam': pd.Series(diam_arr, dtype= 'float'),
							'delta_diam': pd.Series(delta_diam, dtype= 'float'),
							'fam_progs': pd.Series(fam_progs, dtype= 'str')
							})
		# Separate positive and negative delta diameters data in two different DataFrames
		up = data.loc[data.delta_diam > 0, :]
		low = data.loc[data.delta_diam <= 0, :]
		# Absolute value of delta diameters (in-place operation)
		np.absolute(up.delta_diam.values, out = up.delta_diam.values)
		np.absolute(low.delta_diam.values, out = low.delta_diam.values)
		# If there isn't the upper program or the lower one, an error message is raised
		if up.delta_diam.values.size == 0 or low.delta_diam.values.size == 0:
			raise ValueError("No master programs for the selected diameter")
		else:
			pass
		# Sort data by delta diameter
		up.sort_values(by = ['delta_diam'], inplace = True, ignore_index = True) # change directly itself without producing a copy
		low.sort_values(by = ['delta_diam'], inplace = True, ignore_index = True)
		# Get upper and lower program filenames and diameters
		common.Variables.up_prog_filename = Path(up.fam_progs[0])
		common.Variables.low_prog_filename = Path(low.fam_progs[0])
		common.Variables.up_diam = up.diam[0]
		common.Variables.low_diam = low.diam[0]
		# Get the master program filename, i.e. the one having the closest diameter among up and low programs
		poss_master_progs = up[['delta_diam', 'fam_progs']][0:1].append(low[['delta_diam', 'fam_progs']][0:1])
		poss_master_progs.sort_values(by = 'delta_diam', inplace = True, ignore_index = True)
		master_prog_filename = poss_master_progs.fam_progs[0]
		# Generate target program filename
		partial_res_prog_filename = common.Variables.res_prog_dir.joinpath(common.Variables.tool_name)
		common.Variables.res_prog_filename = partial_res_prog_filename.with_suffix(common.Variables.vgp_suffix)
		# Copy the master program with the target program name (create the target program)
		shutil.copyfile(master_prog_filename, common.Variables.res_prog_filename)
		# Instantiate the result program object
		common.Variables.res_prog = pm.prog_select(common.Variables.res_prog_filename)

	@classmethod
	def scale_values(cls):
		with common.Variables.res_prog as res_prog:
			 res_prog.scale_prog_values()

	@classmethod
	def update_input_values(cls):
		with common.Variables.res_prog as res_prog:
			 res_prog.update_input_values()

	@classmethod	
	def apply_relations(self):
		#print('apply_relations')
		for i, row in common.Variables.data.iterrows(): # row is the pd.Series corresponding to a specific row
			if row.rel is not None:
				common.relations.select[row.rel](common.relations, [row.val_name], [row.rel_args], [row.val_addr]) # (self, [val_name], [row.rel_args], [row.val_addr])
				# val_name is passed in case of data update mode (when the returned value is kept into data without beeing updated in the program; the val_name is needed to address
				# the value into data)
			else:
				pass

# End phase
class End(Position):

	@classmethod
	def activate(self):
		print('Program ended. Press ENTER to exit')
		input()
		exit(0)




# This class contain the information carrier, the positions
class Machine(object):

	first_position_name = 'initialize'
	last_position_name = 'end'
	position = {
				  'initialize': Initialize(),
				  'insert_parameters': InsertParameters(),
				  'create_program': CreateProgram(),
				  'end': End()
				}

	@classmethod
	def go_to_position(cls, next_position_name):
		return cls.position.get(next_position_name)

	@classmethod
	def run(cls):
		print(common.Variables.copyright_header)
		current_position = cls.go_to_position(cls.first_position_name) # start position
		while current_position != cls.go_to_position(cls.last_position_name):
			next_position_name = current_position.activate() # return position name chosen in the position, and acquire user input while running (if any)
			current_position = cls.go_to_position(next_position_name) # current_position object belongs to an "is-a position" class
		# Be sure to print out the last scene
		current_position.activate()
			
