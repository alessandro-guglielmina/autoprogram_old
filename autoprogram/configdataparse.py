import pandas as pd
import numpy as np
from pathlib import Path
import tkinter as tk
import re
from math import * # needed to read trigonometric functions in the configuration file

from autoprogram import common
from autoprogram.openvgp.vgpio import VgpData

CONFIG_FILE_FILENAME = "configuration file.xlsx"
DIAM_NAME_SH_NAME = "diameter name"
INPUT_DATA_SH_NAME = "input data"
REL_DATA_SH_NAME = "relationships"
FUNCT_DATA_1_SH_NAME = "function data 1"
FUNCT_DATA_2_SH_NAME = "function data 2"
NECESSARY_SH_NAMES = [DIAM_NAME_SH_NAME, INPUT_DATA_SH_NAME]
FUNCT_DATA_SH_NAMES = [FUNCT_DATA_1_SH_NAME, FUNCT_DATA_2_SH_NAME]
VGP_DATA_SEP = ","
VAL_FUND_SEP = "-"
AUX_STR = "AUXILIARY"

def try_decorator(next_method):
	"""
	This decorator is added to any confirm function, in order to print the error (if any) on the communication label
	"""
	def wrapper_function(*args, **kwargs):
		try:
			return next_method(*args, **kwargs)
		except FileNotFoundError:
			raise ValueError(f"No such a configuration file: {args[0]}")
	return wrapper_function


