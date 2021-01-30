from typing import List

import wx
import wx.grid
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

from analyst.investhistory.singlefundinvest import SingleFundInvestAnalyst
from display.gui_common import MyStaticText, ScrollPanel, FmtGrid


class DisplayTextPair:
	def __init__(self, label, valuefunc, fmtfunc = lambda x: str(x)):
		self.label = label
		self.valuefunc = valuefunc
		self.fmtfunc = fmtfunc

	def getLabel(self):
		return self.label

	def getvalue(self):
		return self.valuefunc()

	def getfmtvalue(self):
		return self.fmtfunc(self.getvalue())

	def getColor(self):
		return "#384042"

class RedGreenTextPair(DisplayTextPair):
	def __init__(self, label, valuefunc, fmtfunc = lambda x: str(x)):
		super().__init__(label, valuefunc, fmtfunc)

	def getColor(self):
		if self.getvalue() > 0:
			return "#e04054"
		elif self.getvalue() < 0:
			return "#399239"
		else:
			return super().getColor()

class TextInoDisplayBoard(wx.Panel):
	def __init__(self, parent, label : str, kws : List[DisplayTextPair]):
		super().__init__(parent)

		self.kws = kws

		self.vbox = wx.BoxSizer(wx.VERTICAL)
		box = wx.StaticBox(self, label = label)
		self.vbox = wx.StaticBoxSizer(box, wx.VERTICAL)

		self.initPanel()
		self.SetSizer(self.vbox)


	def initPanel(self):
		gridsizer = wx.FlexGridSizer(rows = 5, cols = 2, hgap = 20, vgap = 5)

		for c in self.kws:
			l = c.getLabel()
			v = c.getfmtvalue()

			label = MyStaticText(self, l, fontid = "BarLabel1", forecolor = "#144875")
			value = MyStaticText(self, v, fontid = "BarLabel2", forecolor = c.getColor())

			setattr(self, l, value) # bind to panel

			hbox = wx.BoxSizer(wx.HORIZONTAL)
			hbox.Add(label, proportion = 0, flag = wx.ALIGN_LEFT)
			hbox.Add(value, proportion = 1, flag = wx.LEFT | wx.ALIGN_LEFT, border = 15)

			gridsizer.Add(hbox, proportion = 1, flag = wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, border = 2 )

		gridsizer.AddGrowableCol(0, 1)
		gridsizer.AddGrowableCol(1, 1)

		#self.vbox.Add(wx.TextCtrl(self), proportion = 0, flag = wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, border = 2)
		self.vbox.Add(gridsizer, proportion = 0, flag = wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, border = 2 )

	def update(self):
		# update values on the board
		# should be content independent -- can be reused by all kinds of text infos


		for c in self.kws:
			v = getattr(self, c.getLabel())
			v.SetLabel(c.getfmtvalue())
			v.SetForegroundColour(c.getColor())


