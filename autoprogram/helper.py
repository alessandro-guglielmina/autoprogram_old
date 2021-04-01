import pandas as pd
import tkinter as tk
import shutil
import threading
import os
from pathlib import Path
from tkinter import filedialog

from autoprogram import configdataparse as cdp
from autoprogram.openvgp import vgpio
from autoprogram import common

fam_dir_path = None

def try_decorator(target_method):
	"""
	This decorator is added to any confirm function, in order to print the error (if any) on the communication label
	"""
	def wrapper_function(*args, **kwargs):
		try:
			args[0].root.comm_label_write("")
			return target_method(*args, **kwargs)
		except ValueError as ve:
			args[0].root.comm_label_write(ve) # args[0] is self, i.e. the frame object (the page)
	return wrapper_function


class InitializationPage(object):
	@staticmethod
	def constant_page_setup(initialization_page_frame):
		"""
		Constant frame setup
		The selected directory can be either the family directory
		(create manual mode) or the directory containing the files
		we want to change (update mode)
		"""
		browse_label = tk.Label(initialization_page_frame, text="Select Directory: ", width=16)
		browse_label.grid(row=0, column=0, padx=4, pady=4)
		initialization_page_frame.browse_entry = tk.Entry(initialization_page_frame, width=34)
		initialization_page_frame.browse_entry.grid(row=0, column=1, padx=4, pady=4)
		initialization_page_frame.browse_butt = tk.Button(initialization_page_frame, text="Browse", width=10)
		initialization_page_frame.browse_butt.grid(row=0, column=2, padx=4, pady=4)

	@try_decorator
	def set_fam_dir_path(initialization_page_frame, initialdir):
		"""
		Set the global variable fam_dir_path. Browse button to look for the family directory. If the directory doesn't exists, throws a ValueError
		"""
		if not os.path.isdir(initialdir):
			raise ValueError("Specified master program directory doesn't exist")
		# Set the global variable fam_dir_path
		global fam_dir_path
		fam_dir_path = Path(filedialog.askdirectory(initialdir=initialdir))
		initialization_page_frame.browse_entry.insert(0, fam_dir_path.as_posix())

	@staticmethod
	def set_config_data():
		"""
		This method sets the configuration file dictionary (from which all the configuration data are read)
		"""
		try:
			# Set the global variable config_data
			global config_data
			config_data = cdp.ConfigData(fam_dir_path)
		except TypeError:
			raise ValueError("Select a folder")


class InputDataPage(object):
	"""
	Description
	"""
	@staticmethod
	def to_widget_name(data_name: str):
		"""
		This method replace the "." with "_", because the dot results in a bad widget name error
		"""
		widget_name = data_name.replace(".", "_").lower()
		return widget_name

	@staticmethod
	def grid_gui_data_entries(input_data_page):
		"""
		Takes input data description from the configuration file and grid in the page
		"""
		for i, (inp_data_name, inp_data_descr) in enumerate(zip(config_data.inp_df.data_name, config_data.inp_df.data_descr)):
			inp_data_entry = tk.Entry(input_data_page, width=20, name=InputDataPage.to_widget_name(inp_data_name))
			inp_data_label = tk.Label(input_data_page, width=20, text=inp_data_descr, name=InputDataPage.to_widget_name(inp_data_name + "_descr")) # inp_data_name + "_descr" is a unique id for the decription labels
			inp_data_entry.grid(row=i, column=1, padx=4, pady=4)
			inp_data_label.grid(row=i, column=0, padx=4, pady=4)

	@staticmethod
	def get_gui_raw_data(input_data_page, input_data_names):
		"""
		This method collect the raw string inputs inserted by the user (it's one way to get input data)
		"""
		raw_inp_data_list = []
		for inp_data_name in input_data_names:
			data_entry = input_data_page.nametowidget(InputDataPage.to_widget_name(inp_data_name))
			string_inp_data_i = data_entry.get()
			try:
				raw_inp_data_i = [float(string_inp_data_i)]
			except ValueError:
				pass
			raw_inp_data_list.append(raw_inp_data_i)
		raw_inp_data = pd.Series(raw_inp_data_list)
		return raw_inp_data

	@staticmethod
	def forget_gui_data_entries(input_data_page):
		"""
		Forget the previously gridded widgets
		"""
		for i, (inp_data_name, inp_data_descr) in enumerate(zip(config_data.inp_df.data_name, config_data.inp_df.data_descr)):
			input_data_page.nametowidget(InputDataPage.to_widget_name(inp_data_name)).grid_forget()
			input_data_page.nametowidget(InputDataPage.to_widget_name(inp_data_name + "_descr")).grid_forget() # inp_data_name + "_descr" is a unique id for the decription labels


