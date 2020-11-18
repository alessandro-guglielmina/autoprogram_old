from pathlib import Path

# Copyright header
copyright_header = 'AutoProgram.\nCopyright \xc2\xa9 2020 Guglielmina Alessandro. All rights reserved.\n'

# Working directories
master_progs_dir = 'C:/master programs' # master programs directory on my pc

#master_progs_dir = Path('...') # master programs directory on my corporate pc

res_prog_dir = 'Desktop' # result program directory on my pc (to be appended to home directory)

# res_prog_dir = 'Work folders/Roaming/Desktop' # generated program directory on my corporate pc (to be appended to home directory)

# Workbooks
'''
workbook containing the values to be inserted for each family, and a sheet called 'general values'
family values columns : val_name, rel
general values columns : val_name, val_addr, val_type, val_descr
'''
values_database_wb_filename = 'values database.xlsx'

# configuration file filename (to be appended to the selected family directory)
config_file_wb_filename = 'configuration file.xlsx'

# input values sheet name
config_vals_sh_name = 'configuration values'

# function values 1 sheet name
funct_vals_1_sh_name = 'function values 1'

# function values 2 sheet name
funct_vals_2_sh_name = 'function values 2'


#File suffix
vgp_suffix = '.vgp'

# Drill variable names
drill_diam_addr = 'Rollomatic.LibCurve.Data.Curves.ToolProfileCurve-D0'

# drill_flute_len_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.allFlute.flutes.flutes1.diamEdge.fluteLength'
# drill_point_ang_addr = 'Rollomatic.LibCurve.Data.Curves.ToolProfileCurve-pA'
# drill_first_spg_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.point.endrelief_from_attribute.oneAttribute.oneAttribute1.od_relief.multi_relief_allmulti.multi_relief.multi_relief1.rel_intern.relief_op_complete.relief_op_complete1.normal_field.func_relief_angle'
# drill_meas_dist_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.allFlute.flutes.flutes1.flute.flute_op.flute_op.flute_one_multi.flute_one_multi1.flute_Simple_Ext_.flute_Lw_X.flute_Simple_Choices.pourcent_rake_in'

separator = '-'