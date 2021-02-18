import numpy as np
import pandas as pd

from utils.const import FREQ


def cut(index_list, base_list, thres_amount : float = 1, thres_idle_interval : int = 10):
    idle = 0
    start_dt = None
    end_dt = None

    for i, (index, Qt) in enumerate(zip(index_list, base_list)):

        if abs(Qt) >= thres_amount:
            idle = 0
            if start_dt is None:
                start_dt = index

        if abs(Qt) < thres_amount:
            # suspect breaking point occur
            if idle == 0:
                end_dt = index  # the last date to be the end date

            idle += 1

            if idle > thres_idle_interval:
                if start_dt is not None and end_dt is not None:
                    yield start_dt, end_dt

                #idle = 0
                start_dt = None
                end_dt = None

    # add last period
    if start_dt is not None:
        yield start_dt, index_list[-1]


def MIRR(dates, CFs, reinvest_rate = 0.03, wacc = 0.03):
    start_dt = dates.min()
    end_dt = dates.max()
    invest_period = (end_dt - start_dt).days
    PVout = 0  # pv of cash outflows at start_dt
    FVin = 0  # fv of cash inflows at end_dt
    for date, CF in zip(dates, CFs):
        if CF < 0:
            distance = (date - start_dt).days / 365
            PVout += (CF * np.exp(- wacc * distance))
        else:
            distance = (end_dt - date).days / 365
            FVin += (CF * np.exp(reinvest_rate * distance))

    # return mirr, and annualized mirr
    return - FVin / PVout - 1, np.log(- FVin / PVout) * 365 / invest_period


def _stat(subset):
    d = {}
    MVt_b = subset['MVt'].iloc[0] + subset['CFt'].iloc[0] + subset['At'].iloc[0] - subset['Gt'].iloc[0]

    d['MVt'] = subset['MVt'].iloc[-1]
    d['Gt'] = subset['Gt'].sum()
    d['At'] = subset['At'].sum()
    d['Dt'] = subset['Dt'].sum()
    d['Invt'] = subset['Invt'].sum()
    d['Witt'] = subset['Witt'].sum()
    d['CFt'] = subset['CFt'].sum()

    denom = MVt_b + d['Invt'] + d['At']
    d['HPRt'] = (d['MVt'] + d['Witt'] + d['Dt']) / denom - 1 if denom != 0 else 0

    return pd.Series(d, index = ['MVt', 'Gt', 'At', 'Dt', 'Invt', 'Witt', 'CFt', 'HPRt'])


def period_performance(df : pd.DataFrame, freq : FREQ = FREQ.MONTH) -> pd.DataFrame:
    """Stat/Aggregate the performance by specified period

    :param df: the df to be stat, index must be date object, columns must contain 'MVt', 'Gt', 'At', 'Dt', 'Invt', 'Witt', 'CFt'
    :param freq: frequency to stat
    :return: tackled df
    """
    if not {'MVt', 'Gt', 'At', 'Dt', 'Invt', 'Witt', 'CFt'}.issubset(df.columns):
        raise IndexError("df must contain columns of 'MVt', 'Gt', 'At', 'Dt', 'Invt', 'Witt', 'CFt'")

    df.index = pd.to_datetime(df.index)
    ga = df.groupby(pd.Grouper(freq = freq.value.pd_fmt)).apply(_stat)
    ga.index = ga.index.to_period(freq.value.pd_fmt)
    return ga