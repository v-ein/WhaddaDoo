# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
import wx

class CollapseButton(wx.StaticText):

    buddy: wx.Window = None
    caption: str = ""

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.caption = self.LabelText

        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)

    def SetBuddy(self, buddy: wx.Window):
        self.buddy = buddy
        self.SetLabel(self.caption)

    def OnMouseUp(self, event):
        # Reversing the expanded state
        self.Expand(not self.buddy.IsShown())
        event.Skip()
        
    def SetLabel(self, label, expanded=None):
        if expanded is None:
            expanded = self.buddy.IsShown()
        self.caption = label
        super().SetLabel(("\u25BC " if expanded else "\u25B6 ") + label)

    def Expand(self, expand=True):
        self.buddy.Show(expand)
        self.SetLabel(self.caption, expand)
        self.buddy.ContainingSizer.Layout()
