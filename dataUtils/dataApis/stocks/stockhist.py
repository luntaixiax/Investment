import datetime
import logging
import pandas as pd
from sqlalchemy import func, and_

from dataUtils.configs.configmanager import CONFIG_INVESTMENT
from dataUtils.dataApis.stocks.calcs import price_adjuster, volume_adjuster
from dataUtils.dataApis.stocks.stockapi import AlphaQuote
from dataUtils.database.sqlapi import dbIO
from dataUtils.database.tables import StockHist
from dataUtils.toolkits.investmentcalendar import InvCalendar
from utils.const import FREQ


class StockHistManager:
	def __init__(self):
		pass

	def check_new(self) -> None:
		# only update ones that are in the watch list but not in the database
		STOCK_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("stock")

		# check list in the database
		with dbIO.get_session() as s:
			query = s.query(StockHist.stock_id).distinct()

		db_list = dbIO.query_df(query)

		for stock_id in STOCK_WATCH_LIST:
			if stock_id not in db_list["stock_id"].values:
				logging.info("%s is in watch list but not in db, downloading now..." % stock_id)
				df = AlphaQuote.getHist(stock_id = stock_id, quick = False, fmt = True)

				dbIO.insert_df(StockHist, df)

	def check_stock(self, stock_id: str) -> None:
		# check if stock_id data is available
		STOCK_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("stock")

		if stock_id not in STOCK_WATCH_LIST:
			CONFIG_INVESTMENT.addWatchList("stock", [stock_id])

		self.check_new()

	def update_all(self) -> None:
		# make database up to date
		STOCK_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("stock")
		recent_trade_date = InvCalendar.get_recent_trade_date()  # TODO: get us/canada trading dates

		for stock_id in STOCK_WATCH_LIST:
			# find latest date in database
			with dbIO.get_session() as s:
				max_date_db = pd.Timestamp(
					s.query(func.max(StockHist.date)).filter(StockHist.stock_id == stock_id).scalar())
				n_records = s.query(StockHist).filter(StockHist.stock_id == stock_id).count()

			if n_records == 0 or (recent_trade_date - max_date_db.date()).days >= 100:
				# no record being found
				logging.info("No record being found for %s, will update_all all" % stock_id)
				df = AlphaQuote.getHist(stock_id = stock_id, quick = False, fmt = True)

				dbIO.insert_df(StockHist, df)

			else:
				if recent_trade_date > max_date_db.date():
					df = AlphaQuote.getHist(stock_id = stock_id, quick = True, fmt = True)
					increment_records = df[df["date"] > max_date_db]
					logging.info("Find %d new records for %s to update_all" % (len(increment_records), stock_id))

					dbIO.insert_df(StockHist, increment_records)
				else:
					logging.info("No new record to update_all for %s, have total of %d records" % (stock_id, n_records))

	def reset(self) -> None:
		# delete all records and restore
		STOCK_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("stock")

		with dbIO.get_session() as s:
			s.query(StockHist).filter(StockHist.stock_id.in_(STOCK_WATCH_LIST)).delete(
				synchronize_session = False)

		self.update_all()

	def query_hist(self, stock_id: str, start_dt: datetime.date = datetime.date(1900, 1, 1), end_dt: datetime.date = datetime.date(2100, 12, 31)) -> pd.DataFrame:
		self.check_stock(stock_id)
		with dbIO.get_session() as s:
			query = s.query(StockHist).filter(
				and_(StockHist.stock_id == stock_id, StockHist.date.between(start_dt, end_dt)))

		return dbIO.query_df(query)


	def query_hist_adj(self, stock_id : str, start_dt: datetime.date = datetime.date(1900, 1, 1), end_dt: datetime.date = datetime.date(2100, 12, 31)) -> pd.DataFrame:
		"""return adjusted closing price and volume

		:param stock_id: stock symbol
		:param start_dt: start query date
		:param end_dt: end query date
		:return: pd.DataFrame(index = date, columns = ["close"])
		"""
		self.check_stock(stock_id)
		with dbIO.get_session() as s:
			query = s.query(StockHist).filter(StockHist.stock_id == stock_id)

		df = dbIO.query_df(query)
		pra = price_adjuster(df["div"], df["split"])
		vla = volume_adjuster(df["split"])

		return pd.DataFrame({
			"open" : pra(df["open"]).values,
			"high": pra(df["high"]).values,
			"low": pra(df["low"]).values,
			"close" : pra(df["close"]).values,
			"vol" : vla(df["vol"]).values,
		}, index = df["date"]).loc[start_dt : end_dt, :]


	def query_div(self, stock_id: str, start_dt: datetime.date = datetime.date(1900, 1, 1), end_dt: datetime.date = datetime.date(2100, 12, 31)) -> pd.DataFrame:
		self.check_stock(stock_id)
		with dbIO.get_session() as s:
			query = s.query(StockHist).filter(
				and_(StockHist.stock_id == stock_id, StockHist.date.between(start_dt, end_dt),
				     StockHist.div > 0))

		return dbIO.query_df(query)

	def query_split(self, stock_id: str, start_dt: datetime.date = datetime.date(1900, 1, 1), end_dt: datetime.date = datetime.date(2100, 12, 31)) -> pd.DataFrame:
		self.check_stock(stock_id)
		with dbIO.get_session() as s:
			query = s.query(StockHist).filter(
				and_(StockHist.stock_id == stock_id, StockHist.date.between(start_dt, end_dt),
				     StockHist.split != 1))

		return dbIO.query_df(query)

	def stat_hist(self, stock_id: str, freq: FREQ = FREQ.MONTH) -> pd.DataFrame:
		self.check_stock(stock_id)
		freq_str = freq.value.sql_fmt

		with dbIO.get_session() as s:
			# https://stackoverflow.com/questions/41840829/using-group-by-with-first-value-and-last-value

			# SELECT
			# 	g.stock_id,
			# 	date,
			# 	OPEN,
			# 	max( g.high ) AS high,
			# 	min( g.low ) AS low,
			# 	CLOSE,
			# 	sum( g.vol ) AS vol
			# FROM
			# 	(
			# SELECT
			# 	stockhist.stock_id,
			# 	DATE_FORMAT( stockhist.date, "%Y-%m" ) AS date,
			# 	first_value ( stockhist.`open` ) OVER ( PARTITION BY DATE_FORMAT( stockhist.date, "%Y-%m" ) ORDER BY stockhist.date ) AS OPEN,
			# 	stockhist.high,
			# 	stockhist.low,
			# 	first_value ( stockhist.`close` ) OVER ( PARTITION BY DATE_FORMAT( stockhist.date, "%Y-%m" ) ORDER BY stockhist.date DESC ) AS CLOSE,
			# 	stockhist.vol
			# FROM
			# 	stockhist
			# WHERE
			# 	stockhist.stock_id = "VSP.TO"
			# 	) AS g
			# WHERE
			# 	g.stock_id = "VSP.TO"
			# GROUP BY
			# 	date;

			subq = s.query(
				StockHist.stock_id,
				StockHist.date,
				func.first_value(StockHist.open).over(
					partition_by = func.date_format(StockHist.date, freq_str),
					order_by = StockHist.date
				).label("open"),  # open price
				StockHist.high,  # high
				StockHist.low,  # low
				func.first_value(StockHist.close).over(
					partition_by = func.date_format(StockHist.date, freq_str),
					order_by = StockHist.date.desc()
				).label("close"),  # close price
				StockHist.vol
			).filter(
				StockHist.stock_id == stock_id
			).subquery()

			query = s.query(
				subq.c.stock_id,
				func.date_format(subq.c.date, freq_str).label("date"),
				subq.c.open,  # open price
				func.max(subq.c.high).label("high"),  # high
				func.min(subq.c.high).label("low"),  # low
				subq.c.close,  # close price
				func.sum(subq.c.vol).label("vol")
			).filter(
				subq.c.stock_id == stock_id
			).group_by(
				func.date_format(subq.c.date, freq_str)
			)
		return dbIO.query_df(query)


if __name__ == '__main__':
	shm = StockHistManager()
	#shm.update_all()
	df = shm.stat_hist(stock_id = "VSP.TO")
	# #df.to_csv("stat.csv")
	print(df)