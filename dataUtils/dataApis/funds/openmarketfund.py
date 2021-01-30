import akshare as ak
import demjson
import pandas as pd
import numpy as np
import logging
import re

import requests


def getFundHistNetPrice(fund_id):
    df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "单位净值走势")  \
        .drop(columns = ["日增长率"])  \
        .rename(columns = {"净值日期" : "date", "单位净值" : "net_value"})  \
        .set_index("date")
    df.index = pd.to_datetime(df.index)
    df["net_value"] = df["net_value"].astype('float')
    return df

def getFundHistFullPrice(fund_id):
    df = ak.fund_em_open_fund_info(fund = fund_id, indicator = "累计净值走势")  \
        .rename(columns = {"净值日期" : "date", "累计净值" : "full_value"})  \
        .set_index("date")
    df.index = pd.to_datetime(df.index)
    df["full_value"] = df["full_value"].astype('float')
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
        df["div"] = df["DivInfo"].apply(extractDiv)

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
        df["split_ratio"] = df["SplitInfo"].apply(extractSplit)

    except:
        df = pd.DataFrame()
    return df


def getFundMergedHist(fund_id):
    netP = getFundHistNetPrice(fund_id)
    fullP = getFundHistFullPrice(fund_id)
    divs = getFundHistDiv(fund_id)
    splits = getFundHistSplit(fund_id)

    df = netP.join(fullP, how = "outer")
    df.loc[:, "div"] = 0
    df.loc[:, "split_ratio"] = 1

    maxdate = df.index.max()

    # merge dividend
    for date, row in divs.iterrows():
        if date <= maxdate:
            df.loc[date, "div"] = row.get("div")

    # merge split
    for date, row in splits.iterrows():
        if date <= maxdate:
            df.loc[date, "split_ratio"] = row.get("split_ratio")


    pnl = df["net_value"] * df["split_ratio"] - df["net_value"].shift(periods = 1) + df["div"]
    pnl2 = (df["full_value"] - df["full_value"].shift(periods = 1)) / df["split_ratio"].cumprod().shift(periods = 1)

    checkError(pnl, pnl2, threshold = 1e-4, rounding = 4)
    df["pnl"] = pnl  # pnl2 has rounding problem because it magnifies the error

    df["equiv_cash"] = (df["split_ratio"].cumprod().shift(periods = 1) * df["div"]).cumsum()
    df["position_value"] = df["split_ratio"].cumprod() * df["net_value"]

    df["daily_return"] = 100 * df["pnl"] / df["net_value"].shift(periods = 1)

    df.loc[:, "fund_id"] = fund_id


    cols = [
        "fund_id", "date", "net_value", "full_value",
        "div", "split_ratio", "pnl", "equiv_cash",
        "position_value", "daily_return"
    ]
    return df.reset_index()[cols]


def checkError(series1, series2, threshold = 1e-4, rounding = 4):
    max_error = ((series1.round(rounding) - series2.round(rounding)) / series1.round(rounding)).abs().max()

    if max_error > threshold:
        logging.warning("Results not match under two approachs, use with caution! Max Error(%%) = %.5f" % max_error)


def getAllFundInfo():
    """
    personalized search for akshare: ak.fund_em_open_fund_daily()
    http://fund.eastmoney.com/fund.html#os_0;isall_0;ft_;pt_1
    :return: 当前交易日的所有开放式基金净值数据
    :rtype: pandas.DataFrame
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
    }
    url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
    params = {
        "t": "1",
        "lx": "1",
        "letter": "",
        "gsid": "",
        "text": "",
        "sort": "zdf,desc",
        "page": "1,20000",
        "dt": "1580914040623",
        "atfc": "",
        "onlySale": "0",
    }
    res = requests.get(url, params = params, headers = headers)
    text_data = res.text
    data_json = demjson.decode(text_data.strip("var db="))
    show_day = data_json["showday"]

    columns = [
        "fund_id",
        "fund_name",
        "-",
        f"{show_day[0]}-单位净值",
        f"{show_day[0]}-累计净值",
        f"{show_day[1]}-单位净值",
        f"{show_day[1]}-累计净值",
        "日增长值",
        "日增长率",
        "bid_stat",
        "ask_stat",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "fee_rate",
        "-",
        "-",
        "-",
    ]
    temp_df = pd.DataFrame(data_json["datas"], columns = columns)

    # remove fee_rate % sign
    def remove_perc(x):
        try:
            x = float(x.strip('%'))
        except:
            x = np.nan
        return x

    temp_df["fee_rate"] = temp_df["fee_rate"].apply(remove_perc)

    return temp_df[["fund_id","fund_name","fee_rate"]]


if __name__ == '__main__':
    # fund_id = "481001"
    # df = getFundMergedHist(fund_id)
    # print(df)
    x = getAllFundInfo()

    print(x["fee_rate"])