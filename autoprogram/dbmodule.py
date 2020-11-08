from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd


class DataBase(object):

	def __init__(self, path):
		self.path = path

	# Context manager
	def __enter__(self):
		self.conn = sqlite3.connect(self.path)
		self.curs = self.conn.cursor()
		return self

	def __exit__(self, exc_class, exc, traceback):
		self.conn.commit()
		self.conn.close()

	# Get the row ids list corresponding to the input id
	def get_rowids(self, table, id_col, id_): # (self, 'table',  'id_col', 'id')
		qry = f"SELECT rowid FROM {table} WHERE {id_col} = ?"
		qry_arg = (id_,)
		self.curs.execute(qry, qry_arg)
		"""
		fetchall returns [(r1c1, r1c2, ...), (r2c1, r2c2, ...), ...], where the tuples
		are the rows of the returned set of values in the database
		"""
		qry_vals = self.curs.fetchall()
		if not qry_vals:
			raise ValueError(f"The query hasn't returned any value in the database {self.path}, in the table {table}, with the id {id_}.")
		else:
			pass
		res = [i[0] for i in qry_vals]
		return res # [rowid1, rowid2, ...]


	# # Get the row ids corresponding to 
	# def db_get_row_ids_double_id_cols(self, table, id_col1, id_col2, id1, id2): #(self, table', 'id_col1', 'id_col2', 'id1', 'id2')

	# 	qry = f"SELECT rowid FROM {table} WHERE {id_col1} = ? AND {id_col2} = ?"
	# 	qry_val = [id1, id2]
	# 	res = [i[0] for i in self.curs.execute(qry, qry_val).fetchall()]

	# 	return res # [rowid1, rowid2, ...]


	# Get values array from single id    	
	def get_values_single_id(self, table, id_col, val_col, id_): #(self, 'table', 'id_col', 'val_col', 'id')
		rowids = self.get_rowids(table, id_col, id_) # [rowid1, rowid2, ...]
		res = np.empty((1,0), dtype=str) # it can be str or None
		for rowid in rowids:
			qry = f'SELECT {val_col} FROM {table} WHERE rowid = ?'
			qry_arg = (rowid,)
			self.curs.execute(qry, qry_arg)
			val = self.curs.fetchall()[0] # (val,)
			res = np.append(res, val)
		return res # array([val1, val2, ...])

	# Update values array from single id
	def update_values(self, table, id_col, val_col, id_, val): #(self, 'table', 'id_col', 'val_col', 'id', [val1, val2, ...])
		rowids = self.get_rowids(table, id_col, id_)
		if hasattr(val, "__len__") and len(val) != len(rowids):
			raise ValueError('Wrong number of input values.')
		for i, j in zip(val, rowids):
			qry = f'UPDATE {table} SET {val_col} = ? WHERE rowid = ?'
			qry_val = (i, j)
			self.curs.execute(qry, qry_val)
	
		

	# def update_function_val(self, table, id_col, val_col, sect_perc_col, id_, val, sect_perc):
# 	try:
# 		row_ids = self.db_get_row_ids(table, id_col, id_)
# 		qry = "UPDATE {table} SET {sect_perc_col} = ?, {val_col} = ? WHERE rowid = ?".format(table = table,
# 			  sect_perc_col = sect_perc_col, val_col = val_col, id_col = id_col)
# 		qry_val = [val, id_]
# 		self.curs.executemany(qry, qry_val)
# 		self.commit()

	# Get values array from multiple ids
	def get_values_multi_ids(self, tables, id_cols, val_cols, ids): # (self, ['table1', 'table2', ...], ['id_col1', 'id_col2', ...], ['val_col1', 'val_col2', ...], ['id1', 'id2', ...]
		# Prepare data to pass them into the function as arguments (arguments must have all the same dimensions)
		# If arguments have different sizes, all the shorter ones are replicated to match the longest one
		args = [tables, id_cols, val_cols, ids]
		# If all the arguments have the same size no one has to be fixed
		all_same_length = True
		for i in range(0, len(args) - 1):

			all_same_length = all_same_length and (len(args[i]) == len(args[i + 1]))

		# Fix arguments length
		if not all_same_length:

			max_len_arg = max(args, key = len)
			max_arg_len = len(max_len_arg)

			for i in range(0, len(args)):

				if len(args[i]) != max_arg_len:

					args[i] = [args[i][0] for j in range(0, max_arg_len)]

		else:

			pass

		tables, id_cols, val_cols, ids = args # unpack fixed arguments

		# Function main part 
		res = np.empty((1,0), dtype=str) # initialize res

		for i, j, k, l in zip(tables, id_cols, val_cols, ids):

			res_i = self.get_values_single_id(i, j, k, l)

			res = np.append(res, res_i)

		return res # list([val1, [val11, val12, ...], ...])


	def get_whole_column(self, table, val_col): #(db(), 'table', 'val_col')
		qry = f"SELECT {val_col} FROM {table}"
		vals = np.asarray(self.curs.execute(qry).fetchall(), dtype = str) # from [(val1,), (val2,), ...] to array(['val1', 'val2', ...])
		res = vals[:, 0].tolist()
		return res # list(['val1', 'val2', ...])


	# def db_get_row_count(self, table, id_col, ids): #(db(), str, str, [int])

	# 	row_ids = self.db_get_row_ids(table, id_col, ids)
	# 	res = len(row_ids)

	# 	return res # int


	def update_values_multi_ids(self, tables, id_col, val_col, ids, vals): #(self, array([[table1], [table2], ...]), array([[id_col1], [id_col2], ...]), array([[val_col1], [val_col2], ...]), array([[id1], [id2], ...], array([[val1], [val2], ...])

		for i, j, k, l, m in zip(tables, val_col, id_col, ids, vals):

			qry = f"UPDATE {i[0]} SET {j[0]} = ? WHERE {k[0]} = ?"
			qry_val = np.hstack((l, m))
			self.curs.execute(qry, qry_val)
			self.conn.commit()


