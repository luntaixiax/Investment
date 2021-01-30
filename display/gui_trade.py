import datetime

import wx
import pandas as pd
from typing import Callable, Tuple

from wx.adv import CalendarCtrl, TimePickerCtrl

from dataUtils.dataApis.funds.fundinfo import FundInfoManager
from dataUtils.dataApis.trading.tradingbook import TradingDataManager
from display.gui_common import SearchableComboBox, MyStaticText, StyledBtn


def search_func(key_word : str) -> Tuple[list,list]:
	"""
	a search function
	:param key_word:
	:return: choicelist, valuelist
	"""
	r = FundInfoManager.blur_query(key_word).head(400)
	if r is None:
		return [], []

	return [f"{record.get('fund_id')} - {record.get('fund_name')}" for i, record in r.iterrows()], r["fund_id"].values



class TradeRecordFrame(wx.Frame):
	def __init__(self,parent,title,size):
		super().__init__(parent,title = title,size = size)
		self.SetSizeHints(size, size)
		self.Center()

		self.tdm = TradingDataManager()

		self.SetBackgroundColour('#f7f7f7')
		#self.p = wx.Panel(self, -1)

		self.vbox = wx.BoxSizer(wx.VERTICAL)

		self.initPanel()
		self.SetSizer(self.vbox)

	def initPanel(self):

		self.fund_choice = SearchableComboBox(self, -1, choices = [], search_func = search_func)

		choice_box = wx.StaticBox(self, label = "Select Fund Id")
		choice_box = wx.StaticBoxSizer(choice_box, wx.VERTICAL)
		choice_box.Add(self.fund_choice, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 5)

		# add calendar and time
		self.calendar = CalendarCtrl(self, -1)
		self.clock = TimePickerCtrl(self, -1)

		date_box = wx.StaticBox(self, label = "Trading Date and Time")
		date_box = wx.StaticBoxSizer(date_box, wx.VERTICAL)
		date_box.Add(self.calendar, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 5)
		date_box.Add(self.clock, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 5)

		# add value and cost and direction
		self.value = wx.TextCtrl(self, -1)
		self.cost = wx.TextCtrl(self, -1)
		self.direction = wx.Choice(self, -1, choices = ["Buy", "Sell"])
		self.price = MyStaticText(self, "--", fontid = "BarLabel1")
		self.quant = MyStaticText(self, "--", fontid = "BarLabel1")
		self.netvalue = MyStaticText(self, "--", fontid = "BarLabel1")

		info_box = wx.FlexGridSizer(6,2,5,5)
		info_box.AddMany([
			(MyStaticText(self, "Total Cash Paid/Recv", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.value, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(MyStaticText(self, "Transaction Cost", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.cost, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(MyStaticText(self, "Direction", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.direction, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(MyStaticText(self, "Price", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.price, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(MyStaticText(self, "Quant", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.quant, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(MyStaticText(self, "Net Value", fontid = "BarLabel1"), 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
			(self.netvalue, 15, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND),
		])

		info_box.AddGrowableCol(0, 1)
		info_box.AddGrowableCol(1, 2)

		# add buttons
		search_btn = StyledBtn(self, "Seach Price", bgcolor = "#eed14a")
		search_btn.Bind(wx.EVT_BUTTON, self.OnSearch)
		save_btn = StyledBtn(self, "Save", bgcolor = "#61a1fa")
		save_btn.Bind(wx.EVT_BUTTON, self.OnSave)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(search_btn, proportion = 1, flag = wx.ALL | wx.EXPAND, border = 0)
		hbox.Add(save_btn, proportion = 1, flag = wx.ALL | wx.EXPAND, border = 0)



		self.vbox.Add(choice_box, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(date_box, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(info_box, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 10)
		self.vbox.Add(hbox, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 10)


	def OnSearch(self, evt):
		fund_id = self.fund_choice.GetSelectionString()
		date = self.calendar.GetDate()
		time = self.clock.GetTime()

		dt = datetime.datetime(date.GetYear(), date.GetMonth() + 1, date.GetDay(), time[0], time[1], time[2])
		dtt = self.tdm.get_effective_date(dt)

		price = self.tdm.get_price(fund_id, dtt)
		cash = float(self.value.GetValue())
		cost = float(self.cost.GetValue())

		value = cash - cost if self.direction.GetSelection() == 0 else cash + cost

		quant = value / price

		self.price.SetLabel(f"{price:.4f}")
		self.quant.SetLabel(f"{quant:.2f}")
		self.netvalue.SetLabel(f"{value:.2f}")


	def OnSave(self, evt):
		fund_id = self.fund_choice.GetSelectionString()
		date = self.calendar.GetDate()
		time = self.clock.GetTime()
		dt = datetime.datetime(date.GetYear(), date.GetMonth() + 1, date.GetDay(), time[0], time[1], time[2])
		cash = float(self.value.GetValue())
		cost = float(self.cost.GetValue())
		direction = self.direction.GetSelection()

		if direction == 0:
			value = cash - cost
			self.tdm.buy(fund_id, trade_datetime = dt, value = value, cost = cost)
		elif direction == 1:
			value = cash + cost
			self.tdm.sell(fund_id, trade_datetime = dt, value = value, cost = cost)




if __name__ == '__main__':
	app = wx.App()
	login = TradeRecordFrame(None, title = "Make Records", size = (300,580))
	login.Show()
	app.MainLoop()