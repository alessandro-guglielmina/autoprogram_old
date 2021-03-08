import pandas as pd
import numpy as np
from pathlib import Path
import tkinter as tk
import re

from autoprogram import common
from autoprogram.openvgp.vgpio import VgpData

CONFIG_FILE_FILENAME = "configuration file.xlsx"
DIAM_NAME_SH_NAME = "diameter name"
MASTER_SELECT_SH_NAME = "master selection"
INPUT_DATA_SH_NAME = "input data"
REL_DATA_SH_NAME = "relationships"
FUNCT_DATA_1_SH_NAME = "function data 1"
FUNCT_DATA_2_SH_NAME = "function data 2"
SCALE_VALS_SH_NAME = "scaled values"
SHEET_NAMES_1 = [SCALE_VALS_SH_NAME, INPUT_DATA_SH_NAME, REL_DATA_SH_NAME]
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
		self.path = Path(fam_dir_path).joinpath(CONFIG_FILE_FILENAME)
		config_data_1 = pd.read_excel(self.path, sheet_name=SHEET_NAMES_1)
		config_data_funct = pd.read_excel(self.path, sheet_name=FUNCT_DATA_SH_NAMES, skiprows=[0, 1]) # the first two rows are skipped in function values sheets
		self.config_data_df = {**config_data_1, **config_data_funct}
		self.input_df = self.config_data_df[INPUT_DATA_SH_NAME].astype(str)
		self._diam_name = None
		self._scale_val_names_list = None

	@property
	def diam_name(self):
		"""
		Description
		"""
		diam_name_df = self.config_data_df[DIAM_NAME_SH_NAME].astype(str)
		self._diam_name = diam_name_df.at[0, "diam_name"]
		return self._diam_name
	
	@property
	def scale_val_names_list(self):
		"""
		Description
		"""
		scale_val_names_df = self.config_data_df[SCALE_VALS_SH_NAME].astype(str)
		self._scale_val_names_list = scale_val_names_df.loc[:, "val_name"].to_list()
		return self._scale_val_names_list
	
	@staticmethod
	def to_widget_name(data_name: str):
		"""
		This method replace the "." with "_", because the dot results in a bad widget name error
		"""
		widget_name = data_name.replace(".", "_").lower()
		return widget_name

	def get_master_prog_name(self, diam_val):
		master_prog_select_df = self.config_data_df[MASTER_SELECT_SH_NAME].astype({"low_diam": float, "up_diam": float, "master_prog_name": str})
		filt = (master_prog_select_df.low_diam <= diam_val) & (master_prog_select_df.up_diam >= diam_val) # & performs element-wise evaluation
		try:
			return master_prog_select_df.loc[filt, "master_prog_name"].iloc[0] + common.vgp_suffix
		except IndexError:
			raise ValueError("No master program for such a diameter")

	def get_gui_raw_data(self, input_data_page):
		"""
		This method collect the raw string inputs inserted by the user (it's one way to get input data)
		"""
		raw_inp_data_list = []
		for inp_data_name in self.input_df.data_name:
			data_entry = input_data_page.nametowidget(ConfigData.to_widget_name(inp_data_name))
			raw_inp_data_i = data_entry.get()
			raw_inp_data_list.append(raw_inp_data_i)
		return pd.Series(raw_inp_data_list)

	def save_input_data(self, raw_inp_data: pd.Series):
		"""
		This method writes the input data in the self.input_df DataFrame
		"""
		vgp_inp_data = raw_inp_data.str.split(VGP_DATA_SEP, n=1, expand=True)
		self.input_df["inp_val"] = vgp_inp_data.loc[:, 0]
		try:
			self.input_df["inp_sect_perc"] = vgp_inp_data.loc[:, 1]
		except KeyError:
			self.input_df["inp_sect_perc"] = np.nan

	def update_input_data(self, res_prog):
		"""
		This method updates the input data coming from the previously saved DataFrame (self.input_df) in the program
		"""
		# Get the boolean filter corresponding to the names that are not auxiliary
		inp_data_names = self.input_df.data_name
		inp_data_names_filt = ~inp_data_names.str.upper().str.contains(AUX_STR, regex=False)
		# Apply the filter
		inp_data_names = inp_data_names[inp_data_names_filt]
		inp_data = self.input_df.loc[inp_data_names_filt, ["inp_val", "inp_sect_perc"]]
		res_prog[inp_data_names] = inp_data

	def update_relationships_data(self, res_prog):
		"""
		In this method, for each relationship, data names are substituted with their correspondent data from the program
		and then updated in the program itself
		"""
		def get_rel_scalar_val(data_name_ser: pd.Series) -> str:
			"""
			This method get the values to put into the relations, data can be get from the program or from the input values if they are auxiliary (not updated in the program)
			"""
			data_name = data_name_ser.iloc[0]
			# if the relation refers to an auxiliary parameter looks into the input_df
			if AUX_STR in data_name.upper():
				filt = self.input_df["data_name"] == data_name
				val = self.input_df.loc[filt, "inp_val"].iloc[0]
			else:
				# otherwise looks directly in the progam
				val = res_prog[data_name].iloc[0, 0] # get the "val" field of the data returned from the program
				# if the returned value is not a scalar it's converted to scalar (values must be constant to have sense)
				if hasattr(val, "__len__"):
					val = val[0]
			return val

		# get a DataFrame whose rows are relations, each one containing the data name and the relationship
		rel_df = self.config_data_df[REL_DATA_SH_NAME].astype(str)
		for rel_idx, (data_name, rel_expr) in rel_df.iterrows():
			arg_data_names = re.findall(r'\$(.*?)\$', rel_expr) # get a list with all the data names in the expression
			sub_data_df = pd.DataFrame(arg_data_names, columns=["arg_data_name"])
			sub_data_df[["arg_scalar_val"]] = sub_data_df.apply(get_rel_scalar_val, axis=1) # get values from the program and convert to scalar (in order to apply relations)
			for idx, (arg_data_name, arg_scalar_val) in sub_data_df.iterrows():
				rel_expr = re.sub(r'\${}\$'.format(arg_data_name), str(arg_scalar_val), rel_expr)
			rel_expr = "raw_rel_val = [(" + rel_expr + ")]" # the relation value is assigned to the variable "raw_rel_val"
			# execute raw_rel_val assignment
			try:
				local_dict = {}
				exec(rel_expr, globals(), local_dict)
				raw_rel_val = local_dict["raw_rel_val"]
			except SyntaxError:
				raise ValueError('Wrong syntax in the configuration values.')
			# update vgp data in the program (raw data are automatically converted to vgp data)
			res_prog[data_name] = raw_rel_val

	def update_function_data(self, res_prog):
		"""
		Description
		"""
		for funct_data_sh_name in FUNCT_DATA_SH_NAMES:
			funct_data_df = self.config_data_df[funct_data_sh_name].astype(str)
			funct_data_df.iloc[:, [0, 1]] = funct_data_sh.iloc[:, [0, 1]].astype(float) # the first two columns are casted as float

	# def get_config_df(self):
	# 	config_df = {}
	# 	for sheet_name in ALL_SHEET_NAMES:
	# 		if sheet_name in SHEET_NAMES_1:
	# 			config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str)
	# 		else:
	# 			config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str, skiprows=(0, 2))
	# 	return config_df