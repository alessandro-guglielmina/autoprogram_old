import sqlite3 as sql
import numpy as np
import pandas as pd
from pathlib import Path
import copy

VGPIO_MODULE_PATH = Path(__file__) # vgpio.py (this module) path
VGPIO_PACKAGE_PATH = VGPIO_MODULE_PATH.parent # directory containing vgpio.py
ADDR_MAP_FILENAME = "address mapper.xlsx"
ADDR_MAP_PATH = VGPIO_PACKAGE_PATH.joinpath(ADDR_MAP_FILENAME) # the file "address mapper.xlsx" is always read from the same directory of the vgpio.py module (this module)
ADDR_MAP_SHEET_NAME = "address mapper"

try:
	ADDR_MAP_DF = pd.read_excel(ADDR_MAP_PATH, sheet_name = ADDR_MAP_SHEET_NAME, dtype=str)
except FileNotFoundError:
 	raise ValueError(f"No such an address mapper file: {ADDR_MAP_FILENAME}")

TABLE_ATTRIBUTES = ("id_col", "val_col", "sect_perc_col")
CURVE = pd.Series(("CU_Id", "CU_Type", np.nan), name="Curve", index=TABLE_ATTRIBUTES)
PARAMETER = pd.Series(("PA_Id", "PA_Value", np.nan), name="Parameter", index=TABLE_ATTRIBUTES)
VGP_DATA = pd.Series(("ID", "PartialFullname", np.nan), name="VGP_Data", index=TABLE_ATTRIBUTES)
VGP_VALUE_DOUBLE = pd.Series(("D_Id", "D_Value", np.nan), name="VGP_Value_Double", index=TABLE_ATTRIBUTES)
VGP_VALUE_FUNCTIOND = pd.Series(("D_Id", "D_Value", "D_Parameter"), name="VGP_Value_FunctionD", index=TABLE_ATTRIBUTES)
VGP_VALUE_INT = pd.Series(("D_Id", "D_Value", np.nan), name="VGP_Value_Int", index=TABLE_ATTRIBUTES)
R_TABLE_SERIES = (CURVE, VGP_DATA)
RW_TABLE_SERIES = (PARAMETER, VGP_VALUE_DOUBLE, VGP_VALUE_FUNCTIOND, VGP_VALUE_INT)
R_TABLES = pd.DataFrame(columns=TABLE_ATTRIBUTES)
RW_TABLES = pd.DataFrame(columns=TABLE_ATTRIBUTES)

for r_table_series in R_TABLE_SERIES:
	R_TABLES.loc[r_table_series.name] = r_table_series

for rw_table_series in RW_TABLE_SERIES:
	RW_TABLES.loc[rw_table_series.name] = rw_table_series
ALL_TABLES = R_TABLES.append(RW_TABLES)
SEPARATOR = "."


