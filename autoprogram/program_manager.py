import sqlite3
import numpy as np
import pandas as pd

from autoprogram import common as common
from autoprogram import db_manager as dbm




# Function allowing to choose the correct object depending on the file extension
def prog_select(path):

	if common.variables.file_suffix == common.variables.vgp_file_suffix:

		res = vgp_prog(path)
		return res

	else:

		print('Unknown file type.')


# Returns if a value can be cast as float or not
def is_float(val):

	try:

		float(val)
		#val[0]

		return True

	except ValueError:

		return False

is_numeric = lambda x: np.any(np.asarray(list(map(is_float, x))))

class program(object):

	def __init__(self, path):

		self.db = dbm.db(path)
		self.settings = common.settings

	# These variables and functions must be created for the ANCA program too (then remove vgp_)

	diam_name = 'diameter name not initialized'
	flute_len_name = 'flute length name not initialized'

	def prog_get_values_from_names(self):

		print('Function prog_get_values_from_names not initialized.')

	# def vgp_get_to_scale_addr(self):

	# 	print('Function vgp_get_to_scale_addr not initialized.')

	def prog_scale_values(self):

		print('Function prog_scale_values not initialized.')

	def prog_update_values_from_names(self):

		print('Function prog_average_values not initialized.')

	def prog_delta_dL(self):

		print('Function delta_dL not initialized')

	def prog_cls(self):

		print('Function prog_cls not initialized.')



