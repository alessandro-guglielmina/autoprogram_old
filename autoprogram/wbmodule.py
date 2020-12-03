import pandas as pd
import numpy as np

from autoprogram import common

class WorkBook(object):


	def __init__(self, path):

		self.path = path

		# read all the sheets in the workbook and save it in  a dictionary of DataFrames where each DataFrame is a sheet,
		#the first two rows are skippd because they contain comments
		self.wb = pd.read_excel(self.path, sheet_name = None, dtype=str, skiprows=(0, 1)) 


	# Get values array from single id
	def get_values_single_id(self, sheet, id_col, val_col, id_): # (self, 'sheet', 'id_col', 'val_col', 'id')

		try:

			act_sheet = self.wb[sheet]

		# If the sheet name is not in the wb returns ValueError
		except KeyError:

			raise ValueError(f'There is no {sheet} sheet in the workbook {self.path}.')

		try:

			res = act_sheet.loc[act_sheet[id_col] == id_, val_col].to_numpy() # array([val1, val2, ...])

			# Set nan values as None (pd.isna() method needed to address np.nan values)
			res[pd.isna(res)] = None

		# If the sheet has not id_col or val_col column returns ValueError
		except KeyError:

			raise ValueError(f'There is no {id_col} or {val_col} column in the {sheet} sheet, in the workbook {self.path}.')

		# If the id is not in the id column returns ValueError 
		if res.size == 0:

			raise ValueError(f'There is no {id_} id in the {id_col} column in the workbook {self.path}.')

		else:

			return res # ['val']


	# Get values array from single id
	def get_values_multi_ids(self, sheet, id_col, val_col, ids): # (self, 'sheet', 'id_col', 'val_col', ['id1', 'id2', ...])

		res = np.empty((1,0), dtype=str)

		for id_ in ids:

			res = np.append(res, self.get_values_single_id(sheet, id_col, val_col, id_)) # self.get_values_single_id(sheet, id_col, val_col, id_) returns a np.array([val]) value

		# Set nan values as None (pd.isna() method needed to address np.nan values)
		res[pd.isna(res)] = None

		return res # array([val1, val2, ...])


	def get_whole_column(self, sheet, val_col): # (self, 'sheet', 'val_col')

		try:

			act_sheet = self.wb[sheet]

		# If the sheet name is not in the wb returns ValueError
		except KeyError:

			raise ValueError(f'There is no {sheet} sheet in the workbook {self.path}.')

		try:

			res = act_sheet[val_col].to_numpy()

			# Set nan values as None (pd.isna() method needed to address np.nan values)
			res[pd.isna(res)] = None

		except KeyError:

			raise ValueError(f'There is no {val_col} column in the {sheet} sheet, in the workbook {self.path}.')

		return res # array([val1, val2, ...])