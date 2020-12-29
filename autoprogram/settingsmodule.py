import configparser


# settings file name
settings_filename = 'autoprogram/settings.ini' # settings path with respect to the project root

# work directories section
work_directories_section = 'work_directories'

# master programs directory variable in the .ini file
master_progs_dir_var = 'master_progs_dir'

# result program directory variable in the .ini file
res_progs_dir_var = 'res_progs_dir'

# instantiate
config = configparser.ConfigParser()

# parse settings file
config.read(settings_filename)

# read string values from the working directories section of the config file
master_progs_dir_path = config.get(work_directories_section, master_progs_dir_var)

res_progs_dir_path = config.get(work_directories_section, res_progs_dir_var)


def save_work_dirs(master_progs_dir_path, res_progs_dir_path):

	config.set(work_directories_section, master_progs_dir_var, master_progs_dir_path)

	config.set(work_directories_section, res_progs_dir_var, res_progs_dir_path)

	# save to a file
	with open(settings_filename, 'w') as configfile:
		config.write(configfile)