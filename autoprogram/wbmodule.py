import pandas as pd
import numpy as np

from autoprogram import common

class WorkBook(object):


	def __init__(self, path):

		self.path = path

		self.wb = pd.read_excel(self.path, sheet_name = None, dtype=str) # read all the sheets in the workbook and save it in  a dictionary of DataFrames where each DataFrame is a sheet


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

		return res


	# Get values array from single id
	def get_values_multi_ids(self, sheet, id_col, val_col, ids): # (self, 'sheet', 'id_col', 'val_col', ['id1', 'id2', ...])

		res = np.empty((1,0), dtype=str)

		for id_ in ids:

			np.append(res, self.get_values_single_id(sheet, id_col, val_col, id_))

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


	# def get_addr_from_names(self): #(self, list(['val_name1', 'val_name2', ...]))
	# 	res = self.db_get_values([self.general_values_table], [self.table_col[self.general_values_table]['val_name_col']],\
	# 		  [self.table_col[self.general_values_table]['val_addr_col']], val_names)
	# 	return res # list([addr1, addr2, ...])


def get_common_data():

	# Get val_names and rels from the configuration values workbook
	config_val_names = common.Variables.config_file_wb.get_whole_column(common.Variables.config_vals_sh_name,'val_name')

	config_rels = common.Variables.config_file_wb.get_whole_column(common.Variables.config_vals_sh_name, 'rel')

	try:

		config_val_addr = np.empty(0)

		config_val_descr = np.empty(0)

		for val_name in config_val_names:

			val_addr_i = common.Variables.values_database_sh.val_addr[common.Variables.values_database_sh.val_name == val_name].tolist()[0]

			val_descr_i = common.Variables.values_database_sh.val_descr[common.Variables.values_database_sh.val_name == val_name].tolist()[0]

			config_val_addr = np.append(config_val_addr, val_addr_i)

			config_val_descr = np.append(config_val_descr, val_descr_i)

		# No need for the following functions if no auxiliary parameters are used
		# config_val_addr[pd.isnull(config_val_addr)] = None # set nan values to None (pd.isnull needed to address nan values)

		# config_val_descr[pd.isnull(config_val_descr)] = None #  set nan values to None (pd.isnull needed to address nan values)

	except KeyError:

		raise ValueError(f"Some values are missing from the values database sheet.")

	# Sect-percs and vals are set to None
	config_sect_percs = np.array([None for i in config_val_names])

	config_vals = np.array([None for i in config_val_names])

	# Build the common data DataFrame
	res = pd.DataFrame({'val_name': pd.Series(config_val_names, dtype='str'),

	             		'rel': pd.Series(config_rels, dtype='str'),

	             		'val_addr': pd.Series(config_val_addr, dtype='str'),

	             		'val_descr': pd.Series(config_val_descr, dtype='str'),

	             		'sect_perc': pd.Series(config_sect_percs, dtype='object'),

	             		'val': pd.Series(config_vals, dtype='object')})

	if not common.Variables.diam_addr in res.val_addr.tolist():

		raise ValueError('Diameter value missing among the configuration values.')
		
	return res # DataFrame('val_addr', 'val_type', 'val_descr')