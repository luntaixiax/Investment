import wx
import wx.lib.scrolledpanel
import wx.grid
from typing import Callable, Tuple

fonts = {
	"BarLabel1" : {
			"pointSize" : 12,
			"family" : wx.DECORATIVE,
			"style" : wx.NORMAL,
			"weight" : wx.NORMAL,
			"underline" : False,
			"faceName" : "Calibri",
	},
	"BarLabel2": {
		"pointSize": 12,
		"family": wx.DECORATIVE,
		"style": wx.NORMAL,
		"weight": wx.NORMAL,
		"underline": False,
		"faceName": "Calibri",
	}
}


class MyStaticText(wx.StaticText):
	def __init__(self, parent, text, fontid, forecolor = None, backcolor = None):
		super().__init__(parent, -1, text)

		params = fonts.get(fontid)
		font = wx.Font(params.get("pointSize"), params.get("family"), params.get("style"), params.get("weight"),
	               params.get("underline"), params.get("faceName"))

		self.SetFont(font)

		if forecolor:
			self.SetForegroundColour(forecolor)
		if backcolor:
			self.SetBackgroundColour(backcolor)

class SearchableComboBox(wx.ComboBox):
	def __init__(self, parent, id, choices : list, search_func : Callable[[str], Tuple[list,list]]):
		super().__init__(parent, id = id, value = "", choices = choices, style = wx.TE_PROCESS_ENTER)

		self.search_func = search_func
		self.selections = None

		self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)


	def OnSearch(self, evt):
		s = self.GetValue()
		self.selections = self.search_func(s)
		self.SetItems(self.selections[0])
		self.Popup()


	def GetSelectionString(self):
		return self.selections[1][self.GetSelection()]

class StyledBtn(wx.Button):
	def __init__(self, parent, label, size = (60,30), color = "#000000", bgcolor = "#FFFFFF"):
		super().__init__(parent, label = label, size = size)
		self.setColor(color, bgcolor)

	def setColor(self, color = "#000000", bgcolor = "#FFFFFF"):
		if color:
			self.SetForegroundColour(color)
		if bgcolor:
			self.SetBackgroundColour(bgcolor)

class FmtGrid(wx.grid.Grid):
	def __init__(self, parent, fmt_dict : dict, color_dict : dict):
		super().__init__(parent)

		self.fmt_dict = fmt_dict
		self.color_dict = color_dict

	def set(self, df):
		row, col = df.shape
		self.CreateGrid(row, col)

		for i, r in enumerate(df.index):
			self.SetRowLabelValue(i, str(r))

		for j, c in enumerate(df.columns):
			self.SetColLabelValue(j, c)
			fmtter = self.fmt_dict.get(c)
			colorer = self.color_dict.get(c)
			for i, r in enumerate(df.index):
				value = df.loc[r, c]
				if colorer:
					color = colorer(value)
					self.SetCellTextColour(i, j, color)
				if fmtter:
					value = fmtter(value)
				self.SetCellValue(i, j, str(value))

		self.SetRowLabelSize(100)
		self.Fit()
		self.Layout()


class ScrollPanel(wx.ScrolledWindow):
	def __init__(self, parent):
		super().__init__(parent)

		self.SetScrollbars(0, 1, 0, 20)

		self.vbox = wx.BoxSizer(wx.VERTICAL)

		self.SetSizer(self.vbox)

	def addSubPanel(self, panel):
		self.vbox.Add(panel, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 0)
		self.Fit()
		self.Layout()

