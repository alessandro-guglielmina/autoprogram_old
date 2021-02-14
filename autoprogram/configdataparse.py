import pandas as pd
import numpy as np
from pathlib import Path
import tkinter as tk

from autoprogram import common

CONFIG_FILE_FILENAME = "configuration file.xlsx"
DIAM_NAME_SH_NAME = "diameter name"
MASTER_SELECT_SH_NAME = "master selection"
INPUT_DATA_SH_NAME = "input data"
REL_DATA_SH_NAME = "relationships"
FUNCT_DATA_1_SH_NAME = "function data 1"
FUNCT_DATA_2_SH_NAME = "function data 2"
SCALE_VALS_SH_NAME = "scaled values"
SHEET_NAMES_1 = (SCALE_VALS_SH_NAME, INPUT_DATA_SH_NAME, REL_DATA_SH_NAME)
SHEET_NAMES_2 = (FUNCT_DATA_1_SH_NAME, FUNCT_DATA_2_SH_NAME) # read all the rows but the first 3
ALL_SHEET_NAMES = SHEET_NAMES_1 + SHEET_NAMES_2
VGP_DATA_SEP = ","
VAL_FUND_SEP = "-"

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
		self.config_data_df = pd.read_excel(self.path, sheet_name=None)
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
		raw_inp_data_list = []
		for inp_data_name in self.input_df.data_name:
			data_entry = input_data_page.nametowidget(ConfigData.to_widget_name(inp_data_name))
			raw_inp_data_i = data_entry.get()
			raw_inp_data_list.append(raw_inp_data_i)
		return pd.Series(raw_inp_data_list)

	def save_input_data(self, raw_inp_data: pd.Series):
		#print("raw_inp_data: ", raw_inp_data)
		vgp_inp_data = raw_inp_data.str.split(VGP_DATA_SEP, n=1, expand=True)
		self.input_df["inp_val"] = vgp_inp_data.loc[:, 0]
		try:
			self.input_df["inp_sect_perc"] = vgp_inp_data.loc[:, 1]
		except KeyError:
			self.input_df["inp_sect_perc"] = np.nan
	

	# def get_config_df(self):
	# 	config_df = {}
	# 	for sheet_name in ALL_SHEET_NAMES:
	# 		if sheet_name in SHEET_NAMES_1:
	# 			config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str)
	# 		else:
	# 			config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str, skiprows=(0, 2))
	# 	return config_df