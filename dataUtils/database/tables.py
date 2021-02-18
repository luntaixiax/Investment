from sqlalchemy.ext.declarative import declarative_base, as_declarative
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Numeric, DECIMAL, inspect, INT

Base = declarative_base()


class MutualFundHist(Base):
    __tablename__ = "mutualfundhist"

    fund_id = Column(String(length = 10), primary_key = True, nullable = False)
    date = Column(Date, primary_key = True, nullable = False)
    net_value = Column(DECIMAL(8, 4), nullable = False)
    full_value = Column(DECIMAL(8, 4), nullable = False)
    div = Column(DECIMAL(8, 4), nullable = False, server_default = "0.0")
    split_ratio = Column(DECIMAL(12, 8), nullable = False, server_default = "1.0")
    pnl = Column(DECIMAL(8, 4), nullable = False, server_default = "0.0")
    equiv_cash = Column(DECIMAL(8, 4), nullable = False, server_default = "0.0")
    position_value = Column(DECIMAL(8, 4), nullable = False, server_default = "0.0")
    daily_return = Column(DECIMAL(8, 4), nullable = False, server_default = "0.0")



class TradeBook(Base):
    __tablename__ = "tradebook"

    fund_id = Column(String(length = 10), primary_key = True, nullable = False)
    trade_datetime = Column(DateTime, primary_key = True, nullable = False)
    effect_date = Column(Date, nullable = False)
    event = Column(String(length = 10), nullable = False)
    value = Column(DECIMAL(10, 2), nullable = False)
    price = Column(DECIMAL(8, 4), nullable = False)
    amount = Column(DECIMAL(10, 2), nullable = False)
    cost = Column(DECIMAL(10, 2), nullable = False)


class MutualFundInfo(Base):
    __tablename__ = "mutualfundinfo"

    fund_id = Column(String(length = 10), primary_key = True, nullable = False)
    fund_name = Column(String(length = 50), primary_key = False, nullable = False)
    fee_rate = Column(DECIMAL(5, 2), nullable = True)


class StockHist(Base):
    __tablename__ = "stockhist"

    stock_id = Column(String(length = 10), primary_key = True, nullable = False)
    date = Column(Date, primary_key = True, nullable = False)
    open = Column(DECIMAL(8, 2), nullable = False)
    high = Column(DECIMAL(8, 2), nullable = False)
    low = Column(DECIMAL(8, 2), nullable = False)
    close = Column(DECIMAL(8, 2), nullable = False)
    vol = Column(DECIMAL(15, 0), nullable = False)
    div = Column(DECIMAL(6, 2), nullable = False, server_default = "0.0")
    split = Column(DECIMAL(6, 4), nullable = False, server_default = "1.0")


class StockInfo(Base):
    __tablename__ = "stockinfo"

    stock_id = Column(String(length = 10), primary_key = True, nullable = False)
    ass_type = Column(String(length = 10))
    company = Column(String(length = 50))
    exch = Column(String(length = 10))
    cur = Column(String(length = 10))
    sec = Column(String(length = 10))
    ind = Column(String(length = 10))


