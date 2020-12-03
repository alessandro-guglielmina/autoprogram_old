from pathlib import Path
import os
import numpy as np
import pandas as pd

from autoprogram import settingsmodule as sm
from autoprogram import wbmodule as wbm


# Common variables namespace
class Variables(object):

	copyright_header = 'AutoProgram.\nCopyright \xc2\xa9 2020 Guglielmina Alessandro. All rights reserved.\n'

	values_database_wb_filename = 'values database.xlsx'

	database_sh_name ='database'

	config_file_wb_filename = 'configuration file.xlsx'

	diam_name_sh_name = 'diameter name'

	config_vals_sh_name = 'configuration values'

	funct_vals_1_sh_name = 'function values 1'
	
	funct_vals_2_sh_name = 'function values 2'

	vgp_suffix = '.vgp'

	drill_diam_addr = 'Rollomatic.LibCurve.Data.Curves.ToolProfileCurve-D0'

	separator = '-'

	# settings file name
	settings_filename = sm.settings_filename # settings path with respect to the project root

	# work directories section
	work_directories_section = sm.work_directories_section

	# master programs directory variable in the .ini file
	master_progs_dir_var = sm.master_progs_dir_var

	# result program directory variable in the .ini file
	res_prog_dir_var = sm.res_prog_dir_var

	# get the string paths from the settings module
	master_progs_dir_path = sm.master_progs_dir_path

	res_prog_dir_path = sm.res_prog_dir_path

	# declare master and result programs directories as windows paths
	master_progs_dir = Path(master_progs_dir_path)

	res_prog_dir = Path(res_prog_dir_path)

	# values_database_wb = wbm.WorkBook(Path(master_progs_dir / values_database_wb_filename))

	# values_database_sh = list(values_database_wb.wb.values())[0] # first wb sheet selection, it's a DataFrame containing all the recorded values information (val_name, val_descr, val_addr)