import os
from itertools import compress

from autoprogram import common

# This function return the user inputs
def user_input(ch_list = None, ch_ids = None, cast = None, print_list = None): #(ch_list, ch_id, cast, print_list)
	# If there is a list of choices
	if ch_list is not None and ch_ids is not None:
		cast = str
		bound_val = True
		print_list = ''
		for i, j in zip(ch_ids, ch_list):
			print_list = print_list + f'Enter {i} for {j}\n'
		print_list = [print_list]
	# if there isn't
	elif cast is not None and print_list is not None:
		bound_val = False
	else:
		raise ValueError('Wrong arguments combination.')
	inp_list = []
	converted = False
	for i in print_list:
		os.system('clear')
		while True:
			try:
				inp_i = cast(input(f'{i}\n> ')) # user input call
				if bound_val: # (so cast = str and ch_id must be given)
					inp_i = inp_i.upper() # the choice must be capital to make the choice case insensitive
					if inp_i in ch_ids:
						bool_filt = [i == inp_i for i in ch_ids]
						ch = list(compress(ch_list, bool_filt))[0] # use boolean indexing on a list
						inp_i = ch # inp_val_i is reassigned with the choice corresponding to the chosen index
						converted = True
					else:
						os.system('clear')
						print("Input non among the possible choices.\n")
				if converted or not bound_val:
					os.system('clear')
					inp_list.append(inp_i)
					print("You have entered: " + str(inp_i) + "\n")
					break
			except ValueError:
				print("Wrong input type\n")
	res = inp_list
	return res # list([inp1, inp2, ...])


def select_family(fam_name_list):
		fam_name_ids = [str(i + 1) for i in list(range(len(fam_name_list)))]
		# Acquire user input
		print('Select family:\n')
		common.Variables.fam_name = user_input(ch_list = fam_name_list, ch_ids = fam_name_ids)[0] # 'ch_fam'
		os.system('clear')

def print_tool_type():
	if common.Variables.tool_type:
		print("Tool type is: " + common.Variables.tool_type)
	else:
		print("Tool type not assigned yet.")


def select_position(Position):
		ch_list = ['confirm', 'repeat', 'move back']
		ch_ids = ['C', 'R', 'B']
		ch = user_input(ch_list = ch_list, ch_ids = ch_ids)
		pos_select = ch[0]
		if (pos_select == 'confirm'):
			next_pos = Position.follow_pos
		elif (pos_select == 'repeat'):
			next_pos = Position.current_pos
		elif (pos_select == 'move back'):
			next_pos = Position.prev_pos
		return next_pos