class ConfigData(object):
	"""
	This class parse all the input arguments, coming from the user input and from the configuration file
	"""
	def __init__(self, fam_dir_path):
		# try to read the configuration file with the necessary sheets, if it's not present, throws a ValueError
		try:
			self.path = Path(fam_dir_path).joinpath(CONFIG_FILE_FILENAME)
			self.temp_config_data_df = pd.read_excel(self.path, sheet_name=NECESSARY_SH_NAMES) # add diameter name, input data and relationships workhsheets by default
			self.diam_name_df = self.temp_config_data_df[DIAM_NAME_SH_NAME].astype(str)
			self.inp_df = self.temp_config_data_df[INPUT_DATA_SH_NAME].astype(str) # fast access to input data
		except FileNotFoundError:
			raise ValueError(f"No configuration file in {fam_dir_path}")
		except KeyError:
			raise ValueError("A necessary worksheet is not present.")
		# try to read the relationships data sheets, if it is absent, it simply goes on
		self.rel_df = None
		try:
			temp_rel_df = pd.read_excel(self.path, sheet_name=REL_DATA_SH_NAME).astype(str) # the first two rows are skipped in function values sheets
			# if the sheet is present but is empty, it simply goes on
			if not temp_rel_df.empty:
				self.rel_df = temp_rel_df
		except KeyError:
			pass
		# try to read two function data sheets, if any of them is absent, it simply goes on
		self.funct_dfs = []
		for funct_data_sh_name in FUNCT_DATA_SH_NAMES:
			try:
				funct_df_i = pd.read_excel(self.path, sheet_name=funct_data_sh_name, skiprows=[0, 1]) # the first two rows are skipped in function values sheets
				# if the sheet is present but is empty, it simply goes on
				if not funct_df_i.empty:
					self.funct_dfs.append(funct_df_i) # fast access to function data
			except KeyError:
				pass
		self._diam_name = None
		self._scale_val_names_list = None

	@property
	def diam_name(self):
		"""
		Diameter name
		"""
		self._diam_name = self.diam_name_df.at[0, "diam_name"]
		return self._diam_name

	def save_raw_inp_data(self, raw_inp_data):
		"""
		This method writes the passed raw_data in the self.inp_df DataFrame
		"""
		raw_inp_data = pd.Series(raw_inp_data)
		raw_inp_data.apply(lambda x: x.append(np.nan))
		self.inp_df["raw_data"] = raw_inp_data # input data can be only scalar values (only the val field is required)

	def set_diam_val(self):
		"""
		This method set the variable self.diam_val to the diameter value inserted by the user
		"""
		filt = self.inp_df["data_name"] == self.diam_name
		self.diam_val = float(self.inp_df.loc[filt, "val"].values[0])

	def update_input_data(self, res_prog):
		"""
		This method updates the data coming from self.inp_df and self.rel_df
		"""
		inp_data_names = self.inp_df.data_name
		inp_data_names_filt = ~inp_data_names.str.upper().str.contains(AUX_STR, regex=False) # get the boolean filter corresponding to the names that are not auxiliary (auxiliary names are not updated in the program)
		inp_data_names = inp_data_names[inp_data_names_filt] # get only the not auxiliary names
		res_prog[inp_data_names] = self.inp_df.loc[inp_data_names_filt, "raw_data"].to_list()

	@staticmethod
	def var_from_python(python_expr, var_name):
		"""
		This method perform a variable assignment from python code
		"""
		try:
			local_dict = {}
			exec(python_expr, globals(), local_dict)
			var = local_dict[var_name]
			return var
		except SyntaxError:
			raise ValueError(f'Wrong syntax in the relationship expression: {python_expr}.')

	def update_relationships_data(self, res_prog):
		"""
		In this method, for each relationship, data names are substituted with their correspondent data from the program
		and then updated in the program itself
		"""
		def get_scalar_val(name):
			"""
			This method gets the scalar value from each name in each relationship
			Firstly looks into the program, then among inputs, then among previous relationships
			"""
			try:
				data = res_prog[name] # get data
				scalar_val = data.val[0] # take only the first value
				return scalar_val
			except ValueError:
					pass
			#Try to search for the auxiliary value inside self.inp_df
			try:
				filt = self.inp_df.data_name == name
				scalar_val = self.inp_df.loc[filt, "raw_data"].iloc[0][0] # data are stored as lists (the last [0] get the scalat value)
				return scalar_val
			except IndexError:
				pass
			except KeyError:
				raise ValueError("Tried to access data from user input")
			#Try to search for the auxiliary value inside self.rel_df
			try:
				filt = self.rel_df.data_name == name
				scalar_val = self.rel_df.loc[filt, "raw_data"].iloc[0][0] # data are stored as lists (the last [0] get the scalat value)
				return scalar_val
			except IndexError:
				raise ValueError(f"No such a name among available data: {name}")

		if self.rel_df is not None: # if relationships are present in the workbook
			self.rel_df["raw_data"] = "" # add an empty column collecting string data
			# Iterate over each relationship (over each row)
			for idx, rel_df_row in self.rel_df.iterrows():
				data_name = rel_df_row.data_name
				rel = rel_df_row.rel
				arg_names_list = re.findall(r'\$(.*?)\$', rel) # get a list with all the data names in the relationship
				for arg_name in arg_names_list:
					scalar_val = get_scalar_val(arg_name) # get a scalar value for each data name in the relationship
					rel = re.sub(r'\${}\$'.format(arg_name), str(scalar_val), rel)
				exec_rel = "raw_rel_data = [[" + rel + "]]" # the relation to be evalued is assigned to the variable "exec_rel_expr"
				raw_rel_data = ConfigData.var_from_python(exec_rel, "raw_rel_data") # list with evalued data (both val and sect_perc)
				# If it's an auxiliary name, raw_rel_data are put in the "raw_data" field in the self.rel_df DataFrame
				if AUX_STR in data_name.upper():
					filt = self.rel_df["data_name"] == data_name
					self.rel_df.loc[filt, "raw_data"] = raw_rel_data
				else:
					res_prog[data_name] = raw_rel_data


	def update_function_data(self, res_prog):
		"""
		This method read data in the function data sheets and update them into the program
		"""
		if self.funct_dfs: # if there are function data sheets
			for i in range(len(self.funct_dfs)):
				funct_data_df = self.funct_dfs[i]
				funct_data_df.iloc[:, [0, 1]] = funct_data_df.iloc[:, [0, 1]].astype(float) # the first two columns are casted as float
				arg_name = funct_data_df.columns[0] # argument name is the first column heading
				arg_val = res_prog[arg_name].val.iloc[0] # select the val and the first element only (in case of Parameter and VGP_Value_FunctionD data)
				filt = (funct_data_df.iloc[:, 0] <= arg_val) & (funct_data_df.iloc[:, 1] >= arg_val) # filtering based on the argument value
				# If the filter doesn't correspond to any row, it means that no function data correspond to that argument value
				if (~filt).all():
					raise ValueError(f"No function data defined for {arg_name} equal to {arg_val}")
				select_funct_data_df = funct_data_df.loc[filt, :].reset_index()
				select_funct_data_df = select_funct_data_df.iloc[:, 2::] # the first two column are the arguments column and are not considered during data reading and updating in the program
				# iterations over columns (rows already match the argument value)
				for data_name in select_funct_data_df: # data_name = column heading
					if not ('UNNAMED' in data_name.upper()): # if the column name is empty, it's a comment and must not be compiled
						funct_raw_expr = select_funct_data_df.at[0, data_name]
						funct_data_expr = "funct_data = [[" + funct_raw_expr + "]]" # the function value is assigned to the variable "raw_funct_data" when this code is compiled
						# execute raw_funct_data assignment
						funct_data = ConfigData.var_from_python(funct_data_expr, "funct_data")
						# convert m/s to mm/s
						if "SPEED" in data_name.upper():
							funct_data[0][0] = pd.Series(funct_data[0][0])*1000
						# convert mm/min to mm/s
						elif "FEEDRATE" in data_name.upper():
							funct_data[0][0] = pd.Series(funct_data[0][0])/60
						# update vgp data in the program (raw data are automatically converted to vgp data)
						res_prog[data_name] = funct_data