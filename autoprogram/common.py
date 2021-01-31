from pathlib import Path
import os
import numpy as np
import pandas as pd

from autoprogram import settingsparser as sp

copyright_header = 'AutoProgram.\nCopyright \xc2\xa9 2020 Guglielmina Alessandro. All rights reserved.\n'
vgp_suffix = '.vgp'
separator = '-'
# settings file name
settings_filename = sp.settings_filename # settings path with respect to the project root
# work directories section
work_directories_section = sp.work_directories_section
# master programs directory variable in the .ini file
master_progs_dir_var = sp.master_progs_dir_var
# result program directory variable in the .ini file
res_progs_dir_var = sp.res_progs_dir_var
# get the string paths from the settings module
master_progs_dir_path = sp.master_progs_dir_path
res_progs_dir_path = sp.res_progs_dir_path
# declare master and result programs directories as windows paths
master_progs_dir = Path(master_progs_dir_path)
res_progs_dir = Path(res_progs_dir_path)