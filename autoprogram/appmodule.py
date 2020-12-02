from pathlib import Path
import glob
import os
import time
import sqlite3
import numpy as np
import pandas as pd
import shutil
from itertools import compress
import re

from autoprogram import common
from autoprogram import wbmodule as wbm
from autoprogram import progmodule as pm

pd.options.mode.chained_assignment = None  # default='warn'


# This is the first program step in which the information carrier is initialized with the familiy name (provided by the user)
class Initialize(object):

	# Get the family names from the family directories inside the master programs directory
	@classmethod
	def get_fam_names(cls):

		try:

			return [str(fam_dir.name) for fam_dir in common.Variables.master_progs_dir.iterdir() if fam_dir.is_dir()]

		except FileNotFoundError:

			raise ValueError(f'No such a master programs directory: {common.Variables.master_progs_dir.__str__()}')


	# Get common data dependent on the chosen family
	@classmethod
	def get_fam_dependent_vars(cls):

		# assign these global variables after pushing the confirm button and not while starting the application, otherwise it would make the application crash if a wrong path is inserted
		common.Variables.values_database_wb = wbm.WorkBook(Path(common.Variables.master_progs_dir / common.Variables.values_database_wb_filename))

		common.Variables.values_database_sh = list(common.Variables.values_database_wb.wb.values())[0] # first wb sheet selection, it's a DataFrame containing all the recorded values information (val_name, val_descr, val_addr)

		# get family directory
		fam_prog_dir = Path(common.Variables.master_progs_dir/common.Variables.fam_name)

		# get the master programs list
		common.Variables.fam_master_list = list(fam_prog_dir.glob('*' + common.Variables.vgp_suffix))

		# assign the configuration file
		common.Variables.config_file_wb =  wbm.WorkBook(Path(fam_prog_dir/common.Variables.config_file_wb_filename))

		# get the tool type from the family name and get the diameter address based on that (IT'S BETTER TO CONFIGURE DIAM ADDRESS)
		if 'DRILL' in common.Variables.fam_name.upper():

			common.Variables.tool_type = 'drill'

			common.Variables.diam_addr = common.Variables.drill_diam_addr

		elif 'MILL' in common.Variables.fam_name.upper():

			common.Variables.tool_type = 'mill'

		elif 'REAMER' in Variables.fam_name.upper():

			common.Variables.tool_type = 'reamer'

		else:

			raise ValueError('No such a tool type.')

		# get the common data from the configuration file
		common.Variables.data = wbm.get_common_data()


# This is the program phase in which the user defines the geometrical parameter of the tool
class InsertParameters(object):

	# get a list with all the input descriptions, with the sam order of the input values
	@classmethod
	def get_params_descr(cls):

		# Create printing list
		all_rel = common.Variables.data.rel.to_numpy()

		all_descr = common.Variables.data.val_descr.to_numpy()

		# print(all_rel)
		# print(all_descr)

		inp_vals_filter = np.equal(all_rel, None) # input values are those not having any relationship with others

		descr_list = all_descr[inp_vals_filter]

		# print(descr_list)

		return descr_list # [descr1, descr2, ...]

	@classmethod
	def save_input_params(cls, input_vals): # (cls, [inp_val1, inp_val2, ...])

		input_vals = [[i] for i in input_vals] # makes all the values lists (iterables)

		# Input values have no relation, this feature is used to reference them among common data
		common.Variables.data.loc[common.Variables.data.rel.isnull(), 'val'] = input_vals # write user input values in common.Variables.data (isnull() needed to reference None values)

		# Save the diameter value in a common variable in order to be easily accessed while choosing the master program
		common.Variables.diam = common.Variables.data.loc[common.Variables.data.val_addr == common.Variables.diam_addr, 'val'].values[0][0] # dereference all values with .values as ndarray and then with [0]


