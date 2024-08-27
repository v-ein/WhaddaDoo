# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
from typing import List, Optional
import wx

class CollapseButton(wx.StaticText):

    buddies: List[wx.Window]
    caption: str = ""

    def __init__(self, *arg, **kw) -> None:
        super().__init__(*arg, **kw)
        self.buddies = []
        self.caption = self.GetLabelText()

        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocusEvent)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusEvent)

    def SetBuddy(self, *buddy: wx.Window) -> None:
        self.buddies = list(buddy)
        self.SetLabel(self.caption)

    def OnMouseUp(self, event: wx.Event) -> None:
        # Reversing the expanded state
        self.Expand(not self.buddies[0].IsShown())
        event.Skip()
        
    def SetLabel(self, label: str, expanded: Optional[bool] = None) -> None:
        if expanded is None:
            expanded = self.buddies[0].IsShown()
        self.caption = label
        super().SetLabel(("\u25BC " if expanded else "\u25B6 ") + label)

    def Expand(self, expand: bool = True) -> None:
        for buddy in self.buddies:
            buddy.Show(expand)
        self.SetLabel(self.caption, expand)
        # TODO: avoid calling Layout() twice on the same sizer. Better collect
        # a set of sizers to refresh in the previous for loop.
        for buddy in self.buddies:
            buddy.GetContainingSizer().Layout()

    def AcceptsFocus(self) -> bool:
        return True

    def OnFocusEvent(self, event: wx.Event) -> None:
        self.Refresh()
        event.Skip()        

    def OnPaint(self, event: wx.Event) -> None:
        dc = wx.PaintDC(self)
        renderer = wx.RendererNative.Get()
        rect = self.GetClientRect()

        # Set up colors
        back_col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        text_col = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)
        dc.SetBrush(wx.Brush(back_col))
        dc.SetTextBackground(back_col)
        dc.SetTextForeground(text_col)

        # Erase the entire background area in case the text label is smaller
        # than the control itself.
        dc.SetPen(wx.TRANSPARENT_PEN)       # type: ignore[attr-defined]    # wx.TRANSPARENT_PEN is defined in wx/core.py
        dc.DrawRectangle(rect)

        # Now draw the label itself and its focus
        dc.DrawText(self.GetLabelText(), 0, 0)
        if self.HasFocus():
            renderer.DrawFocusRect(self, dc, rect)

    def OnKeyDown(self, event: wx.Event) -> None:
        assert isinstance(event, wx.KeyEvent)   # for mypy
        # TODO: neither left/right nor Enter actually work. Fix this.
        if event.KeyCode == wx.WXK_LEFT or event.KeyCode == wx.WXK_RIGHT:
            self.Expand(event.KeyCode == wx.WXK_RIGHT)
        elif event.KeyCode == wx.WXK_RETURN or event.KeyCode == wx.WXK_SPACE:
            self.Expand(not self.buddies[0].IsShown())
        event.Skip()
