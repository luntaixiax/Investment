from sqlalchemy import and_
from sqlalchemy.sql import func

from dataUtils.dataApis.funds.openmarketfund import getFundMergedHist
from dataUtils.database.sqlapi import dbIO

from dataUtils.database.tables import MutualFundHist


dbIO.register()

# fund_id = "166002"
# df = getFundMergedHist(fund_id)
# df["date"] = df["date"].astype('str')
# print(df)
#
# dbIO.insert_df(MutualFundHist, df)





# get largest net_value between 2020-12-23 to 2021-01-15
with dbIO.get_session() as s:
    query = s.query(func.max(MutualFundHist.net_value)).filter(and_(MutualFundHist.fund_id == "166002", MutualFundHist.date.between('2020-12-23', '2021-01-15')))
    print(query.scalar())

    query = s.query(
        func.date_format(MutualFundHist.date, '%Y-%m').label('yr_m'),
        func.sum(MutualFundHist.pnl).label('pnl'),
        func.sum(MutualFundHist.div).label("div")
    ).filter(MutualFundHist.fund_id == "166002").group_by(func.date_format(MutualFundHist.date, '%Y-%m'))
    print(dbIO.query_df(query))

    query = s.query(func.max(MutualFundHist.date)).filter(
        MutualFundHist.fund_id == "166002")
    print(query.scalar())

