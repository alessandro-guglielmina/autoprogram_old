from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import math

from autoprogram import settings
from autoprogram import wbmodule as wbm

# Common variables namespace
class Variables(object):

	copyright_header = settings.copyright_header
	master_progs_dir = Path(settings.master_progs_dir)
	res_prog_dir = Path.home().joinpath(settings.res_prog_dir)
	values_database_wb = wbm.WorkBook(Path(master_progs_dir / settings.values_database_wb_filename))
	config_vals_wb_filename = settings.config_vals_wb_filename
	funct_vals_wb_filename = settings.funct_vals_wb_filename
	vgp_suffix = settings.vgp_suffix
	drill_diam_addr = settings.drill_diam_addr

	# tool_name = None
	# fam_name = None
	# fam_prog_dir = None
	# fam_prog_list = None
	# file_suffix = None
	# tool_type = None
	# diam = None
	# flute_len = None
	# diam_addr = None
	# flute_len_addr = None
	# data = None
	# prog_filename = None
	# prog = None
	# low_prog_filename = None
	# up_prog_filename = None
	# up_diam = None
	# low_diam = None
	# point_ang_addr = None
	# first_spg_addr = None
	# meas_dist_addr = None

class Relations(object):

	def prepare_args(self, args, res_addr): # (self, ['args'], ['res_addr'])

		# The rel_args string is split
		try:

			args = args[0].split(',')

		except:

			args = [None]

		# res_addr must be a single address
		if len(res_addr) > 1:

			raise ValueError('Wrong number of addresses.')

		# args must include only rel_args and update mode
		if len(args) > 2:

			raise ValueError('Wrong number of relation arguments.')

		# The first element always includes the relation arguments
		rel_args = args[0]

		# If the split rel_args has 2 elements, the second is the self update mode ('prog' is the default)
		try:

			update_mod = args[1]

		except:

			update_mod = 'prog'

		if not(update_mod == 'data' or update_mod == 'prog'):

			raise ValueError('Wrong update mode input.')

		return rel_args, update_mod # 'rel_args', 'update_mod'

	# This function update the value in the program or in common.variables.data.val_name, the argument rel_arg_name is always passed (even if in 'prog' mode)
	def update_rel_val(self, addr, val_name, update_mod, val, sect_perc = None): # (self, val, ['val_name'], ['address'], 'update mode', [sect_perc], 'rel_arg_name')

			# If the string 'prog' is passed the value is updated directly in the program
			if update_mod == 'prog':

				update_val = pd.DataFrame([[sect_perc, val]], columns = ['sect_perc', 'val']) # build value dataframe
				variables.prog.prog_update_values_from_addr(addr, update_val) # update val in the program

			# If the string 'data' is passed the value is updated in common.variables.data.val 
			elif update_mod == 'data':

				try:

					variables.data.val[variables.data.val_name == val_name[0]] = val # update val in data

				except:

					raise ValueError(f'{val_name} not found among the database value names.')


	def get_rel_arg_val(self, rel_arg_name):

		try:

			return variables.data.val[variables.data.val_name == rel_arg_name].values[0]

		except:

			raise ValueError(f'{rel_arg_name} not found among the database value names.')


	# all function rel_argsiments: (self, ['rel_arg1', 'rel_arg2', ...], ['res_addr1', 'res_addr2', ...])
	def equal_to_f(self, val_name, args, res_addr):

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# rel_arg_name is the only passed relation argument
		rel_arg_name = rel_args

		# Get rel_argument value
		rel_arg_val = self.get_rel_arg_val(rel_arg_name)

		# Calculations
		res_val = rel_arg_val # calculation

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, res_val)
		# res = pd.DataFrame([[None, res_val]], columns = ['sect_perc', 'val']) # build value dataframe
		# variables.prog.prog_update_values_from_addr(res_addr, res) # update value


	def deg_to_rad_f(self, val_name, args, res_addr):

		rel_args, update_mod = self.prepare_args(args, res_addr)
		
		# deg_ang_name is the only passed relation argument
		deg_ang_name = rel_args

		# Get deg_ang_val
		deg_ang_val = self.get_rel_arg_val(deg_ang_name)

		# Calculations
		rad_ang_val = rel_args_val / 180 * math.pi # calculation

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, rad_ang_val)
		# res = pd.DataFrame([[None, rad_ang_val]], columns = ['sect_perc', 'val']) # build value dataframe
		# variables.prog.prog_update_values_from_addr(res_addr, res) # update val


	def lead_to_helix_f(self, val_name, args, res_addr): # return helix angle in radians

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# lead_name is the only passed relation argument
		lead_name = rel_args

		# Get lead_val
		lead_val = self.get_rel_arg_val(lead_name)

		# Calculations
		helix_val = math.pi / 2 - math.atan(lead_val / (variables.diam*math.pi))

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, helix_val)


	def add_f(self, val_name, args, res_addr):

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# Get rel_arg_name addend
		rel_args = rel_args.split('+') # get a list with the argument name and the factor to be multiplied by
		rel_arg_name = rel_args[0]
		addend = rel_args[1]

		# Get rel_argument value
		rel_arg_val = self.get_rel_arg_val(rel_arg_name)

		# Cast factor to float (if possible)
		try:

			addend = float(addend)

		except:

			raise ValueError('Wrong multiplication factor.')

		# Calculations
		res_val = rel_arg_val + addend # calculation

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, res_val)


	def multiply_f(self, val_name, args, res_addr):

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# Get rel_arg_name and multiplication factor
		rel_args = rel_args.split('*') # get a list with the argument name and the factor to be multiplied by
		rel_arg_name = rel_args[0]
		factor = rel_args[1]

		# Get rel_argument value
		rel_arg_val = rel_arg_val = self.get_rel_arg_val(rel_arg_name)

		# Cast factor to float (if possible)
		try:

			factor = float(factor)

		except:

			raise ValueError('Wrong multiplication factor.')

		# Calculations
		res_val = rel_arg_val * factor # calculation

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, res_val)
		#res = pd.DataFrame([[None, res_val]], columns = ['sect_perc', 'val']) # build value dataframe
		#variables.prog.prog_update_values_from_addr(res_addr, res) # update val



	def meas_dist_f(self, val_name, args, res_addr):

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# Calculations
		if variables.diam >= 2:

			meas_dist_perc_val = 0.1 / variables.diam

		else:

			meas_dist_perc_val = 0.05

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, meas_dist_perc_val)
		#res = pd.DataFrame([[None, meas_dist_perc_val]], columns = ['sect_perc', 'val'])
		#variables.prog.prog_update_values_from_addr(res_addr, res)
		


	def sP1_calc_f(self, val_name, args, res_addr): #(self, ['arg1', 'arg2', ...], ['addr1', 'addr2', ...])

		if variables.tool_type != 'drill':

			raise ValueError('Wrong tool type for this function.')

		rel_args, update_mod = self.prepare_args(args, res_addr)

		# Get sP1_end_name
		sP1_end_name = rel_args

		# Get sP1_end_val
		sP1_end_val = rel_arg_val = self.get_rel_arg_val(sP1_end_name)

		# Auxiliary rel_arguments
		point_ang = math.radians(variables.prog.prog_get_values_from_addr([variables.point_ang_addr]).loc[0, 'val']) # point angle value
		cone_len = variables.diam / (2*math.tan(point_ang / 2))

		# Calculations
		sP1_val = sP1_end_val - cone_len

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, sP1_val)
		#res = pd.DataFrame([[None, sP1_val]], columns = ['sect_perc', 'val'])
		#variables.prog.prog_update_values_from_addr(res_addr, res) # (['addr'], DataFrame('sect_perc', 'val'))


	def cut_params_select_f(self, val_name, rel_args, res_addr):

		# Feeds table and diameter column
		cut_params_table = 'cutting_parameters'
		diam_column = 'tool_diameter'

		rel_args, update_mod = self.prepare_args(rel_args, res_addr)

		# Get feed category
		cutting_param_name = rel_args

		# Get feeds table column names
		settings.curs.execute(f'SELECT * FROM {cut_params_table}')
		col_names = [descr[0] for descr in settings.curs.description]

		if cutting_param_name not in col_names:

			raise ValueError('No such a cutting parameter.')

		else:

			pass

		try:

			data = pd.DataFrame(settings.curs.execute(f'SELECT {diam_column}, {cutting_param_name} FROM {cut_params_table}').fetchall(), columns = ['tool_diam', 'cutting_param'])

		except:

			raise ValueError('Wrong cutting parameter category as input.')

		data = data.astype(float)
		cutting_param_fun = interp1d(data.tool_diam[data.cutting_param.notnull()], data.cutting_param[data.cutting_param.notnull()])

		try:

			cutting_param_val = cutting_param_fun(variables.diam).astype(float)

		except:

			raise ValueError(f'{cutting_param_name} column has no cutting parameters for diameter {variables.diam}.')

		if variables.file_suffix == '.vgp':

			if 'SPEED' in cutting_param_name.upper():

				cutting_param_val = cutting_param_val * 1000 # from m/s to mm/s

			elif 'FEED' in cutting_param_name.upper():

				cutting_param_val = cutting_param_val / 60 # from mm/min to mm/s

			else:

				raise ValueError('Call cutting parameter "speed" or "feed".')

		else:

			raise ValueError('No cutting parameters for this file type.')

		# Update value
		self.update_rel_val(res_addr, val_name, update_mod, cutting_param_val) # feed must be always directly updated
		#res = pd.DataFrame([[None, feed]], columns = ['sect_perc', 'val'])


	# def one_val_funct_f(self, val_name, rel_args, res_addr):

	# 	if len(rel_args) != 1 or len(res_addr) != 1:

	# 		raise ValueError('Wrong number of input arguments.')

	# 	else:

	# 		pass

	# 	# Get rel_argsument name
	# 	rel_arg_name = rel_args[0]

	# 	# Get rel_argsument value
	# 	val = variables.data.val[variables.data.val_name == rel_arg_name].values[0]

	# 	# Calculations
	# 	res_val = [val]*2
	# 	res_sect_perc = [0, 1]

	# 	# Update value
	# 	res = pd.DataFrame([[res_sect_perc, res_val]], columns = ['sect_perc', 'val']) # build value dataframe
	# 	variables.prog.prog_update_values_from_addr(res_addr, res) # update val



	equal_to = lambda self, val_name, rel_args, res_addr: self.equal_to_f(val_name, rel_args, res_addr)
	deg_to_rad = lambda self, val_name, rel_args, res_addr: self.deg_to_rad_f(val_name, rel_args, res_addr)
	lead_to_helix = lambda self, val_name, rel_args, res_addr: self.lead_to_helix_f(val_name, rel_args, res_addr)
	add = lambda self, val_name, rel_args, res_addr: self.add_f(val_name, rel_args, res_addr)
	multiply = lambda self, val_name, rel_args, res_addr: self.multiply_f(val_name, rel_args, res_addr)
	meas_dist = lambda self, val_name, rel_args, res_addr: self.meas_dist_f(val_name, rel_args, res_addr)
	sP1_calc = lambda self, val_name, rel_args, res_addr: self.sP1_calc_f(val_name, rel_args, res_addr)
	cut_params_select = lambda self, val_name, rel_args, res_addr: self.cut_params_select_f(val_name, rel_args, res_addr)
	one_val_funct = lambda self, val_name, rel_args, res_addr: self.one_val_funct_f(val_name, rel_args, res_addr)

	select = {
			  'equal_to' : equal_to,
			  'deg_to_rad' : deg_to_rad,
			  'lead_to_helix' : lead_to_helix,
			  'add' : add,
			  'multiply' : multiply,
			  'meas_dist' : meas_dist,
			  'sP1_calc': sP1_calc,
			  'cut_params_select': cut_params_select,
			  'one_val_funct' : one_val_funct
			  }


relations = Relations()