import datetime
import json
import urllib.request
from urllib.parse import urlencode

from dataUtils.toolkits.conversions import str2date
from utils.const import FREQ
import pandas as pd

def convert_num(x, rounding = 1.0, decimal = 3):
	try:
		y = float(x)
	except:
		y = None
	else:
		y = round(y / rounding, decimal)
	return y


class AlphaQuote:
	mainURL = "https://www.alphavantage.co/query"
	apiKey = "D39XMS1LJTP2AUD4"

	@ classmethod
	def _fetch(cls, params : dict) -> dict:
		url = "%s?%s" % (cls.mainURL, urlencode(params))

		f = urllib.request.urlopen(url)  # open the url
		content = f.read()  # read the content
		res = json.loads(content)  # save as json

		if res.get("Error Message"):
			raise ValueError(f"Invalid parameters: {res.get('Error Message')}")

		return res

	@ classmethod
	def getHist(cls, stock_id : str, quick : bool = False, fmt : bool = False) -> pd.DataFrame:
		params = {
			"function": "TIME_SERIES_DAILY_ADJUSTED",
			"symbol": stock_id,
			"outputsize": "compact" if quick else "full",  # full / compact
			"apikey": cls.apiKey,  # APP Key
			"datatype": "json",
		}

		res = cls._fetch(params)

		df = pd.DataFrame.from_dict(res.get("Time Series (Daily)"), orient = "index").astype('float')
		df.columns = ["open", "high", "low", "close", "adj_close", "vol", "div", "split"]

		if fmt:
			df["date"] = df.index#.astype(datetime.date)
			df["date"] = df["date"].apply(str2date)
			df.loc[:, "stock_id"] = stock_id
			df.reset_index(inplace = True, drop = True)

		df.drop(columns = "adj_close", inplace = True)

		return df

	@ classmethod
	def getOverview(cls, stock_id : str) -> dict:
		params = {
			"function": "OVERVIEW",
			"symbol": stock_id,
			"apikey": cls.apiKey,  # APP Key
		}

		res = cls._fetch(params)

		r = {
			"stock_id" : res.get("Symbol"),
			"ass_type" : res.get("AssetType"),
			"company": res.get("Name"),
			"exch": res.get("Exchange"),
			"cur": res.get("Currency"),
			"sec": res.get("Sector"),
			"ind": res.get("Industry"),
		}
		return r


	@ classmethod
	def getKeyFinancials(cls, stock_id : str) -> dict:
		params = {
			"function": "OVERVIEW",
			"symbol": stock_id,
			"apikey": cls.apiKey,  # APP Key
		}

		res = cls._fetch(params)

		r = {
			"stock_id" : res.get("Symbol"),
			"mkt_cap" : convert_num(res.get("MarketCapitalization"), rounding = 10e6),
			"bvps" : convert_num(res.get("BookValue"), rounding = 1.0),
			"shares" : convert_num(res.get("SharesOutstanding"), rounding = 10e6, decimal = 2),
			"p_b" : convert_num(res.get("PriceToBookRatio"), rounding = 1.0),
			"p_e_f" : convert_num(res.get("ForwardPE"), rounding = 1.0),
			"p_e_t" : convert_num(res.get("TrailingPE"), rounding = 1.0),
			"peg" : convert_num(res.get("PEGRatio"), rounding = 1.0),
			"eps" : convert_num(res.get("EPS"), rounding = 1.0),
			"div_y" : convert_num(res.get("DividendYield"), rounding = 0.01),
			"oprm" : convert_num(res.get("OperatingMarginTTM"), rounding = 0.01),
			"prfm": convert_num(res.get("ProfitMargin"), rounding = 0.01),
			"roe" : convert_num(res.get("ReturnOnEquityTTM"), rounding = 0.01),
			"ev_ebitda" : convert_num(res.get("EVToEBITDA"), rounding = 1.0),
			"prf_y" : convert_num(res.get("QuarterlyEarningsGrowthYOY"), rounding = 0.01),
			"tar_p" : convert_num(res.get("AnalystTargetPrice"), rounding = 1.0),
			"beta" : convert_num(res.get("Beta"), rounding = 1.0),
		}

		return r



if __name__ == '__main__':
	df = AlphaQuote.getHist(stock_id = "VSP.TO", quick = True, fmt = True)
	print(df)
	# r = AlphaQuote.getOverview(stock_id = "VSP.TO")
	# for k, v in r.items():
	# 	print(k, " => ", v)