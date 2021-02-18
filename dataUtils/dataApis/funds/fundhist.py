import datetime
import logging
from sqlalchemy import func, and_
import pandas as pd

from dataUtils.configs.configmanager import CONFIG_INVESTMENT
from dataUtils.dataApis.funds.openmarketfund import getFundMergedHist
from dataUtils.database.sqlapi import dbIO
from dataUtils.database.tables import MutualFundHist

# FUND_WATCH_LIST = ["481001", "003095"]
from dataUtils.toolkits.conversions import str2date
from dataUtils.toolkits.investmentcalendar import InvCalendar
from utils.const import FREQ


class FundDataManager:
    def __init__(self):
        pass

    def check_new(self) -> None:
        # only update ones that are in the watch list but not in the database
        FUND_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("fund")

        # check list in the database
        with dbIO.get_session() as s:
            query = s.query(MutualFundHist.fund_id).distinct()

        db_list = dbIO.query_df(query)

        for fund_id in FUND_WATCH_LIST:
            if fund_id not in db_list["fund_id"].values:
                logging.info("%s is in watch list but not in db, downloading now..." % fund_id)
                df = getFundMergedHist(fund_id)
                df["date"] = df["date"].apply(str2date)

                dbIO.insert_df(MutualFundHist, df)

    def check_fund(self, fund_id: str) -> None:
        # check if fund_id data is available
        FUND_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("fund")

        if fund_id not in FUND_WATCH_LIST:
            CONFIG_INVESTMENT.addWatchList("fund", [fund_id])

        self.check_new()


    def update_all(self) -> None:
        # make database up to date
        FUND_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("fund")
        recent_trade_date = InvCalendar.get_recent_trade_date()

        for fund_id in FUND_WATCH_LIST:
            # find latest date in database
            with dbIO.get_session() as s:
                max_date_db = pd.Timestamp(s.query(func.max(MutualFundHist.date)).filter(MutualFundHist.fund_id == fund_id).scalar())
                n_records = s.query(MutualFundHist).filter(MutualFundHist.fund_id == fund_id).count()

            if n_records == 0:
                # no record being found
                logging.info("No record being found for %s, will update_all all" % fund_id)
                df = getFundMergedHist(fund_id)
                df["date"] = df["date"].apply(str2date)
                dbIO.insert_df(MutualFundHist, df)

            else:
                if recent_trade_date > max_date_db:
                    df = getFundMergedHist(fund_id)
                    increment_records = df[df["date"] > max_date_db]
                    logging.info("Find %d new records for %s to update_all" % (len(increment_records), fund_id))

                    increment_records["date"] = increment_records["date"].apply(str2date)
                    dbIO.insert_df(MutualFundHist, increment_records)
                else:
                    logging.info("No new record to update_all for %s, have total of %d records" % (fund_id, n_records))


    def reset(self) -> None:
        # delete all records and restore
        FUND_WATCH_LIST = CONFIG_INVESTMENT.getWatchList("fund")

        with dbIO.get_session() as s:
            s.query(MutualFundHist).filter(MutualFundHist.fund_id.in_(FUND_WATCH_LIST)).delete(synchronize_session = False)

        self.update_all()

    def query_hist(self, fund_id : str, start_dt : datetime.date = datetime.date(1900,1,1), end_dt : datetime.date = datetime.date(2100,12,31)) -> pd.DataFrame:
        self.check_fund(fund_id)
        with dbIO.get_session() as s:
            query = s.query(MutualFundHist).filter(and_(MutualFundHist.fund_id == fund_id, MutualFundHist.date.between(start_dt, end_dt)))

        return dbIO.query_df(query)

    def query_div(self, fund_id : str, start_dt : datetime.date = datetime.date(1900,1,1), end_dt : datetime.date = datetime.date(2100,12,31)) -> pd.DataFrame:
        self.check_fund(fund_id)
        with dbIO.get_session() as s:
            query = s.query(MutualFundHist).filter(and_(MutualFundHist.fund_id == fund_id, MutualFundHist.date.between(start_dt, end_dt), MutualFundHist.div > 0))

        return dbIO.query_df(query)

    def query_split(self, fund_id : str, start_dt : datetime.date = datetime.date(1900,1,1), end_dt : datetime.date = datetime.date(2100,12,31)) -> pd.DataFrame:
        self.check_fund(fund_id)
        with dbIO.get_session() as s:
            query = s.query(MutualFundHist).filter(and_(MutualFundHist.fund_id == fund_id, MutualFundHist.date.between(start_dt, end_dt), MutualFundHist.split_ratio != 1))

        return dbIO.query_df(query)

    def stat_hist(self, fund_id : str, freq : FREQ = FREQ.MONTH) -> pd.DataFrame:
        self.check_fund(fund_id)
        freq_str = freq.value.sql_fmt

        with dbIO.get_session() as s:
            subq = s.query(
                MutualFundHist.date,  # number of trading days/records
                MutualFundHist.fund_id,
                func.first_value(MutualFundHist.net_value).over(
                    partition_by = func.date_format(MutualFundHist.date, freq_str),
                    order_by = MutualFundHist.date.desc()
                ).label("net_value"),  # balance at period end
                func.first_value(MutualFundHist.full_value).over(
                    partition_by = func.date_format(MutualFundHist.date, freq_str),
                    order_by = MutualFundHist.date.desc()
                ).label("full_value"),  # balance at period end
                func.first_value(MutualFundHist.equiv_cash).over(
                    partition_by = func.date_format(MutualFundHist.date, freq_str),
                    order_by = MutualFundHist.date.desc()
                ).label("equiv_cash"),  # balance at period end
                func.first_value(MutualFundHist.position_value).over(
                    partition_by = func.date_format(MutualFundHist.date, freq_str),
                    order_by = MutualFundHist.date.desc()
                ).label("position_value"),  # balance at period end
                MutualFundHist.div,  # accumulative dividend
                MutualFundHist.split_ratio,  # cumprod of split during that period
                MutualFundHist.pnl,  # sum of pnl
                MutualFundHist.daily_return  # cumprod of return (period return)
            ).filter(
                MutualFundHist.fund_id == fund_id
            ).subquery()

            # aggregate the results
            query = s.query(
                func.date_format(subq.c.date, freq_str).label("date"),
                subq.c.fund_id,
                func.count(subq.c.date).label("count"),  # number of trading days/records
                subq.c.net_value,  # balance at period end
                subq.c.full_value,  # balance at period end
                subq.c.equiv_cash,  # balance at period end
                subq.c.position_value,  # balance at period end
                func.sum(subq.c.div).label("div"),  # accumulative dividend
                func.exp(func.sum(func.ln(subq.c.split_ratio))).label("split_ratio"),  # cumprod of split during that period
                func.sum(subq.c.pnl).label('pnl'),  # sum of pnl
                (func.exp(func.sum(func.ln(1 + subq.c.daily_return / 100))) - 1).label("return")  # cumprod of return (period return)
            ).filter(
                subq.c.fund_id == fund_id
            ).group_by(
                func.date_format(subq.c.date, freq_str)
            )

        return dbIO.query_df(query)



if __name__ == '__main__':
    #dbIO.register()

    fdm = FundDataManager()
    fdm.reset()
    df = fdm.stat_hist(fund_id = "160222")
    print(df)