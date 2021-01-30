import configparser
import json
import os
from myLibrary import MAIN_PATH


def getConfigDict(filepath, dataTypes):
	con = configparser.ConfigParser()
	con.read(filepath)

	df = con._sections
	for section, dtypes in dataTypes.items():
		for k, dtype in dtypes.items():
			if dtype == int:
				df[section][k] = con.getint(section, k)
			elif dtype == float:
				df[section][k] = con.getfloat(section, k)
			elif dtype == bool:
				df[section][k] = con.getboolean(section, k)
			else:
				raise ValueError("data types can only be int, float, bool")

	return df


def loadJSON(file):
	if isinstance(file, (list, dict)):
		return file
	elif isinstance(file, str):
		with open(file, "rb") as obj:
			return json.load(obj)
	else:
		raise ValueError("Please parse a file path or JS object")

def toJSON(js, file):
	with open(file, "w") as obj:
		json.dump(js, obj, indent = 4)


def getFilePath(relativePaths):
	# last being file name
	paths = relativePaths.split("/")
	return os.path.join(MAIN_PATH, *paths)