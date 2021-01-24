import pandas as pd

from autoprogram import common

ALL_SHEET_NAMES = common.SHEET_NAMES_1 + common.SHEET_NAMES_2

class ConfigWorkBook(object):
	"""
	Class escription
	"""
	def __init__(self, path):
		self.path = path
		self.df_setup()
		self.diam_id = self.df["diameter_id"].at[0, "diam_id"]
		self.input_vals_ids = self.df["input values"]["val_id"]
		self.rel_vals = self.df["relationships"]

	def df_setup(self):
		self.df = {}
		for sheet_name in ALL_SHEET_NAMES:
			if sheet_name in common.SHEET_NAMES_1
				self.df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str)
			else:
				self.df[sheet_name] = pd.read_excel(self.path, sheet_name = sheet_name, dtype=str, skiprows=(0, 2))