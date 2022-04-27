from cmath import exp
import wx

class CollapseButton(wx.StaticText):

    buddy: wx.Window = None
    caption: str = ""

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.caption = self.GetLabelText()

        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)

    def SetBuddy(self, buddy: wx.Window):
        self.buddy = buddy
        self.SetLabel(self.caption)

    def OnMouseUp(self, event):
        expand = not self.buddy.IsShown()
        self.buddy.Show(expand)
        self.SetLabel(self.caption, expand)
        self.buddy.GetContainingSizer().Layout()
        event.Skip()
        
    def SetLabel(self, label, expanded = None):
        if expanded is None:
            expanded = self.buddy.IsShown()
        self.caption = label
        super().SetLabel(("\u25BC " if expanded else "\u25B6 ") + label)
