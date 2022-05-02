#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade
#

import wx

# begin wxGlade: dependencies
import wx.adv
import wx.grid
# end wxGlade

# begin wxGlade: extracode
from ui.comment_list import CommentList
import wx.richtext
from ui.task_list import TaskList
import ui.controls
# end wxGlade


class AppWindowBase(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: AppWindowBase.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((650, 550))
        self.SetTitle("WhaddaDoo")

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        self.tabs_boards = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_1.Add(self.tabs_boards, 1, wx.EXPAND, 0)

        self.notebook_1_pane_1 = wx.Panel(self.tabs_boards, wx.ID_ANY)
        self.tabs_boards.AddPage(self.notebook_1_pane_1, "notebook_1_pane_1")

        sizer_6 = wx.BoxSizer(wx.VERTICAL)

        self.window_1 = wx.SplitterWindow(self.notebook_1_pane_1, wx.ID_ANY, style=0)
        self.window_1.SetMinimumPaneSize(100)
        self.window_1.SetSashGravity(0.5)
        sizer_6.Add(self.window_1, 1, wx.ALL | wx.EXPAND, 8)

        self.window_1_pane_1 = wx.Panel(self.window_1, wx.ID_ANY)

        self.sizer_left_pane = wx.BoxSizer(wx.VERTICAL)

        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_left_pane.Add(sizer_7, 0, wx.EXPAND, 0)

        self.label_done = ui.controls.CollapseButton(self.window_1_pane_1, wx.ID_ANY, "Done")
        self.label_done.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_7.Add(self.label_done, 0, wx.BOTTOM, 4)

        static_line_1 = wx.StaticLine(self.window_1_pane_1, wx.ID_ANY)
        sizer_7.Add(static_line_1, 1, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.RIGHT, 4)

        self.grid_done = TaskList(self.window_1_pane_1, wx.ID_ANY, size=(1, 1))
        self.sizer_left_pane.Add(self.grid_done, 1, wx.BOTTOM | wx.EXPAND | wx.RIGHT, 4)

        sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_left_pane.Add(sizer_8, 0, wx.EXPAND, 8)

        self.label_active = ui.controls.CollapseButton(self.window_1_pane_1, wx.ID_ANY, "Active")
        self.label_active.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Segoe UI"))
        sizer_8.Add(self.label_active, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.TOP, 4)

        static_line_2 = wx.StaticLine(self.window_1_pane_1, wx.ID_ANY)
        sizer_8.Add(static_line_2, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.btn_new_task = wx.Button(self.window_1_pane_1, wx.ID_ANY, "&New task")
        sizer_8.Add(self.btn_new_task, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        self.grid_tasks = TaskList(self.window_1_pane_1, wx.ID_ANY, size=(1, 1))
        self.sizer_left_pane.Add(self.grid_tasks, 2, wx.EXPAND | wx.RIGHT | wx.TOP, 4)

        self.window_1_pane_2 = wx.Panel(self.window_1, wx.ID_ANY)

        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)

        self.panel_2 = wx.ScrolledWindow(self.window_1_pane_2, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        self.panel_2.SetScrollRate(10, 10)
        sizer_4.Add(self.panel_2, 1, wx.EXPAND | wx.LEFT, 4)

        self.sizer_right_pane = wx.BoxSizer(wx.VERTICAL)

        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_right_pane.Add(sizer_9, 0, wx.EXPAND, 0)

        sizer_9.Add((20, 20), 1, wx.EXPAND, 0)

        self.panel_active_workflow_buttons = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_9.Add(self.panel_active_workflow_buttons, 0, wx.EXPAND, 0)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_cancel = wx.Button(self.panel_active_workflow_buttons, wx.ID_ANY, "&Cancel task")
        sizer_2.Add(self.btn_cancel, 0, 0, 8)

        self.btn_done = wx.Button(self.panel_active_workflow_buttons, wx.ID_ANY, "&Done")
        sizer_2.Add(self.btn_done, 0, wx.LEFT, 8)

        self.panel_completed_workflow_buttons = wx.Panel(self.panel_2, wx.ID_ANY)
        sizer_9.Add(self.panel_completed_workflow_buttons, 0, wx.EXPAND, 0)

        sizer_10 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_reopen = wx.Button(self.panel_completed_workflow_buttons, wx.ID_ANY, "&Reopen")
        sizer_10.Add(self.btn_reopen, 0, 0, 0)

        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_right_pane.Add(sizer_3, 1, wx.EXPAND, 0)

        self.edit_desc = wx.richtext.RichTextCtrl(self.panel_2, wx.ID_ANY)
        sizer_3.Add(self.edit_desc, 1, wx.EXPAND | wx.TOP, 8)

        self.panel_desc_buttons = wx.Panel(self.panel_2, wx.ID_ANY)
        self.panel_desc_buttons.Hide()
        sizer_3.Add(self.panel_desc_buttons, 0, wx.EXPAND | wx.TOP, 8)

        sizer_desc_buttons = wx.BoxSizer(wx.HORIZONTAL)

        sizer_desc_buttons.Add((20, 20), 1, wx.EXPAND, 0)

        self.btn_desc_discard = wx.Button(self.panel_desc_buttons, wx.ID_ANY, "Discard")
        sizer_desc_buttons.Add(self.btn_desc_discard, 0, 0, 8)

        self.btn_desc_save = wx.Button(self.panel_desc_buttons, wx.ID_ANY, "&Save changes")
        sizer_desc_buttons.Add(self.btn_desc_save, 0, wx.LEFT, 8)

        sizer_14 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_right_pane.Add(sizer_14, 0, wx.EXPAND | wx.TOP, 8)

        label_1 = wx.StaticText(self.panel_2, wx.ID_ANY, "Created:")
        sizer_14.Add(label_1, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

        self.label_created = wx.StaticText(self.panel_2, wx.ID_ANY, "01.01.2022")
        sizer_14.Add(self.label_created, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        label_2 = wx.StaticText(self.panel_2, wx.ID_ANY, "Deadline:")
        sizer_14.Add(label_2, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

        self.date_deadline = wx.adv.DatePickerCtrl(self.panel_2, wx.ID_ANY, style=wx.adv.DP_ALLOWNONE | wx.adv.DP_DEFAULT | wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
        sizer_14.Add(self.date_deadline, 1, 0, 8)

        self.panel_closed_date = wx.Panel(self.panel_2, wx.ID_ANY)
        self.panel_closed_date.Hide()
        self.sizer_right_pane.Add(self.panel_closed_date, 0, wx.EXPAND | wx.TOP, 8)

        sizer_18 = wx.BoxSizer(wx.HORIZONTAL)

        label_5 = wx.StaticText(self.panel_closed_date, wx.ID_ANY, "Completed:")
        sizer_18.Add(label_5, 0, 0, 0)

        self.label_closed = wx.StaticText(self.panel_closed_date, wx.ID_ANY, "01.01.2022")
        sizer_18.Add(self.label_closed, 0, 0, 0)

        sizer_15 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_right_pane.Add(sizer_15, 0, wx.EXPAND | wx.TOP, 8)

        label_3 = wx.StaticText(self.panel_2, wx.ID_ANY, "Epic:")
        sizer_15.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)

        self.combo_epic = wx.ComboBox(self.panel_2, wx.ID_ANY, choices=[], style=wx.CB_DROPDOWN)
        sizer_15.Add(self.combo_epic, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        sizer_16 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_right_pane.Add(sizer_16, 0, wx.EXPAND | wx.TOP, 8)

        label_4 = wx.StaticText(self.panel_2, wx.ID_ANY, "Labels:")
        sizer_16.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 4)

        self.edit_labels = wx.TextCtrl(self.panel_2, wx.ID_ANY, "")
        sizer_16.Add(self.edit_labels, 1, wx.ALIGN_CENTER_VERTICAL, 0)

        self.panel_3 = wx.Panel(self.panel_2, wx.ID_ANY)
        self.sizer_right_pane.Add(self.panel_3, 2, wx.EXPAND | wx.TOP, 16)

        sizer_11 = wx.BoxSizer(wx.VERTICAL)

        self.grid_comments = CommentList(self.panel_3, wx.ID_ANY, size=(1, 1))
        sizer_11.Add(self.grid_comments, 1, wx.EXPAND, 0)

        self.edit_comment = wx.richtext.RichTextCtrl(self.panel_3, wx.ID_ANY)
        self.edit_comment.SetMinSize((-1, 80))
        self.edit_comment.Hide()
        sizer_11.Add(self.edit_comment, 0, wx.EXPAND | wx.TOP, 8)

        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_11.Add(sizer_5, 0, wx.EXPAND | wx.TOP, 8)

        sizer_5.Add((20, 20), 1, wx.EXPAND, 0)

        self.panel_comment_edit_buttons = wx.Panel(self.panel_3, wx.ID_ANY)
        self.panel_comment_edit_buttons.Hide()
        sizer_5.Add(self.panel_comment_edit_buttons, 0, wx.EXPAND, 0)

        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_comment_cancel = wx.Button(self.panel_comment_edit_buttons, wx.ID_ANY, "Cancel")
        sizer_13.Add(self.btn_comment_cancel, 0, 0, 0)

        self.btn_comment_save = wx.Button(self.panel_comment_edit_buttons, wx.ID_ANY, "Apply")
        sizer_13.Add(self.btn_comment_save, 0, wx.LEFT, 8)

        self.panel_comment_buttons = wx.Panel(self.panel_3, wx.ID_ANY)
        sizer_5.Add(self.panel_comment_buttons, 0, wx.EXPAND, 0)

        sizer_12 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_comment = wx.Button(self.panel_comment_buttons, wx.ID_ANY, "Co&mment")
        sizer_12.Add(self.btn_comment, 0, 0, 0)

        self.panel_comment_buttons.SetSizer(sizer_12)

        self.panel_comment_edit_buttons.SetSizer(sizer_13)

        self.panel_3.SetSizer(sizer_11)

        self.panel_closed_date.SetSizer(sizer_18)

        self.panel_desc_buttons.SetSizer(sizer_desc_buttons)

        self.panel_completed_workflow_buttons.SetSizer(sizer_10)

        self.panel_active_workflow_buttons.SetSizer(sizer_2)

        self.panel_2.SetSizer(self.sizer_right_pane)

        self.window_1_pane_2.SetSizer(sizer_4)

        self.window_1_pane_1.SetSizer(self.sizer_left_pane)

        self.window_1.SplitVertically(self.window_1_pane_1, self.window_1_pane_2)

        self.notebook_1_pane_1.SetSizer(sizer_6)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()
        self.Centre()

        self.Bind(wx.grid.EVT_GRID_CMD_SELECT_CELL, self.OnGridTasksSelectCell, self.grid_done)
        self.Bind(wx.EVT_BUTTON, self.OnBtnNewTask, self.btn_new_task)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_CHANGED, self.OnGridTasksCellChanged, self.grid_tasks)
        self.Bind(wx.grid.EVT_GRID_CMD_SELECT_CELL, self.OnGridTasksSelectCell, self.grid_tasks)
        self.Bind(wx.EVT_BUTTON, self.OnBtnCancel, self.btn_cancel)
        self.Bind(wx.EVT_BUTTON, self.OnBtnDone, self.btn_done)
        self.Bind(wx.EVT_BUTTON, self.OnBtnReopen, self.btn_reopen)
        self.Bind(wx.EVT_BUTTON, self.OnBtnDescDiscard, self.btn_desc_discard)
        self.Bind(wx.EVT_BUTTON, self.OnBtnDescSave, self.btn_desc_save)
        self.Bind(wx.EVT_BUTTON, self.OnBtnCommentCancel, self.btn_comment_cancel)
        self.Bind(wx.EVT_BUTTON, self.OnBtnCommentSave, self.btn_comment_save)
        self.Bind(wx.EVT_BUTTON, self.OnBtnComment, self.btn_comment)
        self.Bind(wx.EVT_SHOW, self.OnFrameShow, self)
        # end wxGlade

    def OnGridTasksSelectCell(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnGridTasksSelectCell' not implemented!")
        event.Skip()

    def OnBtnNewTask(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnNewTask' not implemented!")
        event.Skip()

    def OnGridTasksCellChanged(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnGridTasksCellChanged' not implemented!")
        event.Skip()

    def OnBtnCancel(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnCancel' not implemented!")
        event.Skip()

    def OnBtnDone(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnDone' not implemented!")
        event.Skip()

    def OnBtnReopen(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnReopen' not implemented!")
        event.Skip()

    def OnBtnDescDiscard(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnDescDiscard' not implemented!")
        event.Skip()

    def OnBtnDescSave(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnDescSave' not implemented!")
        event.Skip()

    def OnBtnCommentCancel(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnCommentCancel' not implemented!")
        event.Skip()

    def OnBtnCommentSave(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnCommentSave' not implemented!")
        event.Skip()

    def OnBtnComment(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnBtnComment' not implemented!")
        event.Skip()

    def OnFrameShow(self, event):  # wxGlade: AppWindowBase.<event_handler>
        print("Event handler 'OnFrameShow' not implemented!")
        event.Skip()

# end of class AppWindowBase

class MyApp(wx.App):
    def OnInit(self):
        self.frame = AppWindowBase(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
