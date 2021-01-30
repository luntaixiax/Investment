import datetime

import pandas as pd
import numpy as np
from typing import Union, List, Generator

from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

from dataUtils.dataApis.funds.fundhist import FundDataManager
from dataUtils.dataApis.trading.tradingbook import TradingDataManager


class SingleFundInvestAnalyst:
    def __init__(self, fund_id : str):
        self.fund_id = fund_id
        self.tdm = TradingDataManager()
        self.fdm = FundDataManager()
        self.update()


    def summarize_trade(self) -> pd.DataFrame:
        """generate a historical investment performance table

        :return: a table of investment performance:

        columns = ["fund_id", "net_value", "div",  "split_ratio", "daily_return", "Qt", "Qbt", "MVt", "Gt", "At", "CFt", "Dt"]
        index = t = date

        known Variable from historical fund data:
            p(t) - net value or price per share at the end of date t = net_value
            d(t) - dividend per share on date t = div
            s(t) - split ration on date t = split_ratio
            g(t) - profit/loss per share on date t = pnl
            r(t) - return on date t

        Variables in summary table:
            Qb(t) - number of shares buy/sell at the end of day t: determined by trading data
            A(t) - transaction cost/tax paid for buy/sell positions on day t: determined by trading data
            Q(t) - number of shares at the end of day t:   Q(t) = Q(t-1) * s(t) + Qb(t);  Q(0) = 0
            MV(t) - market value of the position on day t:   MV(t) = p(t) * Q(t)
            G(t) - gain/loss of the position on day t:   G(t) = [MV(t) + C(t)] - [MV(t-1) + C(t-1)] + A(t)= g(t) * Q(t-1)
            C(t) - virtual cash balance at the end of day t:  CF(t) = C(t-1) + D(t) - p(t) * Qb(t) - A(t);  C(0) = 0
            CF(t) - cash flow on day t: CF(t) = C(t) - C(t-1) = D(t) - p(t) * Qb(t) - A(t); CF(t) > 0 is inflow otherwise is outflow
            D(t) - cash dividend received for the position on day t: D(t) = d(t) * Q(t-1)
        """

        # save results to summary
        summary = pd.DataFrame(columns = ["date", "fund_id", "net_value", "div",  "split_ratio", "daily_return", "Qt", "Qbt", "MVt", "Gt", "At", "CFt", "Dt"]).set_index("date")

        # first search trade book about relevant trades
        trade_df = self.tdm.query_trade(self.fund_id)
        # reverse sell amount to negative number
        trade_df.loc[trade_df["event"] == "buy", "real_amount"] = trade_df.loc[trade_df["event"] == "buy", "amount"]
        trade_df.loc[trade_df["event"] == "sell", "real_amount"] = -trade_df.loc[trade_df["event"] == "sell", "amount"]

        # then get price/div/split data
        start_dt = trade_df["effect_date"].min()  # the start date should be the min trading date


        hist_df = self.fdm.query_hist(self.fund_id, start_dt = start_dt)

        # start analysis
        Qt = 0  # initial quantity Q(0) = 0
        #Ct = 0  # initial cash balance C(0) = 0
        for index, hist in hist_df.iterrows():
            t = hist.get("date")  # time t
            pt = hist.get("net_value")  # net value or price at time t = p(t)
            st = hist.get("split_ratio")  # split ratio at time t = s(t)
            gt = hist.get("pnl")  # gain/loss per share at time t = g(t)
            dt = hist.get("div")  # dividend per share at time t = d(t)
            rt = hist.get("daily_return")  # daily return at day t

            Gt = gt * Qt  # position gain G(t) = [MV(t) + C(t)] - [MV(t-1) + C(t-1)] + A(t)= g(t) * Q(t-1)
            Dt = dt * Qt  # position dividend D(t) = d(t) * Q(t-1)

            if t in trade_df["effect_date"].values:
                dd = trade_df[trade_df["effect_date"] == t][["real_amount", "cost"]].sum()
                Qbt = dd["real_amount"]  # quant variation at t due to buy+/sell- = Qb(t)
                At = dd["cost"]  # cost(transaction cost at time t) = A(t)
            else:
                Qbt = 0
                At = 0

            Qt = Qt * st + Qbt

            if abs(Qt) < 1:
                # rounding error, ignore
                Qt = 0

            MVt = pt * Qt # market value of the position = p(t) * Q(t)
            #Ct = Ct + Dt - pt * Qbt - At # cash balance at time t C(t) = C(t-1) + D(t) - p(t) * Qb(t) - A(t)
            CFt = Dt - pt * Qbt - At  # cash flow at time t CF(t) = D(t) - p(t) * Qb(t) - A(t)

            # write into summary
            summary.loc[t, ["fund_id", "net_value", "div",  "split_ratio", "daily_return", "Qt", "Qbt", "MVt", "Gt", "At", "CFt", "Dt"]] = [self.fund_id, pt, dt, st, rt, Qt, Qbt, MVt, Gt, At, CFt, Dt]

        return summary


    def split_trade_summary(self, thres_amount : float = 1, thres_idle_interval : int = 10) -> Generator[pd.DataFrame, None, None]:
        """Split the whole trading history into different investment periods for the fund

        :param thres_amount: the threshold number of shares Q^, if Q(t) < Q^, will treat as if the position is closed (idle day),
                Q(t) below the threshold regard as rounding error
        :param thres_idle_interval: threshold number of periods T, split the trade only if the interval of the consecutive idle periods (Q(t) < Q^)
                is longer than T, i.e., avoid splitting high-freq trading (frequent closing position)
        :return: list of sub-summary tables
        """

        for start_dt ,end_dt in cut(self.fund_summ.index, self.fund_summ["Qt"].values, thres_amount, thres_idle_interval):
            yield self.fund_summ.loc[start_dt : end_dt, :]

    def stat_subtrade(self, subtrade_summary : pd.DataFrame) -> pd.DataFrame:
        subtrade_summary = subtrade_summary.copy()  # prevent error

        # update values
        accum_invest = 0
        accum_withdraw = 0
        MV = 0
        TWR = 0  # accumulative fund return
        adj_buyQuant = 0

        for i, date in enumerate(subtrade_summary.index):
            sr, rt, Q_b, gain, cost, CFt = subtrade_summary.loc[date, ["split_ratio", "daily_return", "Qbt", "Gt", "At", "CFt"]]

            adj_buyQuant = sr * adj_buyQuant + max(Q_b, 0)

            if i == 0:
                rt = 0

            HPR = rt / 100 if MV == 0 else (gain - cost) / MV  # one-day holding period return, equals fund return adjusted for transaction cost

            # update MV to current day value
            MV = subtrade_summary.loc[date, "MVt"]

            accum_invest = accum_invest - min(CFt, 0)
            accum_withdraw = accum_withdraw + max(CFt, 0)
            accum_profit = MV + accum_withdraw - accum_invest
            avg_cost = accum_invest / adj_buyQuant
            accounting_r = accum_profit / accum_invest  # accumulative accounting profit margin
            TWR = (1 + TWR) * (1 + np.nan_to_num(HPR)) - 1


            # make record to the table
            subtrade_summary.loc[date, "BuyQuant"] = adj_buyQuant
            subtrade_summary.loc[date, "InvestAccum"] = accum_invest
            subtrade_summary.loc[date, "WithdrawAccum"] = accum_withdraw
            subtrade_summary.loc[date, "AvgCost"] = avg_cost
            subtrade_summary.loc[date, "HPR"] = HPR
            subtrade_summary.loc[date, "MarketReturnAccum"] = TWR
            subtrade_summary.loc[date, "InvestorReturnAccum"] = accounting_r

        return subtrade_summary


    def calc_current_stat(self, subtrade_summary : pd.DataFrame) -> dict:

        start_dt = subtrade_summary.index.min()
        end_dt = subtrade_summary.index.max()

        trading_days = len(subtrade_summary)
        invest_period = (end_dt - start_dt).days
        n_shares, last_price, adj_buyQuant, MV = subtrade_summary.loc[end_dt, ["Qt", "net_value", "BuyQuant", "MVt"]]
        avg_cost, TWR, accounting_r = subtrade_summary.loc[end_dt, ["AvgCost", "MarketReturnAccum", "InvestorReturnAccum"]]
        accum_invest, accum_withdraw = subtrade_summary.loc[end_dt, ["InvestAccum", "WithdrawAccum"]]

        accum_profit = MV + accum_withdraw - accum_invest
        accounting_r_ann = np.log(1 + accounting_r) * 365 / invest_period
        TWR_ann = np.log(1 + subtrade_summary["HPR"]).sum() * 365 / invest_period

        # when calculating MIRR, should adjust last CF as if we sell all the position out
        # the last CF should be increase by MV
        CFs = subtrade_summary["CFt"].values
        CFs[-1] += MV
        mirr, mirr_ann = MIRR(subtrade_summary.index, CFs)

        # add transaction cost and dividend analysis
        total_div = subtrade_summary["Dt"].sum()
        total_trans = subtrade_summary["At"].sum()
        trans_rate = total_trans / (accum_withdraw + accum_invest - total_div - total_trans)

        # if accounting_r > TWR:  investor's operation has positive value: beat the fund through buy/sell

        return {
            "Start Date" : start_dt,
            "End Date" : end_dt,
            "Calendar Days" : invest_period,
            "Trading Days" : trading_days,
            "Shares Outstanding" : n_shares,
            "Adj. Shares Bought" : adj_buyQuant,
            "Total Invest" : accum_invest,
            "Total Withdraw" : accum_withdraw,
            "Market Value": MV,
            "Last Price" : last_price,
            "Average Cost" : avg_cost,
            "Accum Profit" : accum_profit,
            "Fund Return" : TWR,
            "Invest Return" : accounting_r,
            "Fund Return Ann." : TWR_ann,
            "Invest Return Ann." : accounting_r_ann,
            "MIRR" : mirr,
            "MIRR Ann." : mirr_ann,
            "Total Dividend" : total_div,
            "Total Fee" : total_trans,
            "Fee Rate" : trans_rate,
        }

    def plot_return_curve(self, separate = False, sep_i = 0):
        subtrade_summary = self.get_invest_stat(separate, sep_i)

        sns.set(style = "whitegrid", color_codes = True, font_scale = 0.8)


        figure = plt.figure()
        ax = figure.add_subplot(111)

        ax.plot(subtrade_summary.index, subtrade_summary["InvestorReturnAccum"], label = "InvestorReturnAccum")
        ax.plot(subtrade_summary.index, subtrade_summary["MarketReturnAccum"], label = "MarketReturnAccum")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax = 1, decimals = 2))
        plt.xticks(rotation = 30)

        plt.legend()

        return figure

    def plot_gain_bar(self, separate = False, sep_i = 0):
        subtrade_summary = self.get_invest_stat(separate, sep_i)
        colors = subtrade_summary["Gt"].apply(lambda x: "#e04054" if x > 0 else "#399239")
        maxdate = subtrade_summary.index.max()
        mindate = max(subtrade_summary.index.min(), maxdate - datetime.timedelta(days = 10))
        min_v_frame = subtrade_summary.loc[mindate : maxdate, "Gt"].min()
        max_v_frame = subtrade_summary.loc[mindate: maxdate, "Gt"].max()

        figure = plt.figure()
        ax = figure.add_subplot(111)

        ax.bar(subtrade_summary.index, subtrade_summary["Gt"], color = colors)
        for i, (d, v) in enumerate(zip(subtrade_summary.index, subtrade_summary["Gt"])):
            y_offset = (max_v_frame - min_v_frame) * (0.03 if v > 0 else -0.03)
            ax.text(d, v + y_offset , f"{v:,.2f}",  color = colors[i], horizontalalignment='center', verticalalignment='center')

        ax.set_xlim([mindate, maxdate])
        ax.set_ylim([min(1.2 * min_v_frame, - min_v_frame), max(1.2 * max_v_frame, - max_v_frame)])
        plt.xticks(rotation = 30)

        return figure

    def plot_operation(self, length_yr : int = 1):
        start_dt = datetime.date.today() - datetime.timedelta(days = length_yr * 365)
        # plot buy/sell transactions on fund accumulative return curve, given timeframe
        df = self.fdm.query_hist(self.fund_id, start_dt = start_dt)
        df = df.set_index("date")[["net_value", "full_value", "daily_return"]]
        df["accum_return"] = np.exp(np.log(df["daily_return"] / 100 + 1).cumsum()) - 1

        # search for buy/sell history
        df_trade = self.tdm.query_trade_aggday(fund_id = self.fund_id, start_dt = start_dt).set_index("effect_date")
        df_trade.loc[df_trade["event"] == "buy", "cf"] = df_trade.loc[df_trade["event"] == "buy", "value"]
        df_trade.loc[df_trade["event"] == "sell", "cf"] = -df_trade.loc[df_trade["event"] == "sell", "value"]
        df_trade["accum_return"] = df.loc[df_trade.index, "accum_return"]
        df_trade["color"] = df_trade["event"].apply(lambda x : "#e04054" if x == "buy" else "#399239")

        sns.set(style = "whitegrid", color_codes = True, font_scale = 0.8)

        figure = plt.figure()
        ax = figure.add_subplot(111)

        ax.plot(df.index, df["accum_return"], color = "#5c6263", label = "Accum Return")
        ax.fill_between(df.index, np.zeros(len(df.index)), df["accum_return"], color='#8fafb4', alpha=0.3)
        ax.scatter(df_trade.index, df_trade["accum_return"], c = df_trade["color"], s = 20, alpha = 1)

        for date in df_trade.index:
            ax.annotate("", xy = (date, df_trade.loc[date, "accum_return"]),
                        xytext = (date, df_trade.loc[date, "accum_return"] - 0.4 * df_trade.loc[date, "cf"] / df_trade["cf"].abs().max()),
                        va = "center", ha = "center",
                        arrowprops = dict(arrowstyle = "<-", color = df_trade.loc[date, "color"]))

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax = 1, decimals = 2))

        plt.legend()

        return figure


    def update(self) -> None:
        self.fund_summ = self.summarize_trade()

        self.invest_stat = {
            "Combined" : self.stat_subtrade(self.fund_summ),
            "Separated" : [self.stat_subtrade(summ) for summ in self.split_trade_summary()]
        }

        self.current_stat = {
            "Combined": self.calc_current_stat(self.invest_stat["Combined"]),
            "Separated": [self.calc_current_stat(summ) for summ in self.invest_stat["Separated"]]
        }


    def get_num_subtrade(self):
        # number of sub periods
        return len(self.invest_stat["Separated"])

    def get_current_stat(self, separate = False, sep_i = 0):
        if separate:
            return self.current_stat["Separated"][sep_i]
        else:
            return self.current_stat["Combined"]

    def get_invest_stat(self, separate = False, sep_i = 0):
        if separate:
            return self.invest_stat["Separated"][sep_i]
        else:
            return self.invest_stat["Combined"]



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







if __name__ == '__main__':
    sfia = SingleFundInvestAnalyst(fund_id = "160222")
    #print(sfia.invest_stat["Separated"][0].to_csv("sub.csv"))
    sfia.plot_operation(1)