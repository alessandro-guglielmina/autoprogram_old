import pandas as pd
import numpy as np

from autoprogram import common

class WorkBook(object):

	def __init__(self, path):
		self.path = path
		self.wb = pd.read_excel(self.path, sheet_name =None, dtype=str) # read all the sheets

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

class ValuesDbWorkBook(WorkBook):

	def __init__(self, path):
		super().__init__(path)

	def get_common_data(self, fam_name): # (self, 'fam_name')
		# Get fam_val_names, and fam_rels (arrays)
		val_names = self.get_whole_column(fam_name, 'val_name')
		rels = self.get_whole_column(fam_name, 'rel')
		# Get val_addr, val_descr (DataFrame)
		act_sheet = self.wb[0]
		try:
			val_addr = act_sheet.val_addr[act_sheet.val_name.isin(val_names)].to_numpy()
			val_addr[pd.isnull(val_addr)] = None # pd.isnull needed to address nan values
			val_descr = act_sheet.val_descr[act_sheet.val_name.isin(val_names)].to_numpy()
			val_descr[pd.isnull(val_descr)] = None # pd.isnull needed to address nan values
		except KeyError:
			raise ValueError(f"Some values are missing from the 'general_values' sheet.")
		# Sect-percs and vals are set to None
		sect_percs = np.array([None for i in val_names])
		vals = np.array([None for i in val_names])
		# Build the common data DataFrame
		res = pd.DataFrame({	'val_name': pd.Series(val_names, dtype='str'),
			             		'rel': pd.Series(rels, dtype='str'),
			             		'val_addr': pd.Series(val_addr, dtype='str'),
			             		'val_descr': pd.Series(val_descr, dtype='str'),
			             		'sect_perc': pd.Series(sect_percs, dtype='object'),
			             		'val': pd.Series(vals, dtype='object')
			             		})
		if not (common.Variables.diam_addr in res.val_addr.tolist() and common.Variables.flute_len_addr in res.val_addr.tolist()):
			raise ValueError('Diameter or flute length value missing.')
		return res # DataFrame('val_addr', 'val_type', 'val_descr')


class ConfigValuesWorkBook(WorkBook):
	
	def __init__(self, path):
		super().__init__(path)