class StatInfoPanel(wx.Panel):
	def __init__(self,parent, valuegetter):
		super().__init__(parent)


		self.valuegetter = valuegetter  # func of func to get value

		self.vbox = wx.BoxSizer(wx.VERTICAL)

		self.initPanel()
		self.SetSizer(self.vbox)

	def initPanel(self):


		kw1 = [
			DisplayTextPair("Start Date", self.valuegetter("Start Date")),
			DisplayTextPair("End Date", self.valuegetter("End Date")),
			DisplayTextPair("Calendar Days", self.valuegetter("Calendar Days")),
			DisplayTextPair("Trading Days", self.valuegetter("Trading Days")),
		]
		self.p1 = TextInoDisplayBoard(self, "Investment Horizon", kw1)

		kw2 = [
			DisplayTextPair("Last Price", self.valuegetter('Last Price'), lambda v: f"{v:.4f}"),
			DisplayTextPair("Average Cost", self.valuegetter('Average Cost'), lambda v: f"{v:.4f}"),
			DisplayTextPair("Shares Outstanding", self.valuegetter('Shares Outstanding'), lambda v: f"{v:.2f}"),
			DisplayTextPair("Adj. Shares Bought", self.valuegetter('Shares Outstanding'), lambda v: f"{v:.2f}"),
		]
		self.p2 = TextInoDisplayBoard(self, "Position Info", kw2)

		kw3 = [
			DisplayTextPair("Total Invest", self.valuegetter('Total Invest'), lambda v: f"{v:,.2f}"),
			DisplayTextPair("Total Withdraw", self.valuegetter('Total Withdraw'), lambda v: f"{v:,.2f}"),
			DisplayTextPair("Market Value", self.valuegetter('Market Value'), lambda v: f"{v:,.2f}"),
			RedGreenTextPair("Accum Profit", self.valuegetter('Accum Profit'), lambda v: f"{v:,.2f}"),
		]
		self.p3 = TextInoDisplayBoard(self, "Contribution and Profit", kw3)

		kw4 = [
			RedGreenTextPair("Fund Return", self.valuegetter('Fund Return'), lambda v: f"{v:.2%}"),
			RedGreenTextPair("Fund Return Ann.", self.valuegetter('Fund Return Ann.'), lambda v: f"{v:.2%}"),
			RedGreenTextPair("Invest Return", self.valuegetter('Invest Return'), lambda v: f"{v:.2%}"),
			RedGreenTextPair("Invest Return Ann.", self.valuegetter('Invest Return Ann.'), lambda v: f"{v:.2%}"),
			RedGreenTextPair("MIRR", self.valuegetter('MIRR'), lambda v: f"{v:.2%}"),
			RedGreenTextPair("MIRR Ann.", self.valuegetter('MIRR Ann.'), lambda v: f"{v:.2%}"),
		]
		self.p4 = TextInoDisplayBoard(self, "Returns", kw4)

		kw5 = [
			DisplayTextPair("Total Fee", self.valuegetter('Total Fee'), lambda v: f"{v:.2f}"),
			DisplayTextPair("Fee Rate", self.valuegetter('Fee Rate'), lambda v: f"{v:.2%}"),
			DisplayTextPair("Total Dividend", self.valuegetter('Total Dividend'), lambda v: f"{v:.2f}"),
		]
		self.p5 = TextInoDisplayBoard(self, "Fees and Div", kw5)

		self.vbox.Add(self.p1, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(self.p2, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(self.p3, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(self.p4, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.vbox.Add(self.p5, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)

	def update(self):
		self.p1.update()
		self.p2.update()
		self.p3.update()
		self.p4.update()



class FigurePanel(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent)

		self.figids = []

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self.sizer)
		self.Fit()

	def addFig(self, figgetter, figid, toolbar = True):
		self.figids.append(figid)
		fig = figgetter()
		setattr(self, f"F_{figid}", fig)
		setattr(self, f"FG_{figid}", figgetter)

		canvas = FigureCanvas(self, -1, fig)
		setattr(self, f"C_{figid}", canvas)

		if toolbar:
			toolbar = NavigationToolbar(canvas)

			# choice = wx.Choice(toolbar, -1, choices = ["A", "B", "C"])
			# toolbar.AddControl(choice, label = "Choose Range")
			# toolbar.Realize()

			setattr(self, f"TB_{figid}", toolbar)

			self.sizer.Add(toolbar, 0, wx.LEFT | wx.TOP | wx.GROW)

		self.sizer.Add(canvas, 1, wx.LEFT | wx.TOP)

	def update(self):
		for figid in self.figids:
			fig = getattr(self, f"F_{figid}")
			figgetter = getattr(self, f"FG_{figid}")

			fig.clear()
			fig = figgetter()

			setattr(self, f"F_{figid}", fig)

			canvas = getattr(self, f"C_{figid}")
			canvas.draw()





class PeriodStatPanel(wx.Notebook):
	def __init__(self, parent, sfia, separate = True, sep_i = 0):
		super().__init__(parent)

		self.sfia = sfia  # data and figure accessor

		# add info page
		valuegetter = lambda col: (lambda: self.sfia.get_current_stat(separate = separate, sep_i = sep_i).get(col))
		infopage = StatInfoPanel(self, valuegetter)
		self.AddPage(infopage, "Info Statistics")


		# add figure page 1
		figgetter = lambda : self.sfia.plot_return_curve(separate = separate, sep_i = sep_i)
		figpage1 = FigurePanel(self)
		figpage1.addFig(figgetter, figid = 1)
		self.AddPage(figpage1, "Accumulative Return")

		# add figure page 2
		figgetter = lambda : self.sfia.plot_gain_bar(separate = separate, sep_i = sep_i)
		figpage2 = FigurePanel(self)
		figpage2.addFig(figgetter, figid = 1)
		self.AddPage(figpage2, "Gain/Loss")

		# add trade hist for total invest
		if separate is False:
			figgetter = lambda : self.sfia.plot_operation(length_yr = 1)
			figpage3 = FigurePanel(self)
			figpage3.addFig(figgetter, figid = 1)
			self.AddPage(figpage3, "Trades")

		# add test grid
		sp = ScrollPanel(self)

		grid = FmtGrid(
			sp ,
		    fmt_dict = {
				"Net Value" : lambda v: f"{v:.4f}",
				"Avg Cost" : lambda v: f"{v:.4f}",
				"Gain/Loss" : lambda v: f"{v:.2f}",
				"HPR" : lambda v: f"{v:.2%}",
				"Accum Mark. R" : lambda v: f"{v:.2%}",
				"Accum Inv. R" : lambda v: f"{v:.2%}",
			},
			color_dict = {
				"Gain/Loss" : lambda v: "#e04054" if v >= 0 else "#399239",
				"HPR" : lambda v: "#e04054" if v >= 0 else "#399239",
			}
		)

		df = self.sfia.get_invest_stat(separate = separate, sep_i = sep_i)[["net_value", "AvgCost", "Gt", "HPR", "MarketReturnAccum", "InvestorReturnAccum"]].sort_index(ascending = False)
		df.columns = ["Net Value", "Avg Cost", "Gain/Loss", "HPR", "Accum Mark. R", "Accum Inv. R"]
		grid.set(df)

		sp.addSubPanel(grid)


		self.AddPage(sp, "TestGridScrolled")



class FundStatGui(wx.Frame):
	def __init__(self,parent,title,size, fund_id):
		super().__init__(parent,title = title,size = size)
		self.SetSizeHints(size, size)
		self.Center()

		self.sfia = SingleFundInvestAnalyst(fund_id)

		self.vbox = wx.BoxSizer(wx.VERTICAL)

		self.initPanel()
		self.SetSizer(self.vbox)

	def initPanel(self):
		self.nb = wx.Notebook(self)

		# add total stat page
		maintab = PeriodStatPanel(self.nb, self.sfia, separate = False)
		self.nb.AddPage(maintab, "Total Stat")

		# Create the sub stat tabs
		num_periods = self.sfia.get_num_subtrade()
		for period in range(num_periods):
			tabname = "Sub Stat %d" % (period + 1)
			subtab = PeriodStatPanel(self.nb, self.sfia, separate = True, sep_i = period)
			self.nb.AddPage(subtab, tabname)


		self.vbox.Add(self.nb, 1, wx.EXPAND)



if __name__ == '__main__':

	app = wx.App()
	login = FundStatGui(None,title = "StatHist", size = (600,600), fund_id = "160222")
	login.Show()
	app.MainLoop()