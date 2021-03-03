import pandas as pd
import numpy as np

from analyst.generalintraproduct.statistics import test_stationary, markov_switching, hidden_markov
from dataUtils.dataApis.stocks.stockhist import StockHistManager


class PriceSeq:
	def __init__(self, prices : pd.Series):
		"""price sequence analyst

		:param prices: pandas series, index = date, col = price
		"""
		self.df = pd.DataFrame({
			"price" : prices.values
		}, index = prices.index)
		self.df["yield"] = np.log(self.df["price"].pct_change()+1)
		self.df["yield"].iloc[0] = 0
		# x = test_stationary(self.df["yield"].values)
		# print(x)
		# y = markov_switching(self.df["yield"].values, k_regimes = 4)
		# print(y)
		hidden_markov(self.df["yield"], n_state = 4)

	def regime(self):
		# divide stock returns into different regions
		# assume stock returns follow regime normal distribution
		# * consider including lagged macro variables, industry variables
		# use EM algorithm to get different regime parameters (mean, std)
		# use EM algorithm to predict regime
		# use HMM to predict
		pass

	def risk(self):
		# market risk, distribution, VaR
		# distribution
		pass

	def blind(self):
		# calculate blind investment return, distribution
		pass



if __name__ == '__main__':
	from matplotlib import pyplot as plt
	shm = StockHistManager()
	# shm.update_all()
	df = shm.query_hist_adj(stock_id = "FIE.TO")
	series = df["close"]

	ps = PriceSeq(series)
	# ps.df["yield"].plot()
	# plt.show()