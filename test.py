import akshare as ak
import pandas as pd
import numpy as np
import logging
import re

def getFundHistNetPrice(fund_id):
    df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "单位净值走势")  \
        .drop(columns = ["日增长率"])  \
        .rename(columns = {"净值日期" : "Date", "单位净值" : "NetValue"})  \
        .set_index("Date")
    df.index = pd.to_datetime(df.index)
    df["NetValue"] = df["NetValue"].astype('float')
    return df

def getFundHistFullPrice(fund_id):
    df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "累计净值走势")  \
        .rename(columns = {"净值日期" : "Date", "累计净值" : "FullValue"})  \
        .set_index("Date")
    df.index = pd.to_datetime(df.index)
    df["FullValue"] = df["FullValue"].astype('float')
    return df

def extractDiv(string):
    if string in ["暂未披露"] or pd.isnull(string):
        logging.warning("Fund dividend undisclosed: %s, may cause calc error!" % string)
        return np.nan

    numbers = re.findall(r"\d+\.?\d*", string)
    if len(numbers) == 1:
        try:
            return float(numbers[0])
        except:
            logging.warning("Fund dividend number abnormal: %s!" % string)
            return np.nan

    return np.nan

def getFundHistDiv(fund_id):
    try:
        df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "分红送配详情") \
            .drop(columns = ["年份", "权益登记日", "分红发放日"]) \
            .rename(columns = {"除息日" : "ExDivDate", "每份分红" : "DivInfo"}) \
            .set_index("ExDivDate")
        df.index = pd.to_datetime(df.index)

        # extract dividend number
        df["Div"] = df["DivInfo"].apply(extractDiv)

    except:
        df = pd.DataFrame()
    return df

def extractSplit(string):
    if string in ["暂未披露"] or pd.isnull(string):
        logging.warning("Fund split undisclosed: %s, may cause calc error!" % string)
        return np.nan

    numbers = re.findall(r"\d+\.?\d*", string)
    if len(numbers) == 2:
        try:
            return float(numbers[1])
        except:
            logging.warning("Fund split number abnormal: %s!" % string)
            return np.nan

    return np.nan

def getFundHistSplit(fund_id):
    try:
        df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "拆分详情") \
            .drop(columns = ["年份", "拆分类型"]) \
            .rename(columns = {"拆分折算日" : "SplitDate", "拆分折算比例" : "SplitInfo"}) \
            .set_index("SplitDate")
        df.index = pd.to_datetime(df.index)

        # extract split number
        df["SplitRatio"] = df["SplitInfo"].apply(extractSplit)

    except:
        df = pd.DataFrame()
    return df


def getFundMergedHist(fund_id):
    netP = getFundHistNetPrice(fund_id)
    fullP = getFundHistFullPrice(fund_id)
    divs = getFundHistDiv(fund_id)
    splits = getFundHistSplit(fund_id)

    df = netP.join(fullP, how = "outer")
    df.loc[:, "Div"] = 0
    df.loc[:, "SplitRatio"] = 1

    maxdate = df.index.max()

    # merge dividend
    for date, row in divs.iterrows():
        if date <= maxdate:
            df.loc[date, "Div"] = row.get("Div")

    # merge split
    for date, row in splits.iterrows():
        if date <= maxdate:
            df.loc[date, "SplitRatio"] = row.get("SplitRatio")


    pnl = df["NetValue"] * df["SplitRatio"] - df["NetValue"].shift(periods = 1) + df["Div"]
    pnl2 = (df["FullValue"] - df["FullValue"].shift(periods = 1)) / df["SplitRatio"].cumprod().shift(periods = 1)

    checkError(pnl, pnl2, threshold = 1e-4, rounding = 4)
    df["PnL"] = pnl  # pnl2 has rounding problem because it magnifies the error

    df["EquivCash"] = (df["SplitRatio"].cumprod().shift(periods = 1) * df["Div"]).cumsum()
    df["PositionValue"] = df["SplitRatio"].cumprod() * df["NetValue"]

    df["Return"] = df["PnL"] / df["NetValue"].shift(periods = 1)


    #df.to_csv("test.csv")
    return df

def checkError(series1, series2, threshold = 1e-4, rounding = 4):
    max_error = ((series1.round(rounding) - series2.round(rounding)) / series1.round(rounding)).abs().max()

    if max_error > threshold:
        logging.warning("Results not match under two approachs, use with caution! Max Error(%%) = %.5f" % max_error)


if __name__ == '__main__':
    fund_em_fund_name_df = ak.fund_em_fund_name()
    print(fund_em_fund_name_df)

    # fund_id = "481001"
    # df = getFundMergedHist(fund_id)