class CreateProgramPage(object):
	"""
	In this page the program is updated with data from the user and from the tables
	"""
	@staticmethod
	def set_diam_val():
		"""
		This method set the variable self.diam_val to the diameter value inserted by the user
		"""
		filt = config_data.inp_df.data_name == config_data.diam_name
		# Set the global variable diam_val
		global diam_val
		diam_val = float(config_data.inp_df.loc[filt, "raw_data"][0][0])

	@staticmethod
	def get_update_prog_list():
		return fam_dir_path.rglob('*' + common.vgp_suffix)

	@staticmethod
	def set_low_up_res_prog_paths():
		"""
		This method sets the lower, upper and result program paths as global variables
		"""
		def get_diam_val(prog_path):
			"""
			This method returns the diameter value of the program path passed as argument
			"""
			with vgpio.VgpProgram(prog_path, config_data.diam_name) as prog:
				return prog.initial_diam

		prog_paths =pd.Series(fam_dir_path.rglob('*' + common.vgp_suffix))
		prog_diam_vals = pd.Series(prog_paths.apply(get_diam_val))
		fam_progs_df = pd.DataFrame({"path": prog_paths, "diam_val": prog_diam_vals})
		# Enclosing and master programs selection
		# Lower program
		low_filt = fam_progs_df["diam_val"] <= diam_val
		low_progs_df = fam_progs_df.loc[low_filt, :].reset_index(drop=True)
		try:
			low_prog_path = low_progs_df.loc[(low_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		except ValueError:
			raise ValueError("The selected diameter is lower than the master programs.")
		# Upper program
		up_filt = fam_progs_df["diam_val"] >= diam_val
		up_progs_df = fam_progs_df.loc[up_filt, :].reset_index(drop=True)
		try:
			up_prog_path = up_progs_df.loc[(up_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		except ValueError:
			raise ValueError("The selected diameter is higher than the master programs.")
		# Master program
		master_prog_path = fam_progs_df.loc[(fam_progs_df["diam_val"] - diam_val).abs().argmin(), "path"]
		# Copy the master program to the result program path
		res_prog_path = common.res_progs_dir.joinpath(res_prog_name + common.vgp_suffix)
		# Make the result directory, if doesn't already exist
		os.makedirs(os.path.dirname(res_prog_path), exist_ok=True)
		shutil.copyfile(master_prog_path, res_prog_path) # copy the master program file to the result directory
		# Create VGP program objects
		global low_prog, up_prog
		if low_prog_path != up_prog_path:
			low_prog, up_prog = vgpio.VgpProgram(low_prog_path, config_data.diam_name), vgpio.VgpProgram(up_prog_path, config_data.diam_name)
		else:
			low_prog, up_prog = None, None
		global res_prog
		res_prog = vgpio.VgpProgram(res_prog_path, config_data.diam_name)

	@staticmethod
	def scale_tool():
		"""
		Save raw input data from the user in config_data.inp_df, aprsing val and sect_perc
		"""
		with low_prog, up_prog: # indented context manager for the enclosing programs
			res_prog.scale_tool(diam_val, low_prog, up_prog) # res_prog has already been open with the context manager in gui.py