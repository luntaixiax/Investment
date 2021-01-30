import datetime
import logging
from sqlalchemy import func, and_
import pandas as pd

from dataUtils.configs.configmanager import CONFIG_INVESTMENT
from dataUtils.dataApis.funds.openmarketfund import getFundMergedHist
from dataUtils.database.sqlapi import dbIO
from dataUtils.database.tables import MutualFundHist

# FUND_WATCH_LIST = ["481001", "003095"]


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
                df["date"] = df["date"].astype('str')

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

        for fund_id in FUND_WATCH_LIST:
            # get latest data
            df = getFundMergedHist(fund_id)

            # get latest date from df
            max_date_df = df["date"].max()

            # find latest date in database
            with dbIO.get_session() as s:
                max_date_db = pd.Timestamp(s.query(func.max(MutualFundHist.date)).filter(MutualFundHist.fund_id == fund_id).scalar())
                n_records = s.query(MutualFundHist).filter(MutualFundHist.fund_id == fund_id).count()


            if n_records == 0:
                # no record being found
                logging.info("No record being found for %s, will update_all all" % fund_id)
                df["date"] = df["date"].astype('str')
                dbIO.insert_df(MutualFundHist, df)

            else:
                if max_date_df > max_date_db:
                    increment_records = df[df["date"] > max_date_db]
                    logging.info("Find %d new records for %s to update_all" % (len(increment_records), fund_id))

                    increment_records["date"] = increment_records["date"].astype('str')
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

    def stat_hist(self, fund_id : str, freq : str = "month") -> pd.DataFrame:
        self.check_fund(fund_id)
        freq_str = {
            "year" : "%Y",
            "month" : "%Y-%m",  # 2017-08 : 2017 Aug
            "week" : "%x-%u"  # 2017-48 :  week 48 in 2017
        }.get(freq)

        with dbIO.get_session() as s:
            # find the year/month/week end date
            q1 = s.query(
                func.max(MutualFundHist.date).label("max_date"),
            ).group_by(
                func.date_format(MutualFundHist.date, freq_str)
            ).filter(
                MutualFundHist.fund_id == fund_id
            ).subquery()

            # find the corresponding balance value at stat end date for each period
            q2 = s.query(
                MutualFundHist.date,
                MutualFundHist.net_value,
                MutualFundHist.full_value,
                MutualFundHist.equiv_cash,
                MutualFundHist.position_value,
            ).join(
                q1, q1.c.max_date == MutualFundHist.date
            ).filter(
                MutualFundHist.fund_id == fund_id
            ).subquery()

            # aggregate the results
            query = s.query(
                func.date_format(MutualFundHist.date, freq_str).label(freq),
                func.count(MutualFundHist.date).label("count"),  # number of trading days/records
                q2.c.net_value,  # balance at period end
                q2.c.full_value,  # balance at period end
                q2.c.equiv_cash,  # balance at period end
                q2.c.position_value,  # balance at period end
                func.sum(MutualFundHist.div).label("div"),  # accumulative dividend
                func.exp(func.sum(func.ln(MutualFundHist.split_ratio))).label("split_ratio"),  # cumprod of split during that period
                func.sum(MutualFundHist.pnl).label('pnl'),  # sum of pnl
                (func.exp(func.sum(func.ln(1 + MutualFundHist.daily_return))) - 1).label("return")  # cumprod of return (period return)
            ).join(
                q2, func.date_format(q2.c.date, freq_str) == func.date_format(MutualFundHist.date, freq_str)
            ).filter(
                MutualFundHist.fund_id == fund_id
            ).group_by(
                func.date_format(MutualFundHist.date, freq_str)
            )

        return dbIO.query_df(query)



if __name__ == '__main__':
    #dbIO.register()

    fdm = FundDataManager()
    fdm.reset()
    #print(fdm.stat_hist("160222"))