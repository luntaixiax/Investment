import pandas as pd


def price_adjuster(divs, splits):
	def func(origin):
		cum_split = splits.cumprod()
		adj_div = (divs * cum_split).cumsum()
		factor = cum_split * origin + adj_div
		ff = origin.iloc[-1] / factor.iloc[-1]
		return ff * factor
	return func

def volume_adjuster(splits):
	def func(origin):
		cum_split = splits[::-1].cumprod()
		return cum_split * origin
	return func