import sqlite3 as sql
import numpy as np
import pandas as pd
import math
from pathlib import Path
import copy

VGPIO_MODULE_PATH = Path(__file__) # vgpio.py (this module) path
VGPIO_PACKAGE_PATH = VGPIO_MODULE_PATH.parent # directory containing vgpio.py
NAMES_MAP_FILENAME = "names mapper.xlsx"
NAMES_MAP_PATH = VGPIO_PACKAGE_PATH.joinpath(NAMES_MAP_FILENAME) # the file "address mapper.xlsx" is always read from the same directory of the vgpio.py module (this module)
NAMES_MAP_SHEET_NAME = "names mapper"
WHEEL_CURVE_NAME = "Rollomatic.LibCurve.Data.Curves.WheelProfileCurve"

try:
	NAMES_MAP_DF = pd.read_excel(NAMES_MAP_PATH, sheet_name = NAMES_MAP_SHEET_NAME, dtype=str)
	NAMES_MAP_DF.name = "names mapper"
except FileNotFoundError:
 	raise ValueError(f"No such an address mapper file: {NAMES_MAP_FILENAME}")

TABLE_ATTRIBUTES = ("id_col", "val_col", "sect_perc_col")
CURVE = pd.Series(("CU_Id", "CU_Type", np.nan), name="Curve", index=TABLE_ATTRIBUTES)
PARAMETER = pd.Series(("PA_Id", "PA_Value", np.nan), name="Parameter", index=TABLE_ATTRIBUTES)
VGP_DATA = pd.Series(("ID", "PartialFullname", np.nan), name="VGP_Data", index=TABLE_ATTRIBUTES)
VGP_VALUE_DOUBLE = pd.Series(("D_Id", "D_Value", np.nan), name="VGP_Value_Double", index=TABLE_ATTRIBUTES)
VGP_VALUE_FUNCTIOND = pd.Series(("D_Id", "D_Value", "D_Parameter"), name="VGP_Value_FunctionD", index=TABLE_ATTRIBUTES)
VGP_VALUE_INT = pd.Series(("D_Id", "D_Value", np.nan), name="VGP_Value_Int", index=TABLE_ATTRIBUTES)
R_TABLE_SERIES = (VGP_DATA, CURVE)
RW_TABLE_SERIES = (PARAMETER, VGP_VALUE_DOUBLE, VGP_VALUE_FUNCTIOND, VGP_VALUE_INT)
R_TABLES = pd.DataFrame(columns=TABLE_ATTRIBUTES)
RW_TABLES = pd.DataFrame(columns=TABLE_ATTRIBUTES)

for r_table_series in R_TABLE_SERIES:
	R_TABLES.loc[r_table_series.name] = r_table_series

for rw_table_series in RW_TABLE_SERIES:
	RW_TABLES.loc[rw_table_series.name] = rw_table_series
ALL_TABLES = R_TABLES.append(RW_TABLES) # Vgp_Data table must be read before the other ones
SEPARATOR = "."


class VgpData(pd.DataFrame):
	"""
	Description
	"""
	def __init__(self, name, val, sect_perc=None):
		if isinstance(sect_perc, pd.DataFrame) and isinstance(val, pd.DataFrame):
			val_ser = val.iloc[:, 0]
			sect_perc_ser = sect_perc.iloc[:, 0]
		elif val is not None and sect_perc is not None:
			val_ser = pd.Series(val)
			sect_perc_ser = pd.Series(sect_perc)
		elif val is not None and sect_perc is None:
			val_ser = pd.Series(val)
			sect_perc_ser = pd.Series(np.nan)
		else:
			raise ValueError("Wrong VgpData arguments")
		idx = pd.Index([name]).repeat(val_ser.size)
		val_ser.index = idx
		sect_perc_ser.index = idx
		super().__init__({"val": val_ser, "sect_perc": sect_perc_ser})


