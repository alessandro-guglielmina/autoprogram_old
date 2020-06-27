from pathlib import Path

# Copyright header
copyright_header = 'AutoProgram.\nCopyright \xc2\xa9 2020 Guglielmina Alessandro. All rights reserved.\n'

# Directories
master_progs_dir = Path('autoprogram/master_programs') # master programs directory
res_prog_dir = Path.home().joinpath('Work folders/Roaming/Desktop') # generated program directory

# Workbooks
'''
workbook containing the values to be inserted for each family, and a sheet called 'general values'
family values columns : val_name, rel
general values columns : val_name, val_addr, val_type, val_descr
'''
input_values_wb_path = Path('autoprogram/workbooks/input_values.xlsx')
# cutting parameters workbook, with each sheet corresponding to a cutting parameters category
cutting_params_wb_path = Path('autoprogram/workbooks/cutting_parameters.xlsx')

#File suffix
vgp_suffix = '.vgp'

# Drill variable names
drill_diam_addr = 'Rollomatic.LibCurve.Data.Curves.ToolProfileCurve@D0'
drill_flute_len_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.allFlute.flutes.flutes1.diamEdge.fluteLength'
drill_point_ang_addr = 'Rollomatic.LibCurve.Data.Curves.ToolProfileCurve@pA'
drill_first_spg_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.point.endrelief_from_attribute.oneAttribute.oneAttribute1.od_relief.multi_relief_allmulti.multi_relief.multi_relief1.rel_intern.relief_op_complete.relief_op_complete1.normal_field.func_relief_angle'
drill_meas_dist_addr = 'one_tooth.all_teeth.drill_type.drill_type1.n_Types.allFlute.flutes.flutes1.flute.flute_op.flute_op.flute_one_multi.flute_one_multi1.flute_Simple_Ext_.flute_Lw_X.flute_Simple_Choices.pourcent_rake_in'