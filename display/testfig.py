import numpy as np
import pygal
import seaborn as sns
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.figure import Figure
import wx



class SimplePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        # sns.set(style="whitegrid", palette="pastel", color_codes=True)
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)

        self.planets = sns.load_dataset("planets")

        self.years = np.arange(2010, 2014)
        sns.factorplot(x="year", ax= self.ax,data=self.planets, kind="count",palette="BuPu", size=6, aspect=1.5, order=self.years)
        sns.despine(left=True)

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)


        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.toolbar, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

def testFig():
    sns.set(style = "whitegrid", palette = "pastel", color_codes = True)

    figure = Figure()
    ax = figure.add_subplot(111)

    planets = sns.load_dataset("planets")

    years = np.arange(2010, 2014)
    sns.factorplot(x = "year", ax = ax, data = planets, kind = "count", palette = "BuPu", size = 6,
                   aspect = 1.5, order = years)
    sns.despine(left = True)

    return figure






if __name__ == "__main__":
    app = wx.App(False)
    fr = wx.Frame(None, title='test', size=(800,600))
    panel = SimplePanel(fr)
    fr.Show()
    app.MainLoop()