class VgpProgram(object):
	"""
	This class is an I/O interface to the VGPro program (version 1.29)
	"""
	def __init__(self, path, diam_name):
		# path: .vgp file path
		self.path = path
		self.diam_name = diam_name

	def __enter__(self):
		# read DataFrame values from the .vgp file
		self.con = sql.connect(self.path)
		self.df_setup()
		self.curr_diam = self[self.diam_name]
		return self

	def __exit__(self, exc_class, exc, traceback):
		# write DataFrame values into the .vgp file
		self.df_commit()
		self.con.commit()
		self.con.close()
		pass

	@staticmethod				
	def elem_wise_query(search_df, id_col, _id, res_col):
		"""
		This method returns a single result value from a query; the arguments are: self, the df where to search, the id (single value), the DataFrame (df), the id column (id_col)
		and the result value column (res_col), it returns a single value as well. This function combined with pd.apply() method performs element-wise queries.
		_id is the first positional argument because corresponds to the series elements automatically passed in by the pd.apply() method
		"""
		filt = (search_df[id_col] == _id)
		res = search_df.loc[filt, res_col]
		if res.notna().any():
			return res.item()
		raise ValueError(f"No {_id} in the {id_col} column in the {search_df.name} DataFrame")

	def set_Parameter_idxs(self, Parameter_df): 
		"""
		Description
		"""
		def Parameter_addrs_builder(Parameter_df_row):
			"""
			Description
			"""
			curve_df = self.df["Curve"]
			curve_type = self.elem_wise_query(curve_df, curve_df.id_col, Parameter_df_row.PA_CurveId, curve_df.val_col)
			return curve_type + SEPARATOR + Parameter_df_row.PA_Name

		Parameter_addrs = Parameter_df.apply(Parameter_addrs_builder, axis=1)
		Parameter_df.set_index(Parameter_addrs, inplace=True)

	def set_Value_idxs(self, Value_df):
		"""
		Description
		"""
		vgp_data_df = self.df["VGP_Data"]
		get_Value_addrs = lambda Value_df_row: self.elem_wise_query(vgp_data_df, vgp_data_df.id_col, Value_df_row.D_Id, vgp_data_df.val_col)
		Value_addrs = Value_df.apply(get_Value_addrs, axis=1)
		Value_df.set_index(Value_addrs, inplace=True)
		# get_Value_names = lambda Value_addr: self.elem_wise_query(NAMES_MAP_DF, "val_addr", Value_addr, "val_id")
		# Value_names = Value_addrs.apply(get_Value_names)

	def df_set_idxs(self, df_arg):
		"""
		Description
		"""
		if df_arg.name == PARAMETER.name:
			self.set_Parameter_idxs(df_arg)
		else:
			self.set_Value_idxs(df_arg)

	def df_setup(self):
		"""
		This method read the specified database tables and write them into corresponding pd.DataFrame object,
		all of those are wrapped into the dictionary self.df
		"""
		self.df = {}
		for table_name, table in ALL_TABLES.iterrows():
			df_temp = pd.read_sql(f"SELECT * FROM {table_name}", self.con)
			if table_name == PARAMETER.name: # for Parameter table, val_col must be cast to float
				df_temp[table.val_col] = df_temp[table.val_col].str.rstrip(" °mm").astype("float64")
			df_temp.name = table_name
			df_temp.id_col = table.id_col
			df_temp.sect_perc_col = table.sect_perc_col
			df_temp.val_col = table.val_col
			if table_name in RW_TABLES.index: # in r/w tables, addresses are set to be indexes by this inplace method (read only tables are read before)
				self.df_set_idxs(df_temp) # addresses are set to be indexes by this inplace method
			self.df[table_name] = df_temp
		del df_temp
				
	def df_commit(self):
		"""
		Description
		"""
		for table_name, table in RW_TABLES.iterrows():
			# Reset Parameter values to be string in order to not alter the original .vgp file data types
			df_temp = self.df[table_name]
			if table_name == PARAMETER.name:
					df_temp[table.val_col] = df_temp[table.val_col].astype("str") # Parameter values are reset to string type
			df_temp.to_sql(table.name, self.con, if_exists='replace', index=False)
		del df_temp, self.df

	def get_addr(self, name):
		"""
		Description
		"""
		return self.elem_wise_query(NAMES_MAP_DF, "val_name", name, "val_addr")

	def get_table(self, addr):
		"""
		Description
		"""
		try:
			return self.elem_wise_query(self.df[VGP_DATA.name], VGP_DATA.val_col, addr, "VGP_Value_Type")
		except ValueError:
			return PARAMETER.name

	def get_arguments_ser(self, name):
		"""
		Description
		"""
		addr = self.get_addr(name)
		table = self.get_table(addr)
		return pd.Series([table, addr], index=["table", "addr"])

	def __getitem__(self, names):
		"""
		Description
		"""
		def get_data(name):
			args_ser = self.get_arguments_ser(name)
			table = args_ser["table"]
			addr = args_ser["addr"]
			df_temp = self.df[table]
			try:
				val = df_temp.loc[[addr], [df_temp.val_col]]
			except KeyError:
				raise ValueError(f"No such a value name in the program: {name}")
			if (df_temp.sect_perc_col in df_temp.columns):
				sect_perc = df_temp.loc[[addr], [df_temp.sect_perc_col]]
			else:
				# Build a sect_perc DataFrame for those datatypes not having a sect_perc column
				# Parameter return duplicate values for a single index, thus np.nan must be uplicate
				sect_perc_list = [np.nan for i in val.iterrows()]
				addr_list = [addr for i in val.iterrows()]
				sect_perc = pd.DataFrame(sect_perc_list, index=addr_list)

			return VgpData(name, val, sect_perc)

		names = pd.Series(names)
		vgp_data_list = []
		for name in names:
			vgp_data_list.append(get_data(name))
		return pd.concat(vgp_data_list)

	def __setitem__(self, names, raw_data):
		"""
		Description
		"""
		def set_data(name):
			args_ser = self.get_arguments_ser(name) # get a DataFrame contining table and address correspondent to the name
			table = args_ser["table"]
			addr = args_ser["addr"]
			df_temp = self.df[table]
			df_temp.loc[[addr], [df_temp.val_col]] = vgp_data_df.loc[[name], ["val"]].values # val
			# if (df_temp.sect_perc_col in df_temp.columns):
			# 	df_temp.loc[[addr], [df_temp.sect_perc_col]] = vgp_data_df.loc[name, "sect_perc"].values # sect_perc

		# Argument homogeneization
		names = pd.Series(names)
		data_df = pd.DataFrame.from_records(raw_data)
		vgp_data_list = []
		for name, [data_idx, data] in zip(names, data_df.iterrows()):
			vgp_data = VgpData(name, data.iloc[0], data.iloc[1])
			vgp_data_list.append(vgp_data)
		vgp_data_df = pd.concat(vgp_data_list)
		names.apply(set_data)

	def scale_tool(self, diam, scale_val_names):
		"""
		Description
		"""
		print(self[scale_val_names])
		# self[scale_val_names] = (self[scale_val_names] / self.curr_diam * diam).round(4)

	# @classmethod
	# def scale_tool(cls, self, diam, low_path, up_path):
	# 	"""
	# 	Description
	# 	"""
	# 	def scale(diam, low_diam, low_ser, up_diam, up_ser):
	# 		"""
	# 		Description
	# 		"""
	# 		def round_to_significant_figures(num, sf):
	# 			"""
	# 			Description
	# 			"""
	# 			try:
	# 				return round(num, sf - 1 - int(math.floor(math.log10(abs(num)))))
	# 			except ValueError:
	# 				return num

	# 		if diam > up_diam or diam < low_diam:
	# 			raise ValueError("No value scaling is possible with the passed programs")
	# 		delta_diam = up_diam - low_diam
	# 		low_delta = diam - low_diam
	# 		up_delta = up_diam - diam
	# 		low_coeff = 1 - low_delta / delta_diam
	# 		up_coeff = 1 - up_delta / delta_diam
	# 		res = low_ser * low_coeff + up_ser * up_coeff
	# 		return res.apply(lambda num: round_to_significant_figures(num, 5)) # round values to 5 significant figures

	# 	low_prog = cls(low_path, self.diam_name)
	# 	up_prog = cls(up_path, self.diam_name)
	# 	with low_prog, up_prog:
	# 		low_diam = low_prog[low_prog.diam_name].val.iloc[0]
	# 		up_diam = up_prog[up_prog.diam_name].val.iloc[0]
	# 		for table in (PARAMETER, VGP_VALUE_DOUBLE, VGP_VALUE_FUNCTIOND): # only these tables are scaled
	# 			df_temp = self.df[table.name]
	# 			# Parameter values relative to wheel geometry are not scaled
	# 			if table.name == PARAMETER.name:
	# 				curve_df = self.df[CURVE.name]
	# 				is_wheel_func = lambda PA_CurveId: True\
	# 								if self.elem_wise_query(curve_df, curve_df.id_col, PA_CurveId, curve_df.val_col) != WHEEL_CURVE_NAME\
	# 								else False
	# 				is_wheel_filt = df_temp.PA_CurveId.apply(is_wheel_func)
	# 				df_temp.loc[is_wheel_filt, table.val_col] = scale(diam, low_diam,\
	# 				low_prog.df[table.name].loc[is_wheel_filt, table.val_col], up_diam, up_prog.df[table.name].loc[is_wheel_filt, table.val_col])
	# 			else:
	# 				df_temp[table.val_col] = scale(diam, low_diam,\
	# 				low_prog.df[table.name][table.val_col], up_diam, up_prog.df[table.name][table.val_col])
	# 			# VGP_Value_FunctionD values are scaled also with respect to the sect_per column
	# 			if table.name == VGP_VALUE_FUNCTIOND.name:
	# 				df_temp[table.sect_perc_col] = scale(diam, low_diam,\
	# 				low_prog.df[table.name][table.sect_perc_col], up_diam, up_prog.df[table.name][table.sect_perc_col])