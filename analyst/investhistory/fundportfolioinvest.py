import datetime

import pandas as pd
import numpy as np
from typing import Union, List, Generator

from analyst.investhistory.singlefundinvest import SingleFundInvestAnalyst
from analyst.investhistory.calc_tools import MIRR, period_performance
from dataUtils.dataApis.funds.fundhist import FundDataManager
from dataUtils.dataApis.trading.tradingbook import TradingDataManager
from utils.const import FREQ


class PortfolioFundInvestAnalyst(dict):
	def __init__(self):
		super().__init__()

		self.tdm = TradingDataManager()
		self.fdm = FundDataManager()

		touched = self.tdm.get_touched()
		for fund_id in touched:
			self[fund_id] = SingleFundInvestAnalyst(fund_id)

	def summarize_trade(self) -> pd.DataFrame:
		# first get all unique dates
		all_dates = pd.Index([])
		for fund_id, sfia in self.items():
			fund_df = sfia.get_invest_stat()
			all_dates = all_dates.append(fund_df.index)

		df = pd.DataFrame(index = all_dates.unique().sort_values(ascending = True), columns = ['MVt', 'Gt', 'At', 'Dt', "Invt", "Witt", 'CFt'])

		for fund_id, sfia in self.items():
			fund_df = sfia.get_invest_stat()
			fund_df = fund_df[['MVt', 'Gt', 'At', 'Dt', "Invt", "Witt", 'CFt']]
			df = df.add(fund_df, fill_value = 0)

		return df

	def stat_trade(self) -> pd.DataFrame:
		subtrade_summary = self.summarize_trade()

		# update values
		accum_invest = 0
		accum_withdraw = 0
		MV = 0

		for i, date in enumerate(subtrade_summary.index):
			Gt, At, Dt, Invt, Witt, CFt = subtrade_summary.loc[date, ["Gt", "At", "Dt", "Invt", "Witt", "CFt"]]

			HPR = 0 if MV == 0 else (Gt - At) / MV  # one-day holding period return, equals fund return adjusted for transaction cost

			# update MV to current day value
			MV = subtrade_summary.loc[date, "MVt"]

			accum_invest = accum_invest + Invt + At
			accum_withdraw = accum_withdraw + Witt + Dt
			accum_profit = MV + accum_withdraw - accum_invest
			accounting_r = accum_profit / accum_invest  # accumulative accounting profit margin

			# make record to the table
			subtrade_summary.loc[date, "InvestAccum"] = accum_invest
			subtrade_summary.loc[date, "WithdrawAccum"] = accum_withdraw
			subtrade_summary.loc[date, "HPR"] = HPR
			subtrade_summary.loc[date, "InvestorReturnAccum"] = accounting_r

		return subtrade_summary

	def calc_current_stat(self) -> dict:
		subtrade_summary = self.stat_trade()

		start_dt = subtrade_summary.index.min()
		end_dt = subtrade_summary.index.max()

		trading_days = len(subtrade_summary)
		invest_period = (end_dt - start_dt).days
		Gt, HPR, MV, accum_invest, accum_withdraw, accounting_r = subtrade_summary.loc[end_dt, ["Gt", "HPR", "MVt", "InvestAccum", "WithdrawAccum", "InvestorReturnAccum"]]

		accum_profit = MV + accum_withdraw - accum_invest
		accounting_r_ann = np.log(1 + accounting_r) * 365 / invest_period

		# when calculating MIRR, should adjust last CF as if we sell all the position out
		# the last CF should be increase by MV
		CFs = list(subtrade_summary["CFt"].values)
		CFs[-1] += MV
		mirr, mirr_ann = MIRR(subtrade_summary.index, CFs)

		# add transaction cost and dividend analysis
		total_div = subtrade_summary["Dt"].sum()
		total_trans = subtrade_summary["At"].sum()
		trans_rate = total_trans / (accum_withdraw + accum_invest - total_div - total_trans)

		# if accounting_r > TWR:  investor's operation has positive value: beat the fund through buy/sell

		return {
			"Start Date": start_dt,
			"End Date": end_dt,
			"Calendar Days": invest_period,
			"Trading Days": trading_days,

			"Last Gain/Loss": Gt,
			"Last Return" : HPR,

			"Total Invest": accum_invest,
			"Total Withdraw": accum_withdraw,
			"Market Value": MV,
			"Accum Profit": accum_profit,

			"Invest Return": accounting_r,
			"Invest Return Ann.": accounting_r_ann,
			"MIRR": mirr,
			"MIRR Ann.": mirr_ann,

			"Total Dividend": total_div,
			"Total Fee": total_trans,
			"Fee Rate": trans_rate,
		}

	def stat_by_period(self, freq : FREQ = FREQ.MONTH) -> pd.DataFrame:
		subtrade_summary = self.summarize_trade()
		#subtrade_summary.to_csv("port.csv")
		return period_performance(subtrade_summary, freq = freq)




if __name__ == '__main__':
	pfia = PortfolioFundInvestAnalyst()
	#pfia.stat_trade().to_csv("portfolio.csv")
	# kw = pfia.calc_current_stat()
	# for k, v in kw.items():
	# 	print(k, " => ", v)
	pfia.stat_by_period(FREQ.MONTH)