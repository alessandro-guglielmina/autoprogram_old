from pathlib import Path
import glob
import os
import time
from itertools import compress
import sqlite3
import numpy as np
import pandas as pd
import shutil

from autoprogram import config
from autoprogram import common
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
	# This function return the user inputs
	def user_input(cls, ch_list = None, ch_ids = None, cast = None, print_list = None): #(ch_list, ch_id, cast, print_list)
		# If there is a list of choices
		if ch_list is not None and ch_ids is not None:
			cast = str
			bound_val = True
			print_list = ''
			for i, j in zip(ch_ids, ch_list):
				print_list = print_list + f'Enter {i} for {j}\n'
			print_list = [print_list]
		# if there isn't
		elif cast is not None and print_list is not None:
			bound_val = False
		else:
			raise ValueError('Wrong arguments combination.')
		inp_list = []
		converted = False
		for i in print_list:
			os.system('clear')
			while True:
				try:
					inp_i = cast(input(f'{i}\n> ')) # user input call
					if bound_val: # (so cast = str and ch_id must be given)
						inp_i = inp_i.upper() # the choice must be capital to make the choice case insensitive
						if inp_i in ch_ids:
							bool_filt = [i == inp_i for i in ch_ids]
							ch = list(compress(ch_list, bool_filt))[0] # use boolean indexing on a list
							inp_i = ch # inp_val_i is reassigned with the choice corresponding to the chosen index
							converted = True
						else:
							os.system('clear')
							print("Input non among the possible choices.\n")
					if converted or not bound_val:
						os.system('clear')
						inp_list.append(inp_i)
						print("You have entered: " + str(inp_i) + "\n")
						break
				except ValueError:
					print("Wrong input type\n")
		res = inp_list
		return res # list([inp1, inp2, ...])

	@classmethod
	def select_position(cls):
		ch_list = ['confirm', 'repeat', 'move back']
		ch_ids = ['C', 'R', 'B']
		ch = cls.user_input(ch_list = ch_list, ch_ids = ch_ids)
		pos_select = ch[0]
		if (pos_select == 'confirm'):
			next_pos = cls.follow_pos
		elif (pos_select == 'repeat'):
			next_pos = cls.current_pos
		elif (pos_select == 'move back'):
			next_pos = cls.prev_pos
		return next_pos

# This is the program phase in which the information carrier is initialized with the familiy name (provided by the user)
class Initialize(Position):

	prev_pos = 'initialize'
	current_pos = prev_pos
	follow_pos = 'insert_parameters'

	@classmethod
	def activate(cls): #()
		cls.insert_preliminary_data()
		cls.get_fam_prog_data()
		cls.get_tool_type()
		cls.get_val_addr()
		cls.get_common_data()
		print(common.Variables.data.val_addr)
		input('pausa')
		return cls.select_position()

	# Get the family names from the master programs directories
	@classmethod
	def get_fam_names(cls):
		return [str(fam_dir.name) for fam_dir in config.master_progs_dir.iterdir() if fam_dir.is_dir()]

	# Get the family name from user
	@classmethod
	def insert_preliminary_data(cls):
		# Acquire tool name
		common.Variables.tool_name = input('Insert tool name:\n>')
		# Create array containing all family names (string format)
		fam_name_list = cls.get_fam_names() # ['fam1', 'fam2', ...]
		# Create list containing family id (string format)
		fam_name_ids = [str(i + 1) for i in list(range(len(fam_name_list)))]
		# Acquire user input
		print('Select family:\n')
		common.Variables.fam_name = cls.user_input(ch_list = fam_name_list, ch_ids = fam_name_ids)[0] # 'ch_fam'
		os.system('clear')

	@classmethod
	def get_fam_prog_data(cls):

		fam_prog_dir = Path(config.master_progs_dir/common.Variables.fam_name)
		common.Variables.fam_prog_list = list(fam_prog_dir.glob('**/*'))
		common.Variables.file_suffix = common.Variables.fam_prog_list[0].suffix

	# Get the tool type from the family name (which must contain the tool type, e.g. 'drill', 'mill', ...)
	@classmethod
	def get_tool_type(cls):
		if 'DRILL' in common.Variables.fam_name.upper():
			common.Variables.tool_type = 'drill'
		elif 'MILL' in common.Variables.fam_name.upper():
			common.Variables.tool_type = 'mill'
		elif 'REAMER' in variables.fam_name.upper():
			common.Variables.tool_type = 'reamer'
		else:
			raise ValueError('No such a tool type.')
		print("Tool type is: " + common.Variables.tool_type)

	# Get the common data needed in the following steps
	@classmethod
	def get_common_data(cls):
		common.Variables.data = common.Variables.input_values_wb.get_common_data(common.Variables.fam_name)

	# Initialize the names of some features, depending on the tool type
	@classmethod
	def get_val_addr(cls):
		# Update diam and flute names depending on file suffix and tool type
		if common.Variables.file_suffix == config.vgp_suffix:
			if common.Variables.tool_type == 'drill':
				common.Variables.diam_addr = config.drill_diam_addr
				common.Variables.flute_len_addr = config.drill_flute_len_addr
				# common.Variables.point_ang_addr = config.drill_point_ang_addr
				# common.Variables.first_spg_addr = config.drill_first_spg_addr
				# common.Variables.meas_dist_addr = config.drill_meas_dist_addr
			elif common.Variables.tool_type == 'mill':
				pass
			else:
				raise ValueError('No such a tool type.')
		else:
			raise ValueError('No such a file suffix.')


