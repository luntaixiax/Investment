import datetime


def str2date(string, fmt = "day"):
	if isinstance(string, (datetime.date, datetime.datetime)):
		return datetime2date(string)
	return datetime2date(datetime.datetime.strptime(string, "%Y-%m-%d"))

def datetime2date(dtt):
	return datetime.date(dtt.year, dtt.month, dtt.day)