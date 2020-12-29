from pathlib import Path
import os
import numpy as np
import pandas as pd


from autoprogram import settingsmodule as sm
from autoprogram import wbmodule as wbm


copyright_header = 'AutoProgram.\nCopyright \xc2\xa9 2020 Guglielmina Alessandro. All rights reserved.\n'

config_file_wb_filename = 'configuration file.xlsx'

diam_name_sh_name = 'diameter name'

input_vals_sh_name = 'input values'

rel_vals_sh_name = 'related values'

funct_vals_1_sh_name = 'function values 1'

funct_vals_2_sh_name = 'function values 2'

vgp_suffix = '.vgp'

separator = '-'

# settings file name
settings_filename = sm.settings_filename # settings path with respect to the project root

# work directories section
work_directories_section = sm.work_directories_section

# master programs directory variable in the .ini file
master_progs_dir_var = sm.master_progs_dir_var

# result program directory variable in the .ini file
res_progs_dir_var = sm.res_progs_dir_var

# get the string paths from the settings module
master_progs_dir_path = sm.master_progs_dir_path

res_progs_dir_path = sm.res_progs_dir_path

# declare master and result programs directories as windows paths
master_progs_dir = Path(master_progs_dir_path)

res_progs_dir = Path(res_progs_dir_path)