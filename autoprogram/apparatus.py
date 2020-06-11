from pathlib import Path
import glob
import os
import time
from itertools import compress

import sqlite3
import numpy as np
import pandas as pd
import shutil

from autoprogram import common
from autoprogram import program_manager as pm




pd.options.mode.chained_assignment = None  # default='warn'

# This class is the blueprint for all the positions (i.e. all the program phases)
class position(object):


	def __init__(self):

		self.prev_pos = []
		self.follow_pos = []


	def activate(self):

		print("This position is not yet configured.")
		print("Subclass it and implement activate(self) method.")
		sys.exit(1)


	# This function return the user inputs
	def user_input(self, ch_list = [], ch_ids = [], cast = [], print_list = []): #(ch_list, ch_id, cast, print_list)
		
		# if there is a list of choices
		if ch_list != [] and ch_ids != []:

			cast = str
			bound_val = True
			print_list = ''

			for i, j in zip(ch_ids, ch_list):

				print_list = print_list + f'Enter {i} for {j}\n'

			print_list = [print_list]

		# if there isn't
		elif cast != [] and print_list != []:

			bound_val = False
			ch_list = []

		else:

			raise ValueError('Not enough input arguments.')

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
							print("Input non among the possible choices.")

					if converted or not bound_val:

						os.system('clear')
						inp_list.append(inp_i)
						print("You have entered: " + str(inp_i))

						break

				except ValueError:

					print("Wrong input type")

		res = inp_list

		return res # list([inp1, inp2, ...])


	def select_position(self):

		ch_list = ['confirm', 'repeat', 'move back']
		ch_ids = ['C', 'R', 'B']

		ch = self.user_input(ch_list = ch_list, ch_ids = ch_ids)
		pos_select = ch[0]


		if (pos_select == 'confirm'):

			next_pos = self.follow_pos

		elif (pos_select == 'repeat'):

			next_pos = self.current_pos

		elif (pos_select == 'move back'):

			next_pos = self.prev_pos

		#os.system('cls' if os.name == 'nt' else 'clear')

		return next_pos




# This is the program phase in which the information carrier is initialized with the familiy name (provided by the user)
class initialize(position):

	def __init__(self):

		self.prev_pos = 'initialize'
		self.current_pos = self.prev_pos
		self.follow_pos = 'insert_parameters'


	def activate(self): #()
 
		self.insert_family_name()
		self.get_fam_prog_list()
		self.get_file_suffix()
		common.functions.get_tool_type()
		self.get_common_data()
		common.functions.get_variable_names()

		return self.select_position()


	# get the family name from user
	def insert_family_name(self):

		# create array containing family names (string format)
		fam_name_list = common.settings.db_get_all_fam_names() # ['fam1', 'fam2', ...]

		# create list containing family id (string format)
		fam_name_n = len(fam_name_list)
		fam_name_ids = [str(i + 1) for i in list(range(fam_name_n))]

		# user input
		print('Select family:')
		ch_fam = self.user_input(ch_list = fam_name_list, ch_ids = fam_name_ids)[0] # 'ch_fam'
		#ch_fam = 'CA-CS drill'
		common.variables.fam_name = ch_fam


	def get_fam_prog_list(self):

		common.variables.fam_prog_dir = Path(common.master_dir_path / common.variables.fam_name)
		common.variables.fam_prog_list = list(common.variables.fam_prog_dir.glob('**/*'))


	def get_file_suffix(self):

		fam_progs = list(common.variables.fam_prog_dir.glob('**/*'))
		common.variables.file_suffix = fam_progs[0].suffix # '.vgp'/ '.tom'

		print("File suffix is: " + common.variables.file_suffix)


	def get_common_data(self):

		common.variables.data = common.settings.db_get_fam_data(common.variables.fam_name)


# This is the program phase in which the user defines the geometrical parameter of the tool
class insert_parameters(position):

	def __init__(self):

		self.prev_pos = 'initialize'
		self.current_pos = 'insert_parameters'
		self.follow_pos = 'create_program'


	def activate(self): #()

		self.insert_parameter_values()
		self.update_diam_flute_len()

		return self.select_position()


	# Write user inputs in the value column
	def insert_parameter_values(self):

		# Creation of the printing list
		all_rel = common.variables.data.rel.tolist()
		all_descr = common.variables.data.descr.tolist()
		inp_vals_filt = [i == None for i in all_rel]
		descr_list = list(compress(all_descr, inp_vals_filt)) # use boolean indexing with lists
		print_list = [f'Enter {i}: ' for i in descr_list]

		# get user input
		print('Insert parameters:')
		inp_vals = self.user_input(cast = float, print_list = print_list)
		#inp_vals = [1.666, 2, 2, 2, 2, 2, 2, 2, 2, 2]
		common.variables.data.loc[common.variables.data.rel.isnull(), 'val'] = inp_vals # isnull() needed to reference None values


	# Insert diameter and flute length values (after user inputs)
	def update_diam_flute_len(self):

		#common.variables.diam = common.variables.v[common.variables.nrda[:, 0] == common.variables.diam_name][0, 0]
		common.variables.diam = common.variables.data.loc[common.variables.data.val_addr == common.variables.diam_addr, 'val'].values[0] # dereference all values with .values as ndarray and then with [0]

		common.variables.flute_len = common.variables.data.loc[common.variables.data.val_addr == common.variables.flute_len_addr, 'val'].values[0]





# This is the program phase in which the user defines the geometrical parameter of the tool
class create_program(position):

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
class end(position):

	def activate(self):

		print('Program ended. Press ENTER to exit')
		input()

		exit(0)




# This class contain the information carrier, the positions
class machine(object):

	def __init__(self):

		self.first_position_name = 'initialize'
		self.last_position_name = 'end'
		self.position = {
						  'initialize': initialize(),
						  'insert_parameters': insert_parameters(),
						  'create_program': create_program(),
						  'end': end()
						 }


	def go_to_position(self, next_position_name): #(machine(), str)

		res = self.position.get(next_position_name)

		return res # "is-a position" class


	def run(self):

		print(common.copyright_header)

		while True:

			try:

				current_position = self.go_to_position(self.first_position_name) # start position

				while current_position != self.go_to_position(self.last_position_name):
					
					next_position_name = current_position.activate() # return position name chosen in the position, and acquire user input while running (if any)
					current_position = self.go_to_position(next_position_name) # current_position object belongs to an "is-a position" class

				# be sure to print out the last scene
				current_position.activate()

				break

			except ValueError as val_err:

				print(val_err) # in case of value error, print the error and go to the first position (initialize)