class VgpProgram(object):
	"""
	This class is an I/O interface to the VGPro program (version 1.29)
	"""
	def __init__(self, path):
		# path: .vgp file path
		self.path = path

	# __enter__ and __exit__ methods needed to use context managers
	def __enter__(self):
		self.con = sql.connect(self.path)
		self.vgp_read()
		return self

	def __exit__(self, exc_class, exc, traceback):
		# write DataFrame values into the .vgp file
		self.vgp_write()
		self.con.commit()
		self.con.close()
		pass

	def read_source_db(self):
		"""
		This method read the specified database tables and write them into corresponding pd.DataFrame object,
		all of those are wrapped into the dictionary self.vgp_dict
		"""
		self.vgp_dict = {}
		for table_name, table in ALL_TABLES.iterrows():
			self.vgp_dict[table.name] = pd.read_sql(f"SELECT * FROM {table.name}", self.con)
			# Additional characters in the PA_Value column in the Parameter table (" ", "°" and "mm") have to be deleted and values cast to float64
			if table.name == PARAMETER.name:
				self.vgp_dict[table.name][PARAMETER.val_col] = self.vgp_dict[table.name][PARAMETER.val_col].str.rstrip(" °mm").astype("float64")

	def scalars_to_array(self):
		"""
		The values in the val_col columns of each DataFRame are set to be arrays in order to deal with consistent data formats;
		in the VGP_Value_FunctionD DataFrame all the columns but the id_col are set to be arrays, as not only the val_col is meant to represent arrays;
		the id_col is left as scalr since it's an argument for queries dealing with scalar values
		"""
		for table_name, table in RW_TABLES.iterrows():
			if table.name == VGP_VALUE_FUNCTIOND.name:
				# All the columns in VGP_Value_FunctionD table are grouped by the D_Id column and values in other columns collected in pd.array objects
				df_gr_by_temp = self.vgp_dict[table.name].groupby(table.id_col)
				df_temp = df_gr_by_temp.agg(pd.array)
				df_temp.reset_index(inplace=True)
				self.vgp_dict[table.name] = df_temp
				del df_gr_by_temp, df_temp
			else:
				# For the other tables, only the val_col is set to be as np.array type (for value data types consistency), other columns are not changed, since they can be arguments for queries
				self.vgp_dict[table.name][table.val_col] = self.vgp_dict[table.name][table.val_col].apply(lambda x: np.asarray([x]))
		
					
	def elem_wise_query(self, df, id_col, _id, res_col):
		"""
		This method returns a single result value from a query; the arguments are: self, the id (single value), the DataFrame (df), the id column (id_col)
		and the result value column (res_col), it returns a single value as well. This function combined with pd.apply() method performs element-wise queries.
		_id is the first positional argument because corresponds to the series elements automatically passed in by the pd.apply() method
		"""
		filt = (df[id_col] == _id)
		try:
			return  df[filt].iloc[0].at[res_col]
		# if the query doesn't return anything, the result is set to np.nan
		except IndexError:
			return np.nan

	def get_val_addr(self, table_name):
		"""
		This method returns a pd.Series of addresses to be put as index of VGP_Value_Double, VGP_Value_Int or VGP_Value_FunctionD DataFrames (not Parameter DataFrame!!!),
		in order to access them more easily by value addresses. The argument table_name is a string (e.g. "VGP_Value_Double"), while the output is a pd.Series containing
		all the addresses of the specified table (i.e. data type)
		"""
		val_addr_ids = self.vgp_dict[table_name][VGP_VALUE_DOUBLE.id_col] # equivalent to VGP_VALUE_FUNCTIOND.id_col or VGP_VALUE_INT.id_col
		addr_qry = lambda _id: self.elem_wise_query(self.vgp_dict[VGP_DATA.name], VGP_DATA.id_col, _id, VGP_DATA.val_col)
		val_addr = val_addr_ids.apply(addr_qry)
		val_addr.rename("address", inplace=True)
		return val_addr


	def get_param_addr(self):
		"""
		This method returns a pd.Series of addresses to be put as index of Parameter DataFrame,
		in order to access them more easily by value addresses. The output is a pd.Series containing
		Parameter addresses, that are ustom strings acting as unique identifiers
		"""
		param_names = self.vgp_dict[PARAMETER.name]["PA_Name"]
		param_curve_id_qry = lambda param_name: self.elem_wise_query( self.vgp_dict[PARAMETER.name], "PA_Name", param_name, "PA_CurveId")
		param_curve_ids = param_names.apply(param_curve_id_qry)
		param_curve_type_qry = lambda curve_id: self.elem_wise_query( self.vgp_dict[CURVE.name], CURVE.id_col, curve_id, CURVE.val_col)
		param_curve_types = param_curve_ids.apply(param_curve_type_qry)
		param_addr = param_curve_types.str.cat(param_names, sep = SEPARATOR)
		param_addr.rename("address", inplace=True)
		return param_addr


	def set_val_addr_idx(self):
		"""
		This method set the index to all the value DataFrames (not Parameter DataFrame!!!) by applying self.get_val_addr()
		"""
		for table_name in ("VGP_Value_Double", "VGP_Value_Int", "VGP_Value_FunctionD"):
			self.vgp_dict[table_name].set_index(self.get_val_addr(table_name), inplace=True)

	def set_param_addr_idx(self):
		"""
		This method set the index to the Parameter DataFrame by applying self.get_param_addr()
		"""
		self.vgp_dict["Parameter"].set_index(self.get_param_addr(), inplace=True)

	def set_addr_idx(self):
		"""
		This method wraps self.set_val_addr_idx() and self.set_param_addr_idx() together
		"""
		self.set_val_addr_idx()
		self.set_param_addr_idx()

	def vgp_read(self):
		"""
		This method wraps the three methods to setup the self.vgp_dict attribute, the tables dictionary, so that it's easier to work with
		"""
		self.read_source_db()
		self.scalars_to_array()
		self.set_addr_idx()

	def array_to_scalars(self):
		"""
		This method reset the original DataFrame formats in order to be written in the .vgp file
		"""
		for table_name, table in RW_TABLES.iterrows():
			if table.name == VGP_VALUE_FUNCTIOND.name:
				# VGP_Value_FunctionD formatting
				df_temp = self.vgp_dict[table.name] # assign to VGP_Value_FunctionD DataFrame
				df_temp.set_index([self.vgp_dict[table.name].index, table.id_col], inplace=True) # set current index and D_Id column as index, so they are duplicated while stacking
				df_temp = df_temp.apply(lambda x: x.apply(pd.Series).stack()) # x is a DataFrame corresponding to a df_temp column, x.apply(pd.Series) is a column DataFrame whose each element (np.array) has been transformed into a pd.Series
				df_temp.reset_index(level=table.id_col, inplace=True) # move the id_col from index to actual DataFrame column
				df_temp = df_temp.droplevel(-1) # drop the index level coming from index duplication (populated by 0, 1, ...)
				self.vgp_dict[table.name] = df_temp
				del df_temp
			else:
				# For other tables, the arrays in the val_col are reset to be scalar values, other columns are not changed
				self.vgp_dict[table.name][table.val_col] = self.vgp_dict[table.name][table.val_col].apply(lambda x: x[0])
				
	def write_source_db(self):
		"""
		Description
		"""
		for table_name, table in RW_TABLES.iterrows():
			# Reset Parameter values to be string in order to not alter the original .vgp file data types
			if table.name == PARAMETER.name:
				self.vgp_dict[table.name][PARAMETER.val_col] = self.vgp_dict[table.name][table.val_col].astype("str")
			self.vgp_dict[table.name].to_sql(table.name, self.con, if_exists='replace', index=False)

	def vgp_write(self):
		"""
		This method reset the tables so that they can be written in the db as the original ones, then they are written in the source db itself
		"""
		self.array_to_scalars()
		 # self.write_source_db()
		delattr(self, "vgp_dict")

	def val_names_to_addr(self, val_names):
		"""
		This method convert the value names contained in the val_names Series into their correspondent address by means of the ADDR_MAP_DF,
		the DataFrame corresponding to the address mapper workbook
		"""
		val_addr_qry = lambda val_name: self.elem_wise_query(ADDR_MAP_DF, "val_name", val_name, "val_addr")
		val_addr = val_names.apply(val_addr_qry)
		mapped_val_names_filt = val_addr.notna()
		if mapped_val_names_filt.all():
			return val_addr
		else:
			not_mapped_val_names = val_names[~mapped_val_names_filt]
			raise ValueError(f"Not mapped value names: {not_mapped_val_names.to_list()}")

	def elem_wise_param_addr_build(self, param_name):
		"""
		This method builds the parameter address (custom string collecting the curve type and the parameter name, acting as unique identifier)
		from the parameter name (RConnect id, i.e. a string value); it has to be used with the pd.apply() method in order to convert eah name
		in the Series into its correspondent address
		"""
		split_param_name = param_name.split(SEPARATOR)
		if split_param_name[0] == "Tool":
			param_addr = "Rollomatic.LibCurve.Data.Curves.ToolProfileCurve" + SEPARATOR + split_param_name[-1]
			return param_addr
		elif split_param_name[0] == "Blank":
			param_addr = "Rollomatic.LibCurve.Data.Curves.BlankProfileCurve" + SEPARATOR + split_param_name[-1]
			return param_addr
		else:
			raise ValueError(f"No such a parameter name: {param_name}")

	def param_names_to_addr(self, param_names):
		"""
		This method takes a pd.Series as argument with the selected parameter names and returns a pd.Series of the same length with the
		correspondent parameter addresses (unique identifiers)
		"""
		param_addr = param_names.apply(self.elem_wise_param_addr_build)
		return param_addr

	def names_to_addr(self, names, is_param_filt, is_val_filt):
		"""
		Pipeline 1st method: it takes a pd.Series of names, parameter and value boolean filters as arguments
		and returns a pd.Series of corresponding addresses
		"""
		param_names = names[is_param_filt] # applying a pd.Series boolean filter to a pd.Series returns a pd.Series as well with only those elements corresponding to True values
		val_names = names[is_val_filt]
		addr = pd.Series([np.nan for i in range(names.size)], dtype=object)
		addr[is_param_filt] = self.param_names_to_addr(param_names)
		addr[is_val_filt] = self.val_names_to_addr(val_names)
		return addr

	def addr_to_tables(self, addr, is_param_filt, is_val_filt):
		"""
		Pipeline 2nd method: it takes a pd.Series of addresses, a pd.Series of names parameter and value boolean filters
		as arguments and returns a pd.Series of corresponding table names
		"""
		tables = pd.Series([np.nan for i in range(addr.size)], dtype=object)
		tables[is_param_filt] = addr[is_param_filt].apply(lambda x: PARAMETER.name)
		table_from_val_addr_qry = lambda val_addr: self.elem_wise_query(self.vgp_dict[VGP_DATA.name], VGP_DATA.val_col, val_addr, "VGP_Value_Type")
		tables[is_val_filt] = addr[is_val_filt].apply(table_from_val_addr_qry)
		not_in_prog_addr_filt = tables.isna()
		if not_in_prog_addr_filt.any():
			not_in_prog_addr = addr[not_in_prog_addr_filt]
			raise ValueError(f"Value addresses not in the program: {not_in_prog_addr.to_list()}")
		else:
			return tables

	def names_to_query_args_df(self, names, is_param_filt, is_val_filt):
		"""
		This method takes a pd.Series of names and value boolean filters as arguments and returns a pd.DataFrame of
		corresponding query arguments (tables and addresses)
		"""
		addr = self.names_to_addr(names, is_param_filt, is_val_filt)
		tables = self.addr_to_tables(addr, is_param_filt, is_val_filt)
		qry_args_df = pd.DataFrame({"table": tables, "addr": addr})
		return qry_args_df

	def is_param(self, names):
		"""
		This method takes a Series of names as argument and returns a boolean filter (pd.Series) that is True for those values being parameters
		(not in the address mapper workbook)
		"""
		is_param_filt = ~names.isin(ADDR_MAP_DF.val_name)
		return is_param_filt

	def is_val(self, names):
		"""
		This method takes a Series of names as argument and returns a boolean filter (pd.Series) that is True for those values being values
		(in the address mapper workbook)
		"""
		is_val_filt = names.isin(ADDR_MAP_DF.val_name)
		return is_val_filt

	def get_vals_qry(self, qry_args):
		"""
		Return Value type values
		"""
		if qry_args.table != PARAMETER.name:
			val = self.vgp_dict[qry_args.table].loc[qry_args.addr, RW_TABLES.loc[qry_args.table, "val_col"]]
		# For Parameter values duplicates must be dropped in order to return a single value per label
		else:
			no_dupl_param_df = self.vgp_dict[qry_args.table][~self.vgp_dict[qry_args.table].index.duplicated(keep='first')]
			val = no_dupl_param_df.loc[qry_args.addr, RW_TABLES.loc[qry_args.table, "val_col"]]
		return val

	def get_sect_percs_qry(self, qry_args):
		"""
		Return Parameter type values
		"""
		try:
			sect_perc = self.vgp_dict[qry_args.table].loc[qry_args.addr, RW_TABLES.loc[qry_args.table, "sect_perc_col"]]
		except KeyError:
			sect_perc = np.nan
		return sect_perc

	def __getitem__(self, names):
		"""
		This method allows to get elements by indexing, it can take strings and array-like of strings as arguments
		"""
		names = pd.Series(names)
		names_len = names.size
		# Get the boolean filters relative to those names being Parameter type and those being Value type
		# (constant through the whole __getitem__ method)
		is_param_filt = self.is_param(names)
		is_val_filt = self.is_val(names)
		# Get a DataFrame with two columns, one is for tables ("table" column) and one for addresses ("addr" column)
		qry_args_df = self.names_to_query_args_df(names, is_param_filt, is_val_filt)
		qry_args_df = qry_args_df[~qry_args_df.index.duplicated(keep='first')] # delete duplicates due to Parameter values
		# Iterate over the two columns: each qry_args_df row is passed as argument to the function inside .apply() (self.get_vals_qry and self.get_sect_percs_qry,
		# each taking the arguments qry_args.addr and qry_args.table)
		vals = qry_args_df.apply(self.get_vals_qry, axis=1) # .apply() method applied to a DataFrame with axis=1 iterates over each row (pd.Series)
		sect_percs = qry_args_df.apply(self.get_sect_percs_qry, axis=1) # .apply() method applied to a DataFrame with axis=1 iterates over each row (pd.Series)
		del is_param_filt, is_val_filt
		data = pd.DataFrame({"sect_perc": sect_percs, "val": vals}).set_index(names)
		return data

	def set_vals_qry(self, qry_args_value):
		"""
		EXCEPTIONS TO BE ADDED!!!
		"""
		# print(self.vgp_dict[qry_args_value.table].loc[qry_args_value.addr, RW_TABLES.loc[qry_args_value.table, "val_col"]])
		# print(qry_args_value.val)
		# input("pause")
		self.vgp_dict[qry_args_value.table].loc[qry_args_value.addr, RW_TABLES.loc[qry_args_value.table, "val_col"]] = [qry_args_value.val]
		self.vgp_dict[qry_args_value.table].loc[qry_args_value.addr, RW_TABLES.loc[qry_args_value.table, "sect_perc_col"]] = [qry_args_value.sect_perc]

	def __setitem__(self, names, values):
		"""
		EXCEPTIONS TO BE ADDED!!!
		"""
		names = pd.Series(names)
		names_len = names.size
		is_param_filt = self.is_param(names)
		is_val_filt = self.is_val(names)
		qry_args_df = self.names_to_query_args_df(names, is_param_filt, is_val_filt)
		qry_args_df = qry_args_df[~qry_args_df.index.duplicated(keep='first')]
		qry_args_values_df = pd.concat([qry_args_df, values], axis=1)
		qry_args_values_df.apply(self.set_vals_qry, axis=1)

	# Parameter_table_names = 'Parameter'

	# VGP_Data_table_names = 'VGP_Data'

	# VGP_Value_Double_table_names = 'VGP_Value_Double'

	# VGP_Value_Int_table_names = 'VGP_Value_Int'

	# VGP_Value_FunctionD_table_names = 'VGP_Value_FunctionD'

	# # this vgp_dictionary collect the column strucure of all the used TABLE_NAMES present in the VGP program
	# table_names_col_vgp_dict = {
	# 					'id_col' : {Parameter_table_names : 'PA_Id', VGP_Data_table_names : 'ID', VGP_Value_Double_table_names : 'D_Id', VGP_Value_Int_table_names : 'D_Id', VGP_Value_FunctionD_table_names : 'D_Id', Curve_table_names : None},
	# 					'sect_perc_col' : {Parameter_table_names : None, VGP_Data_table_names : None, VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None , VGP_Value_FunctionD_table_names : 'D_Parameter', Curve_table_names : None},
	# 					'val_col' : {Parameter_table_names : 'PA_Value', VGP_Data_table_names : None, VGP_Value_Double_table_names : 'D_Value', VGP_Value_Int_table_names : 'D_Value', VGP_Value_FunctionD_table_names : 'D_Value', Curve_table_names : None},
	# 					'val_addr_col' : {Parameter_table_names : None, VGP_Data_table_names : 'PartialFullname', VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None, VGP_Value_FunctionD_table_names : None, Curve_table_names : None},
	# 					'name_col' : {Parameter_table_names : 'PA_Name', VGP_Data_table_names : None, VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None, VGP_Value_FunctionD_table_names : None, Curve_table_names : None},
	# 					'datatype_col' : {Parameter_table_names : None, VGP_Data_table_names : 'VGP_Value_Type', VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None, VGP_Value_FunctionD_table_names : None, Curve_table_names : None},
	# 					'curve_id_col' : {Parameter_table_names : 'PA_CurveId', VGP_Data_table_names : None, VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None, VGP_Value_FunctionD_table_names : None, Curve_table_names  : 'CU_Id'},
	# 					'curve_type_col' : {Parameter_table_names : None, VGP_Data_table_names : None, VGP_Value_Double_table_names : None, VGP_Value_Int_table_names : None, VGP_Value_FunctionD_table_names : None, Curve_table_names  : 'CU_Type'},
	# 				 }

	# table_names_col = pd.DataFrame(table_names_col_vgp_dict)

	# # Get the Parameter id from the parameter name (and curve type, because more parameters have the same name, but only one parameter per curve type)
	# def get_param_id_from_addr(self, addr): # (self, row.addr)

	# 	try:

	# 		addr = addr.split(common.Variables.separator) # split the address in parameter type and parameter name

	# 		curve_type = addr[0]

	# 		param_name = addr[1]

	# 	except IndexError:

	# 		raise ValueError(f'Wrong Parameter address or value name not present in the program: {addr}.')

	# 	# Get the possible curve ids from Curve table_names
	# 	poss_curve_ids = self.get_values_single_id(self.Curve_table_names, self.table_names_col.loc[self.Curve_table_names, 'curve_type_col'],\

	# 					 self.table_names_col.loc[self.Curve_table_names, 'curve_id_col'], curve_type) # [poss_cu_id1, poss_cu_id2, ...]

	# 	# Get all the curve ids corresponding to the parameter name
	# 	same_name_curve_ids = self.get_values_single_id(self.Parameter_table_names, self.table_names_col.loc[self.Parameter_table_names, 'name_col'],\

	# 						  self.table_names_col.loc[self.Parameter_table_names, 'curve_id_col'], param_name)

	# 	# Get all the parameter ids corresponding to the parameter name
	# 	same_name_param_ids = self.get_values_single_id(self.Parameter_table_names, self.table_names_col.loc[self.Parameter_table_names, 'name_col'],\

	# 						   self.table_names_col.loc[self.Parameter_table_names, 'id_col'], param_name)

	# 	# Collect curve ids and parameter ids in a DataFrame
	# 	param_data = pd.DataFrame({'curve_id': pd.Series(same_name_curve_ids, dtype = 'str'),

	# 							   'param_id': pd.Series(same_name_param_ids, dtype = 'str'),})

	# 	res = param_data.loc[param_data.curve_id.isin(poss_curve_ids), 'param_id'].values[0] # the query could returns 2 values, but changing one, vgp automatically update the other one
	# 																						 # otherwise we should treat it as a function value																				
	# 	return res # param_id

	
	# # vgp_get_dtype_n_id() auxiliary function
	# def get_dtype_n_id_from_single_addr(self, addr): #(self, 'val_address')

	# 	try:

	# 		dtype = self.get_values_single_id(self.VGP_Data_table_names, self.table_names_col.loc[self.VGP_Data_table_names, 'val_addr_col'], self.table_names_col.loc[self.VGP_Data_table_names, 'datatype_col'], addr)[0]

	# 		id_ = self.get_values_single_id(self.VGP_Data_table_names, self.table_names_col.loc[self.VGP_Data_table_names, 'val_addr_col'], self.table_names_col.loc[self.VGP_Data_table_names,'id_col'], addr)[0]

	# 		res = np.asarray([[dtype, id_]])

	# 	# If get_values() returns a Parameter
	# 	except:

	# 		id_ = self.get_param_id_from_addr(addr)

	# 		res = np.asarray([[self.Parameter_table_names, id_]]) # strings

	# 	return res #array([['table_names', 'id']])


	# # Returm the data type and the id corresponding to a certain address array for data types VGP_Value_Double, VGP_Value_Int, VGP_Value_String, ... (not Parameter)
	# def get_dtypes_n_ids(self, addr): #(self, array(['val_addr1', 'val_addr2', ...]))

	# 	res = np.empty((0,2))

	# 	for i in addr:

	# 		dtype_n_id_i = self.get_dtype_n_id_from_single_addr(i)

	# 		res = np.append(res, dtype_n_id_i, axis = 0)

	# 	return res # array([['table_names1', 'id1'], ['table_names2', 'id2'], ...])


	# # Get id_col and val_col alongside table_names and id, obtained with the previous function (values that must not be averaged are skipped because of the previous function)
	# def get_qry_data_from_addr(self, addresses): #(self, ['val_addr1', 'val_addr2', ...])) T.B.N. addresses not belonging to TABLE_NAMES 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted

	# 	dtypes_n_ids = self.get_dtypes_n_ids(addresses)

	# 	columns = ['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id']

	# 	res = pd.DataFrame(columns = columns, dtype = str)

	# 	for dts_n_ids, addr in zip(dtypes_n_ids, addresses):

	# 		dtype = dts_n_ids[0]

	# 		id_ = dts_n_ids[1]

	# 		if dtype in [self.Parameter_table_names, self.VGP_Value_Double_table_names, self.VGP_Value_Int_table_names]:

	# 			res = res.append({'val_addr' : addr, 'table_names' : dtype, 'id_col' : self.table_names_col.loc[dtype, 'id_col'], 'sect_perc_col' : None, 'val_col' : self.table_names_col.loc[dtype, 'val_col'],\

	# 				  'id' : id_}, ignore_index = True)

	# 		elif dtype == self.VGP_Value_FunctionD_table_names:

	# 			res = res.append({'val_addr' : addr, 'table_names' : dtype, 'id_col' : self.table_names_col.loc[dtype, 'id_col'], 'sect_perc_col' : self.table_names_col.loc[dtype, 'sect_perc_col'],\

	# 				  'val_col' : self.table_names_col.loc[dtype, 'val_col'],'id' : id_}, ignore_index = True)

	# 		else:

	# 			raise ValueError(f'Data in {dtype} must not be processed.')

	# 	return res # DataFrame(['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id'])
	# 	# T.B.N. addresses not belonging to TABLE_NAMES 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted


	# # Return a list containng both scalar values and function values in string format (to obtain float values the output must be cast!!!)
	# def get_values_from_qry_data(self, qry_data): #(self, DataFrame(['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id'])) T.B.N. addresses not belonging to TABLE_NAMES 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted

	# 	columns = ['sect_perc', 'val']

	# 	res = pd.DataFrame(columns = columns, dtype = float)

	# 	for i, row in qry_data.iterrows(): # row is the pd.Series corresponding to a specific row

	# 		# If the value is a scalar integer
	# 		if row.table_names == self.VGP_Value_Int_table_names:

	# 			val = self.get_values_single_id(row.table_names, row.id_col, row.val_col, row.id) # value can be either an array of string or None values


	# 			if val:

	# 				val = val.astype(int)

	# 			else:

	# 				val = np.array([np.nan])

	# 			res = res.append({'sect_perc' : None, 'val' : val}, ignore_index = True)

	# 		# If the value is a scalar float
	# 		if row.table_names in [self.Parameter_table_names, self.VGP_Value_Double_table_names]:

	# 			val = self.get_values_single_id(row.table_names, row.id_col, row.val_col, row.id) # value can be either an array of string or None values

	# 			if val:

	# 				val = np.char.rstrip(val, ' mm°')

	# 				val = val.astype(float)

	# 			else:

	# 				val = np.array([np.nan])

	# 			res = res.append({'sect_perc' : None, 'val' : val}, ignore_index = True)

	# 		# If the value is a function value:
	# 		elif row.table_names == self.VGP_Value_FunctionD_table_names:

	# 			sect_perc = self.get_values_single_id(row.table_names, row.id_col, row.sect_perc_col, row.id) # value can be either array of strings or None values

	# 			val = self.get_values_single_id(row.table_names, row.id_col, row.val_col, row.id)

	# 			np.char.rstrip(sect_perc, ' mm°')

	# 			np.char.rstrip(val, ' mm°')

	# 			sect_perc = sect_perc.astype(float)

	# 			val = val.astype(float)

	# 			res = res.append({'sect_perc' : sect_perc, 'val' : val}, ignore_index = True)

	# 	return res  # DataFrame(['sect_perc', 'val'])


	# def get_values_from_addr(self, param_addr): # (self, list(['par_addr1', 'par_addr2', ...]))

	# 	# Get query data from addresses
	# 	qry_data = self.get_qry_data_from_addr(param_addr)

	# 	return self.get_values_from_qry_data(qry_data) # DataFrame(['sect_perc', 'val'])


	# def get_addr_from_names(self, param_names):

	# 	param_addr = []

	# 	for param_name in param_names:

	# 		# return a 1-sized pd.Series object with the address corresponding to the name (if the name and address have been recorded)
	# 		param_addr_i = common.Variables.values_database_sh.val_addr[common.Variables.values_database_sh.val_name == param_name]

	# 		try:

	# 			param_addr_i = param_addr_i.iloc[0] # returns the string value of the address

	# 		except IndexError:

	# 			raise ValueError(f'No such a name in the values database: {param_name}.') # if the name and address have not been recorded yet, raises a ValueError

	# 		param_addr.append(param_addr_i)

	# 	return param_addr


	# def get_values_from_names(self, param_names): # (self, list(['par_name1', 'par_name2', ...]))

	# 	param_addr = self.get_addr_from_names(param_names)

	# 	qry_data = self.get_qry_data_from_addr(param_addr)

	# 	return self.get_values_from_qry_data(qry_data) # DataFrame(['sect_perc', 'val'])


	# # Return a list containng both scalar values and function values in string format (to obtain float values the output must be cast!!!)
	# def update_values_from_qry_data(self, qry_data, vals): #(self, DataFrame(['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id'])), DataFrame(['sect_perc', 'val'])

	# 	for qry_data_iterrows, vals_iterrows in zip(qry_data.iterrows(), vals.iterrows()):

	# 		qry_i, qry_row = qry_data_iterrows

	# 		val_i, val_row = vals_iterrows

	# 		# If the value is a float scalar:
	# 		if qry_row.table_names in [self.Parameter_table_names, self.VGP_Value_Double_table_names]:

	# 			#print(qry_row.table_names, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val)

	# 			self.update_values_single_id(qry_row.table_names, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val) # no need to cast, as all the values are float already

	# 		# If the value is an integer scalar:
	# 		elif qry_row.table_names == self.VGP_Value_Int_table_names:

	# 			self.update_values_single_id(qry_row.table_names, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val) # value must be cast,from float to integer

	# 		# If the value is a function:
	# 		elif qry_row.table_names == self.VGP_Value_FunctionD_table_names:

	# 			# If a function value has a single input
	# 			val_len = len(val_row.val)

	# 			# if not hasattr(val_row.val, "__len__") and val_row.sect_perc == None:
	# 			if val_len == 1 and val_row.sect_perc is None:

	# 				val_row.val = [val_row.val[0], val_row.val[0]]

	# 				val_row.sect_perc = [0, 1]

	# 			elif val_len > 1 and val_row.sect_perc is None:

	# 				nums = range(val_len)

	# 				den = val_len - 1

	# 				val_row.sect_perc = [num / den for num in nums]

	# 			self.update_values_single_id(qry_row.table_names, qry_row.id_col, qry_row.sect_perc_col, qry_row.id, val_row.sect_perc)

	# 			self.update_values_single_id(qry_row.table_names, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val)

	# 		else:

	# 			raise ValueError('Wrong datatype provided')


	# def update_values_from_addr(self, param_addr, vals): # (self, list(['par_addr1', 'par_addr2', ...]), DataFrame(['sect_perc', 'val']))

	# 	# Get query data from addresses
	# 	qry_data = self.get_qry_data_from_addr(param_addr)

	# 	return self.update_values_from_qry_data(qry_data, vals)


	# def update_values_from_names(self, param_names, vals): # (self, list(['par_name1', 'par_name2', ...]), DataFrame(['sect_perc', 'val']))

	# 	param_addr = self.get_addr_from_names(param_names) # ERROR

	# 	qry_data = self.get_qry_data_from_addr(param_addr)

	# 	return self.update_values_from_qry_data(qry_data, vals)


	# # Get all the query data that have to be scaled (without passing through addresses)
	# def get_to_scale_qry_data(self):

	# 	# Get Parameter addresses, composing parameter name and curve type
	# 	par_addr_part2 = self.get_whole_column(self.Parameter_table_names, self.table_names_col.loc[self.Parameter_table_names, 'name_col'])

	# 	par_curve_ids = self.get_whole_column(self.Parameter_table_names, self.table_names_col.loc[self.Parameter_table_names, 'curve_id_col'])

	# 	curve_ids = self.get_whole_column(self.Curve_table_names, self.table_names_col.loc[self.Curve_table_names, 'curve_id_col'])

	# 	par_addr_part1 = self.get_values_multi_ids([self.Curve_table_names], [self.table_names_col.loc[self.Curve_table_names, 'curve_id_col']], [self.table_names_col.loc[self.Curve_table_names, 'curve_type_col']], par_curve_ids)

	# 	par_addr = pd.Series(par_addr_part1).str.cat(par_addr_part2, sep = common.Variables.separator).to_list()

	# 	# Get Parameter dtypes and ids
	# 	par_dtypes = [self.Parameter_table_names for i in par_addr]

	# 	par_ids = self.get_whole_column(self.Parameter_table_names, self.table_names_col.loc[self.Parameter_table_names, 'id_col'])

	# 	# Get VGP_Values addresses, dtypes and ids
	# 	val_addr = self.get_whole_column(self.VGP_Data_table_names, self.table_names_col.loc[self.VGP_Data_table_names, 'val_addr_col']) # array(['val1', 'val2', ...])

	# 	val_dtypes = self.get_whole_column(self.VGP_Data_table_names, self.table_names_col.loc[self.VGP_Data_table_names, 'datatype_col'])

	# 	val_ids = self.get_whole_column(self.VGP_Data_table_names, self.table_names_col.loc[self.VGP_Data_table_names, 'id_col'])

	# 	# Concatenate lists
	# 	addresses = par_addr + val_addr

	# 	dtypes = par_dtypes + val_dtypes

	# 	ids = par_ids + val_ids

	# 	# Get id_cols and val_cols, query data are appended only if belong to the dtypes Parameter, VGP_Value_Double or VGP_Value_FunctionD
	# 	columns = ['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id']

	# 	res = pd.DataFrame(columns = columns, dtype = str)

	# 	for addr, dtype, id_ in zip(addresses, dtypes, ids):

	# 		# Check if the values belong to one of the three types, if the address is not among the input values and if the value is actually used in the program
	# 		#T.B.N. not all the addresses in VGP_Data are actually used in the program!!!
	# 		if dtype in [self.Parameter_table_names, self.VGP_Value_Double_table_names, self.VGP_Value_FunctionD_table_names] and addr not in common.Variables.data['val_addr'].tolist()\
	# 		and id_ in self.get_whole_column(dtype, self.table_names_col.loc[dtype, 'id_col']): # T.B.N. not all the addresses in VGP_Data table_names are actually used in the program

	# 			res = res.append({'val_addr' : addr, 'table_names' : dtype, 'id_col' : self.table_names_col.loc[dtype, 'id_col'], 'sect_perc_col' : self.table_names_col.loc[dtype, 'sect_perc_col'],\
	# 				  'val_col' : self.table_names_col.loc[dtype, 'val_col'],'id' : id_}, ignore_index = True)

	# 		else:

	# 			pass

	# 	return res # DataFrame(['val_addr', 'table_names', 'id_col', 'sect_perc_col', 'val_col', 'id'])


	# def scale_prog_values(self):

	# 	to_scale_qry_data = self.get_to_scale_qry_data()

	# 	up_prog = VgpProg(common.Variables.up_prog_filename)

	# 	low_prog = VgpProg(common.Variables.low_prog_filename)

	# 	with up_prog, low_prog:

	# 		up_to_scale_vals = up_prog.get_values_from_qry_data(to_scale_qry_data) # DataFrame(['sect_perc', 'val'])

	# 		low_to_scale_vals = low_prog.get_values_from_qry_data(to_scale_qry_data) # DataFrame(['sect_perc', 'val'])

	# 	# Data scaling
	# 	scaled_vals = up_to_scale_vals*(1 - ((common.Variables.up_diam - common.Variables.diam) / (common.Variables.up_diam - common.Variables.low_diam))) +\
	# 				  low_to_scale_vals*(1 - ((common.Variables.diam - common.Variables.low_diam) / (common.Variables.up_diam - common.Variables.low_diam)))

	# 	self.update_values_from_qry_data(to_scale_qry_data, scaled_vals)


	# def update_input_values(self):

	# 	input_vals_ind = np.logical_and(common.Variables.data.val_addr.notnull(), common.Variables.data.rel.isnull()) # input values that can be directly updated must have an address and no relations

	# 	addr_list = common.Variables.data.val_addr[input_vals_ind].tolist() # address list

	# 	vals = common.Variables.data.loc[input_vals_ind, 'sect_perc':'val'] # sect percs and vals DataFrame

	# 	self.update_values_from_addr(addr_list, vals)