# class SettingsDb(DataBase):

# 	def __init__(self, path):

# 		self.path = path

# 		self.family_values_table = 'family_values'
# 		self.general_values_table = 'general_values'
# 		self.table_col = {
# 						self.family_values_table : {'fam_name_col' : 'fam_name', 'val_name_col' : 'val_name', 'rel_name_col' : 'rel_name', 'rel_args_col' : 'rel_args'},
# 						self.general_values_table : {'val_name_col' : 'val_name', 'val_descr_col' : 'val_descr', 'val_addr_col' : 'val_addr'},
# 					}

# 		super().__init__(self.path)


# 	def db_get_all_fam_names(self): #(self)

# 		raw_names = self.db_get_whole_column(self.family_values_table, self.table_col[self.family_values_table]['fam_name_col']) # list(['fam1', 'fam1', 'fam2', ...]) with duplicates
# 		res = list(dict.fromkeys(raw_names)) # delete duplicates and keep order

# 		return res # list(['fam1', 'fam2', ...])



# 	def db_get_addr_from_names(self, val_names): #(self, list(['val_name1', 'val_name2', ...]))

# 		res = self.db_get_values([self.general_values_table], [self.table_col[self.general_values_table]['val_name_col']],\
# 			  [self.table_col[self.general_values_table]['val_addr_col']], val_names)

# 		return res # list([addr1, addr2, ...])




# 	def db_get_fam_data(self, fam_name): #(settings_db(), 'fam_name')

# 		# Value names are considered as a function value
# 		val_names = self.db_get_value_single_id(self.family_values_table, self.table_col[self.family_values_table]['fam_name_col'],\
# 				self.table_col[self.family_values_table]['val_name_col'], fam_name) # get names needed to search addresses and description in "general_values" table

# 		# Relation names are considered as a function value
# 		rel_names = self.db_get_value_single_id(self.family_values_table, self.table_col[self.family_values_table]['fam_name_col'],\
# 			self.table_col[self.family_values_table]['rel_name_col'], fam_name) # get family_s relations

# 		# Relation argument names are considered as a function value
# 		rel_args = self.db_get_value_single_id(self.family_values_table, self.table_col[self.family_values_table]['fam_name_col'],\
# 			self.table_col[self.family_values_table]['rel_args_col'], fam_name) # relation arguments names contains strings and None values
# 		#rel_argss_temp = rel_argss[rel_argss != None] # get rid of None values

# 		descr = self.db_get_values([self.general_values_table], [self.table_col[self.general_values_table]['val_name_col']],\
# 			[self.table_col[self.general_values_table]['val_descr_col']], val_names) # get descriptions from "general_values table"

# 		sect_percs = [None for i in val_names]

# 		vals = [None for i in val_names]

# 		val_addr = self.db_get_addr_from_names(val_names) # get addresses from "general_values" table

# 		#rel_arg_addr_temp = self.db_get_addr_from_names(rel_argss_temp)
# 		#rel_arg_addr = np.asarray(rel_argss)
# 		#rel_arg_addr[rel_arg_addr != None] = rel_arg_addr_temp

# 		#res = pd.DataFrame(list(zip(names_df, rel_names_df, descr_df, addr_df, vals_df)), columns =['names', 'rel_names', 'descr', 'addr', 'vals'])
		
# 		res = pd.DataFrame({
#                      		'descr': pd.Series(descr, dtype = 'str'),
#                      		'sect_perc': pd.Series(sect_percs, dtype = 'object'),
#                      		'val': pd.Series(vals, dtype = 'object'),
#                      		'val_addr': pd.Series(val_addr, dtype = 'str'),
#                      		'val_name': pd.Series(val_names, dtype = 'str'),
#                      		'rel': pd.Series(rel_names, dtype = 'str'),
#                      		'rel_args': pd.Series(rel_args, dtype = 'str')
#                      		})
		

# 		return res #DataFrame([[n1, r1, d1, a1, v1], [n2, r2, d2, a2, v2], ...])