import datetime
import logging

import pandas as pd
from sqlalchemy import func, distinct

from dataUtils.dataApis.funds.fundhist import FundDataManager
from dataUtils.database.sqlapi import dbIO
from dataUtils.database.tables import TradeBook
from dataUtils.toolkits.investmentcalendar import InvCalendar


class TradingDataManager:
    def __init__(self):
        self.fdm = FundDataManager()

    def get_effective_date(self, trade_datetime:datetime.datetime):
        return InvCalendar.get_effect_date(trade_datetime)

    def get_price(self, fund_id, date : datetime.date):
        r = self.fdm.query_hist(fund_id, start_dt = date, end_dt = date)
        return float(r.loc[0, "net_value"])

    def buy(self, fund_id:str, trade_datetime:datetime.datetime,
                value:float, cost:float, price:float = None, amount:float = None,
                effect_date:datetime.date = None) -> None:
        """buy in a fund

        :param fund_id: the fund id
        :param trade_datetime: the specific trading date and time
        :param value: fund value bought in, net of transaction cost, equals price * amount
        :param cost: transaction cost/tax paid, cost + value = total investment
        :param price: if not given, search in database
        :param amount: if not given, search in database
        :param effect_date: date to confirm the transaction price
        :return: None
        """

        if effect_date is None:
            effect_date = self.get_effective_date(trade_datetime)

        record = {
            "fund_id" : fund_id,
            "trade_datetime" : trade_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "event" : "buy",
            "value" : value,
            "cost" : cost,
            "effect_date" : effect_date.strftime("%Y-%m-%d"),

        }

        r = self.fdm.query_hist(fund_id, start_dt = effect_date, end_dt = effect_date)

        if len(r) != 1:
            if price is None or amount is None:
                logging.error("No trading data available on this date, no record will be saved to db, "
                                "please check effective date or provide price and amount!!!!")
                return  # just quit

            else:
                logging.warning("No trading data available on this date, but since you provide price and amount"
                                "will make record on price and amount provided!!!!")

        else:
            # normal case, use price and amount queried from db
            price = float(r.loc[0, "net_value"])
            amount = float(value / price)

        record["price"] = price
        record["amount"] = amount

        dbIO.insert(TradeBook, record)

    def sell(self, fund_id:str, trade_datetime:datetime.datetime,
                value:float, cost:float, price:float = None, amount:float = None,
                effect_date:datetime.date = None) -> None:
        """sell out a fund

        :param fund_id: the fund id
        :param trade_datetime: the specific trading date and time
        :param value: fund value sell out, before transaction cost, equals price * amount
        :param cost: transaction cost/tax paid, value - cost = total refund
        :param price: if not given, search in database
        :param amount: if not given, search in database
        :param effect_date: date to confirm the transaction price
        :return: None
        """

        if effect_date is None:
            effect_date = self.get_effective_date(trade_datetime)

        record = {
            "fund_id" : fund_id,
            "trade_datetime" : trade_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "event" : "sell",
            "value" : value,
            "cost" : cost,
            "effect_date" : effect_date.strftime("%Y-%m-%d"),

        }

        r = self.fdm.query_hist(fund_id, start_dt = effect_date, end_dt = effect_date)

        if len(r) != 1:
            if price is None or amount is None:
                logging.error("No trading data available on this date, no record will be saved to db, "
                                "please check effective date or provide price and amount!!!!")
                return  # just quit

            else:
                logging.warning("No trading data available on this date, but since you provide price and amount"
                                "will make record on price and amount provided!!!!")

        else:
            # normal case, use price and amount queried from db
            price = float(r.loc[0, "net_value"])
            amount = float(value / price)

        record["price"] = price
        record["amount"] = amount

        dbIO.insert(TradeBook, record)

    def query_trade(self, fund_id : str = None, start_dt : datetime.date = datetime.date(1900,1,1), end_dt : datetime.date = datetime.date(2100,12,31)) -> pd.DataFrame:
        with dbIO.get_session() as s:
            query = s.query(TradeBook).filter(TradeBook.effect_date.between(start_dt, end_dt))
            if fund_id:
                query = query.filter(TradeBook.fund_id == fund_id)

        return dbIO.query_df(query)

    def query_trade_aggday(self, fund_id : str, start_dt : datetime.date = datetime.date(1900,1,1), end_dt : datetime.date = datetime.date(2100,12,31)):
        with dbIO.get_session() as s:
            query = s.query(
                TradeBook.effect_date,
                TradeBook.event,
                func.sum(TradeBook.value).label("value"),
                TradeBook.price,
                func.sum(TradeBook.amount).label("amount"),
                func.sum(TradeBook.cost).label("cost"),
            ).group_by(
                TradeBook.effect_date,
                TradeBook.event,
            ).filter(
                TradeBook.effect_date.between(start_dt, end_dt)
            ).filter(
                TradeBook.fund_id == fund_id
            )

        return dbIO.query_df(query)

    def get_touched(self) -> list:
        with dbIO.get_session() as s:
            query = s.query(distinct(TradeBook.fund_id).label("fund_id"))

        df = dbIO.query_df(query)
        return df["fund_id"].values






if __name__ == '__main__':

    # fund_id = "160222"
    # sb = SingleBook(fund_id)
    # sb.buy("2020-06-12", 500)
    # sb.buy("2020-07-03", 2000)
    # sb.buy("2020-07-08", 1000)
    # sb.sell("2020-07-17", 1888.52)
    # sb.tran_cost("2020-07-17", 7.41)
    # sb.sell("2020-07-17", 472.13)
    # sb.sell("2020-07-17", 1416.39)
    # sb.tran_cost("2020-07-17", 9.92)
    #
    # print(sb.histDf.loc["2020-06-11" : "2020-07-19", ["NetValue", "FullValue", "SplitRatio", "Div"]])
    #
    # for r in sb.records:
    #     print(pd.DataFrame.from_records([r]))

    tdm = TradingDataManager()
    # tdm.buy("160222", datetime.datetime(2020,6,12,12,45,6), 500, 0)
    # tdm.buy("160222", datetime.datetime(2020, 7, 3, 4, 39, 0), 2000, 0)
    # tdm.buy("160222", datetime.datetime(2020, 7, 7, 23, 16, 0), 1000, 0)
    # tdm.sell("160222", datetime.datetime(2020, 7, 16, 21, 9, 0), 1888.52, 7.41)
    # tdm.sell("160222", datetime.datetime(2020, 7, 16, 21, 25, 16), 472.13, 0)
    # tdm.sell("160222", datetime.datetime(2020, 7, 17, 8, 36, 15), 1416.39, 9.92)
    # tdm.buy("160222", datetime.datetime(2021, 1, 6, 12, 27, 0), 1000, 0)
    # tdm.buy("160222", datetime.datetime(2021, 1, 20, 21, 17, 26), 500, 0)

    # tdm.buy("217011", datetime.datetime(2019, 12, 12, 22, 5, 47), 500, 0)
    # tdm.buy("217011", datetime.datetime(2020, 1, 15, 7, 22, 30), 1000, 0)