class vgp_prog(program): # CREATE SAME FUNCTIONS IN AN OBJECT THAT IHERIT "PROGRAM" AS PARENT OBJECT. "PROGRAM" IS INHERITED BY ANCA_PROG TOO

	def __init__(self, path):

		super().__init__(path)

	Curve_table = 'Curve' 
	Parameter_table = 'Parameter'
	VGP_Data_table = 'VGP_Data'
	VGP_Value_Double_table = 'VGP_Value_Double'
	VGP_Value_FunctionD_table = 'VGP_Value_FunctionD'

	table_col_dict = {
						'id_col' : {Parameter_table : 'PA_Id', VGP_Data_table : 'ID', VGP_Value_Double_table : 'D_Id', VGP_Value_FunctionD_table : 'D_Id', Curve_table : None},
						'sect_perc_col' : {Parameter_table : None, VGP_Data_table : None, VGP_Value_Double_table : None, VGP_Value_FunctionD_table : 'D_Parameter', Curve_table : None},
						'val_col' : {Parameter_table : 'PA_Value', VGP_Data_table : None, VGP_Value_Double_table : 'D_Value', VGP_Value_FunctionD_table : 'D_Value', Curve_table : None},
						'val_addr_col' : {Parameter_table : None, VGP_Data_table : 'PartialFullname', VGP_Value_Double_table : None, VGP_Value_FunctionD_table : None, Curve_table : None},
						'name_col' : {Parameter_table : 'PA_Name', VGP_Data_table : None, VGP_Value_Double_table : None, VGP_Value_FunctionD_table : None, Curve_table : None},
						'datatype_col' : {Parameter_table : None, VGP_Data_table : 'VGP_Value_Type', VGP_Value_Double_table : None, VGP_Value_FunctionD_table : None, Curve_table : None},
						'curve_id_col' : {Parameter_table : 'PA_CurveId', VGP_Data_table : None, VGP_Value_Double_table : None, VGP_Value_FunctionD_table : None, Curve_table  : 'CU_Id'},
						'curve_type_col' : {Parameter_table : None, VGP_Data_table : None, VGP_Value_Double_table : None, VGP_Value_FunctionD_table : None, Curve_table  : 'CU_Type'},
					 }

	table_col = pd.DataFrame(table_col_dict)


	# Get the Parameter id from the parameter name (and curve type, because more parameters have the same name, but only one parameter per curve type)
	def vgp_get_param_id_from_addr(self, addr): # (self, row.addr)

		addr = addr.split('@') # split the address in parameter type and parameter name
		curve_type = addr[0]
		param_name = addr[1]

		# Get the possible curve ids from Curve table
		poss_curve_ids = self.db.db_get_value_single_id(self.Curve_table, self.table_col.loc[self.Curve_table, 'curve_type_col'],\
						 self.table_col.loc[self.Curve_table, 'curve_id_col'], curve_type) # [poss_cu_id1, poss_CU_Id2, ...]

		# if poss_curve_ids is a scalar, it's made list-like in order to be passed in the function .isin()
		if isinstance(poss_curve_ids, str):

			poss_curve_ids = [poss_curve_ids]

		else:

			pass

		# Get all the curve ids corresponding to the parameter name
		same_name_curve_ids = self.db.db_get_value_single_id(self.Parameter_table, self.table_col.loc[self.Parameter_table, 'name_col'],\
							  self.table_col.loc[self.Parameter_table, 'curve_id_col'], param_name)

		# Get all the parameter ids corresponding to the parameter name
		same_name_param_ids = self.db.db_get_value_single_id(self.Parameter_table, self.table_col.loc[self.Parameter_table, 'name_col'],\
							   self.table_col.loc[self.Parameter_table, 'id_col'], param_name)

		#print(same_name_curve_ids)
		#print(poss_curve_ids)
		# Collect curve ids and parameter ids in a DataFrame
		param_data = pd.DataFrame({
								   'curve_id': pd.Series(same_name_curve_ids, dtype = 'str'),
								   'param_id': pd.Series(same_name_param_ids, dtype = 'str'),
									})

		res = param_data.loc[param_data.curve_id.isin(poss_curve_ids), 'param_id'].values[0] # the query could returns 2 values, but changing one, vgp automatically update the other one
																							 # otherwise we should treat it as a function value
		#print(res)																					
		return res # param_id

	
	# vgp_get_dtype_n_id() auxiliary function
	def vgp_get_dtype_n_id_from_single_addr(self, addr): #(self, 'val_address')

		if addr == None:

			raise ValueError('None address not valid.')

		else:

			pass

		# If the address is not in VGP_Data, it means that it's a Parameter
		try:

			dtype = self.db.db_get_value_single_id(self.VGP_Data_table, self.table_col.loc[self.VGP_Data_table, 'val_addr_col'], self.table_col.loc[self.VGP_Data_table, 'datatype_col'], addr)
			id_ = self.db.db_get_value_single_id(self.VGP_Data_table, self.table_col.loc[self.VGP_Data_table, 'val_addr_col'], self.table_col.loc[self.VGP_Data_table,'id_col'], addr)
			res = np.asarray([[dtype, id_]])

		# If db_get_value_single_id() returns a 
		except:

			id_ = self.vgp_get_param_id_from_addr(addr)

			res = np.asarray([[self.Parameter_table, id_]]) # strings


		return res #array([['table', 'id']])


	# Returm the data type and the id corresponding to a certain address array for data types VGP_Value_Double, VGP_Value_Int, VGP_Value_String, ... (not Parameter)
	def vgp_get_dtypes_n_ids(self, addr): #(self, array(['val_addr1', 'val_addr2', ...]))

		res = np.empty((0,2))

		for i in addr:

			dtype_n_id_i = self.vgp_get_dtype_n_id_from_single_addr(i)

			#print(dtype_n_id_i)

			res = np.append(res, dtype_n_id_i, axis = 0)

		return res # array([['table1', 'id1'], ['table2', 'id2'], ...])


	# Get id_col and val_col alongside table and id, obtained with the previous function (values that must not be averaged are skipped because of the previous function)
	def vgp_get_qry_data_from_addr(self, addresses): #(self, ['val_addr1', 'val_addr2', ...])) T.B.N. addresses not belonging to tables 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted

		dtypes_n_ids = self.vgp_get_dtypes_n_ids(addresses)
		columns = ['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id']
		res = pd.DataFrame(columns = columns, dtype = str)


		for dts_n_ids, addr in zip(dtypes_n_ids, addresses):

			dtype = dts_n_ids[0]
			id_ = dts_n_ids[1]

			if dtype in [self.Parameter_table, self.VGP_Value_Double_table]:

				res = res.append({'val_addr' : addr, 'table' : dtype, 'id_col' : self.table_col.loc[dtype, 'id_col'], 'sect_perc_col' : None, 'val_col' : self.table_col.loc[dtype, 'val_col'],\
					  'id' : id_}, ignore_index = True)

			elif dtype == self.VGP_Value_FunctionD_table:

				res = res.append({'val_addr' : addr, 'table' : dtype, 'id_col' : self.table_col.loc[dtype, 'id_col'], 'sect_perc_col' : self.table_col.loc[dtype, 'sect_perc_col'],\
					  'val_col' : self.table_col.loc[dtype, 'val_col'],'id' : id_}, ignore_index = True)

			else:

				raise ValueError(f'Data in {dtype} must not be processed.')

		return res # DataFrame(['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id'])
		# T.B.N. addresses not belonging to tables 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted

	

	# Return a list containng both scalar values and function values in string format (to obtain float values the output must be cast!!!)
	def vgp_get_values_from_qry_data(self, qry_data): #(self, DataFrame(['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id'])) T.B.N. addresses not belonging to tables 'Parameter', 'VGP_Value_Double' or 'VGP_Value_FunctionD' are automatically deleted

		columns = ['sect_perc', 'val']
		res = pd.DataFrame(columns = columns, dtype = str)

		for i, row in qry_data.iterrows(): # row is the pd.Series corresponding to a specific row
				
			# If the value is a scalar value
			if row.table in [self.Parameter_table, self.VGP_Value_Double_table]:

				val = self.db.db_get_value_single_id(row.table, row.id_col, row.val_col, row.id) # value can be either a string or None

				try:

					val = val.strip(' mm°') # delete non numeric characters
					val = float(val)
					#res = res.append({'sect_perc' : None, 'val' : val}, ignore_index = True)

				except:

					pass

				res = res.append({'sect_perc' : None, 'val' : val}, ignore_index = True)


			# If the value is a function value:
			elif row.table == self.VGP_Value_FunctionD_table:

				sect_perc = self.db.db_get_value_single_id(row.table, row.id_col, row.sect_perc_col, row.id) # value can be either array of strings or None values
				val = self.db.db_get_value_single_id(row.table, row.id_col, row.val_col, row.id)

				try:

					np.char.rstrip(sect_perc, ' mm°')
					np.char.rstrip(val, ' mm°')
					sect_perc = sect_perc.astype(float)
					val = val.astype(float)
			 		#res = res = res.append({'sect_perc' : sect_perc, 'val' : val}, ignore_index = True)

				except:

			 		pass

				res = res.append({'sect_perc' : sect_perc, 'val' : val}, ignore_index = True)


		return res  # DataFrame(['sect_perc', 'val'])


	def prog_get_values_from_addr(self, param_addr): # (self, list(['par_name1', 'par_name2', ...]))

		# Get query data from addresses
		qry_data = self.vgp_get_qry_data_from_addr(param_addr)

		return self.vgp_get_values_from_qry_data(qry_data) # DataFrame(['sect_perc', 'val'])


	def prog_update_values_from_addr(self, param_addr, vals): # (self, list(['par_name1', 'par_name2', ...]), DataFrame(['sect_perc', 'val']))

		# Get query data from addresses
		qry_data = self.vgp_get_qry_data_from_addr(param_addr)

		return self.vgp_update_values_from_qry_data(qry_data, vals) # DataFrame(['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id'])


	# Return a list containng both scalar values and function values in string format (to obtain float values the output must be cast!!!)
	def vgp_update_values_from_qry_data(self, qry_data, vals): #(self, DataFrame(['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id'])), DataFrame(['sect_perc', 'val'])

		for qry_data_iterrows, vals_iterrows in zip(qry_data.iterrows(), vals.iterrows()):

			qry_i, qry_row = qry_data_iterrows
			val_i, val_row = vals_iterrows

			#print(qry_row.val_addr, qry_row.table, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.sect_perc, val_row.val)

			# If the value is a scalar:
			if qry_row.table in [self.Parameter_table, self.VGP_Value_Double_table]:

				self.db.db_update_values_single_id(qry_row.table, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val)

			# If the value is a function:
			elif qry_row.table == self.VGP_Value_FunctionD_table:

				# If a function value has a single input
				if not hasattr(val_row.val, "__len__") and val_row.sect_perc == None:

					val_row.val = [val_row.val]*2
					val_row.sect_perc = [0, 1]

				self.db.db_update_values_single_id(qry_row.table, qry_row.id_col, qry_row.sect_perc_col, qry_row.id, val_row.sect_perc)
				self.db.db_update_values_single_id(qry_row.table, qry_row.id_col, qry_row.val_col, qry_row.id, val_row.val)

			else:

				raise ValueError('Wrong datatype provided')


	# Get all the query data that have to be scaled (without passing through adrresses)
	def vgp_get_to_scale_qry_data(self):

		# Get Parameter addresses, composing parameter name and curve type
		par_addr_part2 = self.db.db_get_whole_column(self.Parameter_table, self.table_col.loc[self.Parameter_table, 'name_col'])
		par_curve_ids = self.db.db_get_whole_column(self.Parameter_table, self.table_col.loc[self.Parameter_table, 'curve_id_col'])
		curve_ids = self.db.db_get_whole_column(self.Curve_table, self.table_col.loc[self.Curve_table, 'curve_id_col'])
		#param_addr_part2 = ['@'*len(param_addr_part1)]
		par_addr_part1 = self.db.db_get_values([self.Curve_table], [self.table_col.loc[self.Curve_table, 'curve_id_col']], [self.table_col.loc[self.Curve_table, 'curve_type_col']], par_curve_ids)
		par_addr = pd.Series(par_addr_part1).str.cat(par_addr_part2, sep = '@').to_list()

		# Get Parameter dtypes and ids
		par_dtypes = [self.Parameter_table for i in par_addr]
		par_ids = self.db.db_get_whole_column(self.Parameter_table, self.table_col.loc[self.Parameter_table, 'id_col'])

		# Get VGP_Values addresses, dtypes and ids
		val_addr = self.db.db_get_whole_column(self.VGP_Data_table, self.table_col.loc[self.VGP_Data_table, 'val_addr_col']) # array(['val1', 'val2', ...])
		val_dtypes = self.db.db_get_whole_column(self.VGP_Data_table, self.table_col.loc[self.VGP_Data_table, 'datatype_col'])
		val_ids = self.db.db_get_whole_column(self.VGP_Data_table, self.table_col.loc[self.VGP_Data_table, 'id_col'])

		# Concatenate lists
		addresses = par_addr + val_addr
		dtypes = par_dtypes + val_dtypes
		ids = par_ids + val_ids

		# Get id_cols and val_cols, query data are appended only if belong to the dtypes Parameter, VGP_Value_Double or VGP_Value_FunctionD
		columns = ['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id']
		res = pd.DataFrame(columns = columns, dtype = str)

		for addr, dtype, id_ in zip(addresses, dtypes, ids):
			
			# Check if the values belong to one of the three types, if the address is not among the input values and if the value is actually used in the program
			#T.B.N. not all the addresses in VGP_Data are actually used in the program!!!
			if dtype in [self.Parameter_table, self.VGP_Value_Double_table, self.VGP_Value_FunctionD_table] and addr not in common.variables.data['val_addr'].tolist()\
			and id_ in self.db.db_get_whole_column(dtype, self.table_col.loc[dtype, 'id_col']): # T.B.N. not all the addresses in VGP_Data table are actually used in the program

				#print({'val_addr' : addr, 'table' : dtype, 'id_col' : self.table_col.loc[dtype, 'id_col'], 'sect_perc_col' : self.table_col.loc[dtype, 'sect_perc_col'],\
					  #'val_col' : self.table_col.loc[dtype, 'val_col'],'id' : id_})

				res = res.append({'val_addr' : addr, 'table' : dtype, 'id_col' : self.table_col.loc[dtype, 'id_col'], 'sect_perc_col' : self.table_col.loc[dtype, 'sect_perc_col'],\
					  'val_col' : self.table_col.loc[dtype, 'val_col'],'id' : id_}, ignore_index = True)

			else:

				pass

		return res # DataFrame(['val_addr', 'table', 'id_col', 'sect_perc_col', 'val_col', 'id'])


	def prog_scale_values(self):

		to_scale_qry_data = self.vgp_get_to_scale_qry_data()

		up_prog = prog_select(common.variables.up_prog_filename)
		low_prog = prog_select(common.variables.low_prog_filename)

		up_to_scale_vals = up_prog.vgp_get_values_from_qry_data(to_scale_qry_data) # DataFrame(['sect_perc', 'val'])
		low_to_scale_vals = low_prog.vgp_get_values_from_qry_data(to_scale_qry_data) # DataFrame(['sect_perc', 'val'])

		# Data scaling
		scaled_vals = up_to_scale_vals*(1 - ((common.variables.up_diam - common.variables.diam) / (common.variables.up_diam - common.variables.low_diam))) +\
					  low_to_scale_vals*(1 - ((common.variables.diam - common.variables.low_diam) / (common.variables.up_diam - common.variables.low_diam)))

		self.vgp_update_values_from_qry_data(to_scale_qry_data, scaled_vals)


	def prog_update_input_values(self):

		input_vals_ind = np.logical_and(common.variables.data.val_addr.notnull(), common.variables.data.rel.isnull()) # input values that can be directly updated must have an address and no relations
		addr_list = common.variables.data.val_addr[input_vals_ind].tolist() # address list
		vals = common.variables.data.loc[input_vals_ind, 'sect_perc':'val'] # sect percs and vals DataFrame

		# print(input_vals_ind)
		# print(common.variables.data.val)
		# print(common.variables.data.val_addr)
		# print(common.variables.data.rel)
		# input('STOP')

		self.prog_update_values_from_addr(addr_list, vals)

		
	#def prog_delta_dL(self):

		# point_ang_n_fst_spg = self.vgp_get_values_from_names([variables.point_ang_name, ariables.first_spg_name])

		# point_ang = point_ang_n_fst_spg.loc[0, 'val'] # it's a scalar
		# fst_spg = point_ang_n_fst_spg.loc[1, 'val'][0] # it's a function, take only first value



	def prog_cls(self):

		self.db.db_cls()