# This is the program phase in which the user defines the geometrical parameter of the tool
class InsertParameters(Position):

	prev_pos = 'initialize'
	current_pos = 'insert_parameters'
	follow_pos = 'create_program'

	@classmethod
	def activate(cls):
		cls.insert_parameter_values()
		cls.update_diam_flute_len()
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
		inp_vals = cls.user_input(cast = float, print_list = print_list)
		# Input values have no relation, this feature is used to refence them in common data
		common.Variables.data.loc[common.Variables.data.rel.isnull(), 'val'] = inp_vals # isnull() needed to reference None values

	# Record diameter and flute length values in common data (after user inputs)
	@classmethod
	def update_diam_flute_len(cls):
		common.Variables.diam = common.Variables.data.loc[common.Variables.data.val_addr == common.Variables.diam_addr, 'val'].values[0] # dereference all values with .values as ndarray and then with [0]
		common.Variables.flute_len = common.Variables.data.loc[common.Variables.data.val_addr == common.Variables.flute_len_addr, 'val'].values[0]





# This is the program phase in which the user defines the geometrical parameter of the tool
class CreateProgram(Position):

	def __init__(self):

		self.prev_pos = 'insert_parameters'
		self.current_pos = 'create_program'
		self.follow_pos = 'end'


	def activate(self): #()

		self.select_master_prog()
		self.scale_values()
		self.update_input_values()
		self.apply_relations()
		self.close_program()
		
		return self.select_position()


	def select_master_prog(self):

		diam = common.variables.diam
		flute_len = common.variables.flute_len
		flute_len_xd = flute_len / diam

		diam_arr = np.empty((1, 0), dtype = float)
		flute_len_xd_arr = np.empty((1, 0), dtype = float)
		fam_progs = common.variables.fam_prog_list

		for i in fam_progs:
			#print('select_master_prog')
			prog_path_i = Path(i)
			prog_i = pm.prog_select(prog_path_i)# T.B.N. no dependency with respect to the file type, .vgp only!!!
			diam_i = prog_i.prog_get_values_from_addr([common.variables.diam_addr]).val.values[0] # float, DataFrame.val.values is a 1-sized numpy array
			flute_len_i = prog_i.prog_get_values_from_addr([common.variables.flute_len_addr]).val.values[0]
			prog_i.prog_cls() # close reference program connections

			flute_len_xd_i = flute_len_i / diam_i

			diam_arr = np.append(diam_arr, diam_i)
			flute_len_xd_arr = np.append(flute_len_xd_arr, flute_len_xd_i)

		# Data to be sorted
		#diam assigned
		delta_diam = diam_arr - diam
		delta_flute_len_xd = flute_len_xd_arr - flute_len_xd
		#fam_progs already assigned 

		data = pd.DataFrame({
							'diam': pd.Series(diam_arr, dtype= 'float'),
							'delta_diam': pd.Series(delta_diam, dtype= 'float'),
							'delta_flute_len_xd': pd.Series(delta_flute_len_xd, dtype= 'float'),
							'fam_progs': pd.Series(fam_progs, dtype= 'str')
							})

		# Separate positive and negative delta diameters data in two different DataFrames
		up = data.loc[data.delta_diam > 0, :]
		low = data.loc[data.delta_diam <= 0, :]

		# Absolute value of delta diameters (in-place operation)
		np.absolute(up.delta_diam.values, out = up.delta_diam.values)
		np.absolute(low.delta_diam.values, out = low.delta_diam.values)


		# If there isn't neither an up program or a low program an error message is raised
		if up.delta_diam.values.size == 0 or low.delta_diam.values.size == 0:

			raise ValueError("No master programs for the selected diameter")

		else:

			pass

		# Sort data by delta flute length xd and then by delta diameter, thus with the same delta diameter, the first element is the one with the lower delta flute length xd 
		up.sort_values(by = ['delta_diam', 'delta_flute_len_xd'], inplace = True, ignore_index = True) # change directly itself without producing a copy
		low.sort_values(by = ['delta_diam', 'delta_flute_len_xd'], inplace = True, ignore_index = True)

		# Get up and low program filenames and diameters
		common.variables.up_prog_filename = up.fam_progs[0]
		common.variables.low_prog_filename = low.fam_progs[0]
		common.variables.up_diam = up.diam[0]
		common.variables.low_diam = low.diam[0]

		# Get the master program filename, i.e. the one having the closest diameter among up and low programs
		poss_master_progs = up[['delta_diam', 'fam_progs']][0:1].append(low[['delta_diam', 'fam_progs']][0:1])
		poss_master_progs.sort_values(by = 'delta_diam', inplace = True, ignore_index = True)
		master_prog_filename = poss_master_progs.fam_progs[0]

		# Generate target program filename
		partial_prog_filename = common.res_prog_dir.joinpath(common.variables.tool_name)
		common.variables.prog_filename = partial_prog_filename.with_suffix(common.variables.file_suffix)

		# Copy the master program with the target program name (create the target program)
		shutil.copy2(master_prog_filename, common.variables.prog_filename)

		# Instantiate the target program object
		common.variables.prog = pm.prog_select(common.variables.prog_filename)


	def scale_values(self):
		#print('scale_values')
		common.variables.prog.prog_scale_values()


	def update_input_values(self):
		#print('update_input_values')
		common.variables.prog.prog_update_input_values()


		
	def apply_relations(self):
		#print('apply_relations')
		for i, row in common.variables.data.iterrows(): # row is the pd.Series corresponding to a specific row

			if row.rel is not None:

				common.relations.select[row.rel](common.relations, [row.val_name], [row.rel_args], [row.val_addr]) # (self, [val_name], [row.rel_args], [row.val_addr])
				# val_name is passed in case of data update mode (when the returned value is kept into data without beeing updated in the program; the val_name is needed to address
				# the value into data)

			else:

				pass


	def close_program(self):

		common.variables.prog.prog_cls()
		common.settings.db_cls()



# End phase
class End(Position):

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
		print(config.copyright_header)
		current_position = cls.go_to_position(cls.first_position_name) # start position
		while current_position != cls.go_to_position(cls.last_position_name):
			next_position_name = current_position.activate() # return position name chosen in the position, and acquire user input while running (if any)
			current_position = cls.go_to_position(next_position_name) # current_position object belongs to an "is-a position" class
		# Be sure to print out the last scene
		current_position.activate()
			
