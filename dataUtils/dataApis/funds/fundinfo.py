from sqlalchemy import or_

from dataUtils.dataApis.funds.openmarketfund import getAllFundInfo
from dataUtils.database.sqlapi import dbIO
from dataUtils.database.tables import MutualFundInfo

import pandas as pd

class FundInfoManager:

	@ classmethod
	def update(cls):
		# get all info online
		df = getAllFundInfo()

		# compare funds in the db and from online to check if any missing/update
		fund_list = df

		with dbIO.get_session() as s:
			query = s.query(MutualFundInfo.fund_id)

		db_list = dbIO.query_df(query)

		missing = fund_list[fund_list["fund_id"].isin(db_list["fund_id"]) == False]

		dbIO.insert_df(MutualFundInfo, missing)

	@ classmethod
	def query_info(cls, fund_id : str) -> pd.DataFrame:
		with dbIO.get_session() as s:
			query = s.query(MutualFundInfo).filter(MutualFundInfo.fund_id == fund_id)

		return dbIO.query_df(query)

	@ classmethod
	def blur_query(cls, key_word : str) -> pd.DataFrame:
		search = "%{}%".format(key_word)
		with dbIO.get_session() as s:
			query = s.query(MutualFundInfo).filter(or_(MutualFundInfo.fund_id.like(search), MutualFundInfo.fund_name.like(search)))

		return dbIO.query_df(query)



if __name__ == '__main__':
	#FundInfoManager.update()

	print(FundInfoManager.blur_query(key_word = "招商安泰"))