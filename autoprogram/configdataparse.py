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
# MASTER_SELECT_SH_NAME = "master selection"
INPUT_DATA_SH_NAME = "input data"
REL_DATA_SH_NAME = "relationships"
FUNCT_DATA_1_SH_NAME = "function data 1"
FUNCT_DATA_2_SH_NAME = "function data 2"
#SCALE_VALS_SH_NAME = "scaled values"
SHEET_NAMES_1 = [DIAM_NAME_SH_NAME, INPUT_DATA_SH_NAME, REL_DATA_SH_NAME]
FUNCT_DATA_SH_NAMES = [FUNCT_DATA_1_SH_NAME, FUNCT_DATA_2_SH_NAME] # read all the rows but the first 3
# ALL_SHEET_NAMES = SHEET_NAMES_1 + SHEET_NAMES_2
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
		# try to read the configuration file, it it's not present, throws a ValueError
		try:
			self.path = Path(fam_dir_path).joinpath(CONFIG_FILE_FILENAME)
			self.config_data_df = pd.read_excel(self.path, sheet_name=SHEET_NAMES_1) # add diameter name, input data and relationships workhsheets by default
		except FileNotFoundError:
			raise ValueError(f"No configuration file in {fam_dir_path}")
		# try to read two function data sheets, if any of them is absent, it simply goes on
		self.funct_data_sh_names = []
		for funct_data_sh_name in FUNCT_DATA_SH_NAMES:
			try:
				config_data_funct_i = pd.read_excel(self.path, sheet_name=[funct_data_sh_name], skiprows=[0, 1]) # the first two rows are skipped in function values sheets
				self.config_data_df = {**self.config_data_df, **config_data_funct_i}
				self.funct_data_sh_names = self.funct_data_sh_names.append(funct_data_sh_name)
			except KeyError:
				pass
		self.inp_df = self.config_data_df[INPUT_DATA_SH_NAME].astype(str) # save input worksheet as DataFrame
		aux_rel_filt = self.config_data_df[REL_DATA_SH_NAME].loc[:, "data_name"].str.contains(AUX_STR, case=False)
		self.rel_sub_df = self.config_data_df[REL_DATA_SH_NAME].loc[~aux_rel_filt, :].astype(str).reset_index() # save relationships to be updated in the program in a DataFrame
		self.rel_aux_df = self.config_data_df[REL_DATA_SH_NAME].loc[aux_rel_filt, :].astype(str).reset_index() # save auxiliary relationships (over which evaluations have to be performed) in a DataFrame 
		self._diam_name = None
		self._scale_val_names_list = None

	@property
	def diam_name(self):
		"""
		Diameter name
		"""
		diam_name_df = self.config_data_df[DIAM_NAME_SH_NAME].astype(str)
		self._diam_name = diam_name_df.at[0, "diam_name"]
		return self._diam_name

	@staticmethod
	def save_staging_data(staging_df, raw_data: pd.Series):
		"""
		This method writes the input data in the passed staging_df DataFrame
		"""
		vgp_data = pd.DataFrame.from_records(raw_data)
		staging_df["val"] = vgp_data.iloc[:, 0]
		try:
			staging_df["sect_perc"] = vgp_data.iloc[:, 1]
		except IndexError:
			staging_df["sect_perc"] = np.nan

	def set_diam_val(self):
		"""
		This method set the variable self.diam_val to the diameter value inserted by the user
		"""
		filt = self.inp_df["data_name"] == self.diam_name
		self.diam_val = float(self.inp_df.loc[filt, "val"].values[0])

	@staticmethod
	def update_staging_data(staging_df, res_prog):
		"""
		This method updates the data coming from the previously saved DataFrame (staging_df) in the program
		"""
		# Get the boolean filter corresponding to the names that are not auxiliary (auxiliary names are not updated in the program)
		data_names = staging_df.data_name
		data_names_filt = ~data_names.str.upper().str.contains(AUX_STR, regex=False)
		# Apply the filter
		data_names = data_names[data_names_filt]
		vgp_data = staging_df.loc[data_names_filt, ["val", "sect_perc"]]
		res_prog[data_names] = vgp_data

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
			raise ValueError('Wrong syntax in the relationship expressions.')

	def update_relationships_data(self, res_prog):
		"""
		In this method, for each relationship, data names are substituted with their correspondent data from the program
		and then updated in the program itself
		"""
		def get_arg_scalar_val(data_name_ser: pd.Series, res_prog) -> str:
			"""
			This method get the scalar value to put into the relations, data can be get from the program or from the input values if they are auxiliary (not updated in the program)
			self comes at the second place, since this method must be iterated over an apply() method. Could be put inside update_relationships_data(), to mantain order
			"""
			data_name = data_name_ser.iloc[0]
			# if the relation refers to an auxiliary parameter looks into the inp_df
			if AUX_STR in data_name.upper():
				# search for auxiliary values in the two staging DataFrames (input and relationships)
				aux_inp_filt = self.inp_df["data_name"] == data_name
				aux_rel_filt = self.rel_aux_df["data_name"] == data_name
				# if the name is in the input staging DataFrame
				if aux_inp_filt.any():
					val = self.inp_df.loc[aux_inp_filt, "val"].iloc[0]
				# if the name is in the relationships staging DataFrame
				elif aux_rel_filt.any():
					val = self.rel_aux_df.loc[aux_rel_filt, "val"].iloc[0]
				else:
					raise ValueError(f"No such an auxiliary value: {data_name}")
			# otherwise looks directly in the program
			else:
				val = res_prog[data_name].iloc[0, 0] # get the "val" field of the data returned from the program
				# if the returned value is not a scalar it's converted to scalar (values must be constant to have sense)
				if hasattr(val, "__len__"):
					val = val[0]
			return val

		def sub_arg_scalar_vals_in_rel(rel_arg_data_df, raw_rel_expr):
			"""
			In each relation, for each argument name, this method substitutes the name with the actual scalar value
			"""
			raw_rel_data = raw_rel_expr
			for idx, rel_arg_data_row in rel_arg_data_df.iterrows():
				raw_rel_data = re.sub(r'\${}\$'.format(rel_arg_data_row["rel_arg_data_name"]), str(rel_arg_data_row["rel_arg_data_scalar_val"]), raw_rel_data)
			return raw_rel_data

		def get_raw_rel_data_from_expr(rel_staging_row):
			"""
			This method extrapolates the raw_rel_data for each realtionship. Firstly, substitutes the scalar values in the expression, then evaluates the expression and eventually
			converts it into a string representing the raw data to be saved
			"""
			raw_rel_expr = rel_staging_row["rel_expr"]
			rel_arg_data_names = re.findall(r'\$(.*?)\$', raw_rel_expr) # get a list with all the data names in the expression
			rel_arg_data_df = pd.DataFrame(rel_arg_data_names, columns=["rel_arg_data_name"])# creates a DataFrame with arguments name (for each relation)
			rel_arg_data_df[["rel_arg_data_scalar_val"]] = rel_arg_data_df.apply(lambda rel_arg_data_row: get_arg_scalar_val(rel_arg_data_row, res_prog), axis=1) # get values from the program and convert to scalar (in order to apply relations)
			raw_rel_expr = sub_arg_scalar_vals_in_rel(rel_arg_data_df, raw_rel_expr) # substitutes argument names with correspondent scalar values
			exec_rel_expr = "rel_exec_data = [" + raw_rel_expr + "]" # the relation to be evalued is assigned to the variable "exec_rel_expr"
			raw_rel_data = ConfigData.var_from_python(exec_rel_expr, "rel_exec_data") # list with evalued data (both val and sect_perc)
			return raw_rel_data

		# if there is any auxiliary relationship (if self.rel_aux_df is not an empty DataFrame)
		if not self.rel_aux_df.empty:
			raw_aux_rel_data = self.rel_aux_df.apply(get_raw_rel_data_from_expr, axis=1) # compute expressions for auxiliary relationships
			ConfigData.save_staging_data(self.rel_aux_df, raw_aux_rel_data) # save auxiliary relationships val and sect_perc fields

		raw_sub_rel_data = self.rel_sub_df.apply(get_raw_rel_data_from_expr, axis=1) # compute expressions for relationships to be updated in the program
		ConfigData.save_staging_data(self.rel_sub_df, raw_sub_rel_data) # save relationships val and sect_perc fields to be updated in the program
		ConfigData.update_staging_data(self.rel_sub_df, res_prog) # update relationships in the program

	def update_function_data(self, res_prog):
		"""
		This method read data in the function data sheets and update them into the program
		"""
		if self.funct_data_sh_names: # if there are function data sheets
			for funct_data_sh_name in self.funct_data_sh_names:
				funct_data_df = self.config_data_df[funct_data_sh_name].astype(str)
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