# This is the program phase in which the program makes computation to get the result program
class CreateProgram(object):

	@classmethod
	def run(cls):

		cls.select_master_prog()

		cls.scale_values()

		cls.update_input_values()

		cls.apply_relations()

		cls.apply_functions()


	# In this step the rogram chooses the master program, i.e. the one having the closest diameter
	@classmethod
	def select_master_prog(cls):

		diam = common.Variables.diam

		diam_arr = np.empty((1, 0), dtype = float)

		fam_progs = common.Variables.fam_master_list

		for i in fam_progs:

			prog_path_i = Path(i)

			# Open a context manager with the db composition of prog_i+ to open a connection with the vgp program (database)
			with  pm.VgpProg(prog_path_i) as prog_i:

				diam_i = prog_i.get_values_from_addr([common.Variables.diam_addr]).val.values[0] # float, DataFrame.val.values is a 1-sized numpy array

			diam_arr = np.append(diam_arr, diam_i)

		# Data to be sorted
		delta_diam = diam_arr - diam

		#fam_progs already assigned 
		data = pd.DataFrame({'diam': pd.Series(diam_arr, dtype= 'float'),

							'delta_diam': pd.Series(delta_diam, dtype= 'float'),

							'fam_progs': pd.Series(fam_progs, dtype= 'str')})

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

		try:

			# Copy the master program with the target program name (create the target program)
			shutil.copyfile(master_prog_filename, common.Variables.res_prog_filename)

			# Instantiate the result program object
			common.Variables.res_prog = pm.VgpProg(common.Variables.res_prog_filename)

		except FileNotFoundError:

			raise ValueError(f'No such a result program directory: {common.Variables.res_prog_dir.__str__()}')


	@classmethod
	def scale_values(cls):

		with common.Variables.res_prog as res_prog:

			 res_prog.scale_prog_values()


	# pdate input values first, so if an input value is read from the program while applying relations, it is up to date
	@classmethod
	def update_input_values(cls):

		with common.Variables.res_prog as res_prog:

			 res_prog.update_input_values()


	@classmethod	
	def apply_relations(self):

		for i, row in common.Variables.data.iterrows(): # row is the pd.Series corresponding to a specific row

			if row.rel is not None: # row.rel is a string

				arg_names = re.findall(r'\$(.*?)\$', row.rel) # get a list with all the arg names (strings between $$)

				with common.Variables.res_prog as res_prog:

					arg_vals = res_prog.get_values_from_names(arg_names) # return a DataFrame whose colimns are sect_perc and val of the values substituted in the relation

					arg_vals = arg_vals.val.to_list() # take only the val (that are np.arrays)

					arg_vals = [i[0] for i in arg_vals] # dereference the arrays, take only the value inside them

					rel_exp = row.rel

					for arg_name, arg_val in zip(arg_names, arg_vals):

						rel_exp = re.sub(r'\${}\$'.format(arg_name), str(arg_val), rel_exp) # substitute the val names in the expression with their value, one at each for cycle

					local_dict = {}

					try:

						exec(rel_exp, globals(), local_dict)

					except SyntaxError:

						raise ValueError('Wrong syntax in the configuration values.')

					row.val = [local_dict['val']] # the value must be an iterable, thus we add parentheses

					res_prog.update_values_from_addr([row.val_addr],  pd.DataFrame([[row.sect_perc, row.val]], columns = ['sect_perc', 'val']))

			else:

				pass


	@classmethod	
	def apply_functions(self):

		funct_vals_sheets = []

		try:

			funct_vals_1_sh =  common.Variables.config_file_wb.wb[common.Variables.funct_vals_1_sh_name] # DataFrame with the first page of function values

			funct_vals_sheets.append(funct_vals_1_sh)

		except KeyError:

			raise ValueError('First function values sheet missing.') # the first function values sheet is mandatory

		try:

			funct_vals_2_sh =  common.Variables.config_file_wb.wb[common.Variables.funct_vals_2_sh_name] # DataFrame with the first page of function values

			funct_vals_sheets.append(funct_vals_2_sh)

		except KeyError:

			pass # the second function values sheet is not mandatory

		for funct_val_sheet in funct_vals_sheets:

			funct_arg_name = funct_val_sheet.columns[0] # takes the first column heading, i.e. the function argument (most times the tool diameter)

			with common.Variables.res_prog as res_prog: # context manager opening the program

				funct_arg_val = res_prog.get_values_from_names([funct_arg_name]).val[0][0] # take function argument value (i.e. the val component)

				diff = funct_val_sheet[funct_arg_name].astype(float).sub(funct_arg_val) # config file argument values - actual program value

				idx = diff[diff < 0].idxmax() # take the index of the gratest smaller argument value in the config file argument column

				funct_val_names = funct_val_sheet.columns[1:] # take all the headings but the first one (that is the argument value)

				funct_val_names = [i for i in funct_val_names if not ('UNNAMED' in i.upper() or 'WHEEL' in i.upper())] # takes only the actual result values headings, not the assigned wheels and the empty coluns (whose heading is imported as 'unnamed...')

				columns = ['sect_perc', 'val']

				comp_funct_vals = pd.DataFrame(columns = columns, dtype = object) # complete function values (just to be updated in the program)

				for funct_val_name in funct_val_names:

					raw_funct_val = funct_val_sheet.loc[idx, funct_val_name] # take the raw text value from the spreadsheet

					try:

						funct_val = np.array(raw_funct_val.split(common.Variables.separator)).astype(float) # array of floats from the spreadsheet

					except ValueError:

						raise ValueError(f'Wrong function value format in the function values sheet: column {funct_val_name}, row {idx}') # if there is some format error, raise a ValueError

					comp_funct_vals = comp_funct_vals.append({'sect_perc' : None, 'val' : funct_val}, ignore_index = True)

				res_prog.update_values_from_names(funct_val_names, comp_funct_vals)