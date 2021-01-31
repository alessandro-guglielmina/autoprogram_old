import pandas as pd
from pathlib import Path

from autoprogram import common

CONFIG_FILE_FILENAME = "configuration file.xlsx"
DIAM_NAME_SH_NAME = "diameter name"
MASTER_SELECT_SH_NAME = "master selection"
INPUT_VALS_SH_NAME = "input values"
REL_VALS_SH_NAME = "relationships"
FUNCT_VALS_1_SH_NAME = "function values 1"
FUNCT_VALS_2_SH_NAME = "function values 2"
SCALE_VALS_SH_NAME = "scaled values"
SHEET_NAMES_1 = (SCALE_VALS_SH_NAME, INPUT_VALS_SH_NAME, REL_VALS_SH_NAME)
SHEET_NAMES_2 = (FUNCT_VALS_1_SH_NAME, FUNCT_VALS_2_SH_NAME) # read all the rows but the first 3
ALL_SHEET_NAMES = SHEET_NAMES_1 + SHEET_NAMES_2


class ConfigFile(object):
	"""
	Class description
	"""
	def __init__(self, fam_dir_path):
		self.path = Path(fam_dir_path).joinpath(CONFIG_FILE_FILENAME)
		# self.get_master_select_df()
		#self.config_df = self.get_config_df()
		#diam_name = self.df[COMMON_OD_SH_NAME].at[0, "diam_name"]
		# input_vals_names = self.config_df[INPUT_VALS_SH_NAME]["val_name"]
		# input_vals_descr = self.config_df[INPUT_VALS_SH_NAME]["val_descr"]
		# rel_vals_names = self.config_df[REL_VALS_SH_NAME]["val_name"]
		#super().__init__({"input_vals_names": [input_vals_names], "input_vals_descr": [input_vals_descr]})

	@property
	def diam_name(self):
		"""
		Description
		"""
		diam_name_df = pd.read_excel(self.path, sheet_name=DIAM_NAME_SH_NAME, dtype=str)
		return diam_name_df.at[0, "diam_name"]

	@property
	def input_vals_df(self):
		return pd.read_excel(self.path, sheet_name=DIAM_NAME_SH_NAME, dtype=str)
	

	def get_config_df(self):
		config_df = {}
		for sheet_name in ALL_SHEET_NAMES:
			if sheet_name in SHEET_NAMES_1:
				config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str)
			else:
				config_df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str, skiprows=(0, 2))
		return config_df