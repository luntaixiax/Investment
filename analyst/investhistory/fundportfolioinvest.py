from dataUtils.dataApis.funds.fundhist import FundDataManager
from dataUtils.dataApis.trading.tradingbook import TradingDataManager


class PortfolioFundInvestAnalyst:
	def __init__(self):
		self.tdm = TradingDataManager()
		self.fdm = FundDataManager()