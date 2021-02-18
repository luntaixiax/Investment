from chinese_calendar import is_workday, is_holiday
import datetime
import pandas as pd
from typing import Generator

class InvCalendar():
    @ classmethod
    def date_generator(cls, start_date: datetime.date, forward : bool = True) -> Generator[datetime.date, None, None]:
        for i in range(10000):
            start_date = start_date + datetime.timedelta(days = 1) if forward else start_date - datetime.timedelta(days = 1)
            yield start_date

    @ classmethod
    def is_trade_date(cls, query_date : datetime.date) -> bool:
        return is_workday(query_date) and query_date.weekday() < 5 and not is_holiday(query_date)

    @ classmethod
    def next_trade_date(cls, base_date : datetime.date) -> datetime.date:
        for dt in cls.date_generator(base_date):
            if cls.is_trade_date(dt):
                return dt

    @ classmethod
    def previous_trade_date(cls, base_date : datetime.date) -> datetime.date:
        for dt in cls.date_generator(base_date, forward = False):
            if cls.is_trade_date(dt):
                return dt

    @ classmethod
    def get_effect_date(cls, trade_time : datetime.datetime, close_hour : int = 15) -> datetime.date:
        '''
        calculate the effective trading date
        :param trade_time: 2021-06-12 12:45:06  exact trading time
        :param close_hour: when the market close, default 15:00 p.m.
        :return: the effective date
        '''
        if trade_time.hour < close_hour and cls.is_trade_date(trade_time.date()):
            return trade_time.date()
        else:
            return cls.next_trade_date(trade_time.date())

    @ classmethod
    def get_recent_trade_date(cls) -> datetime.date:
        today = datetime.date.today()
        if cls.is_trade_date(today):
            return today
        else:
            return cls.previous_trade_date(today)





if __name__ == '__main__':

    print(InvCalendar.get_recent_trade_date())