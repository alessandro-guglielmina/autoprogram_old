from pathlib import Path
import sqlite3 as sql
import numpy as np
import pandas as pd


class DataBase(object):

	def __init__(self, path):

		self.path = path

	# Context manager
	def __enter__(self):

		self.conn = sql.connect(self.path)

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
	def update_values_single_id(self, table, id_col, val_col, id_, val): #(self, 'table', 'id_col', 'val_col', 'id', [val1, val2, ...])
	
		rowids = self.get_rowids(table, id_col, id_)

		if len(val) != len(rowids):

			raise ValueError('Wrong number of input values.')

		for i, j in zip(val, rowids): # i is a single, float value

			qry = f'UPDATE {table} SET {val_col} = ? WHERE rowid = ?'

			qry_val = (i, j)

			self.curs.execute(qry, qry_val)


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


	def update_values_multi_ids(self, tables, id_col, val_col, ids, vals): #(self, array([[table1], [table2], ...]), array([[id_col1], [id_col2], ...]), array([[val_col1], [val_col2], ...]), array([[id1], [id2], ...], array([[val1], [val2], ...])

		for i, j, k, l, m in zip(tables, val_col, id_col, ids, vals):

			qry = f"UPDATE {i[0]} SET {j[0]} = ? WHERE {k[0]} = ?"

			qry_val = np.hstack((l, m))

			self.curs.execute(qry, qry_val)

			self.conn.commit()