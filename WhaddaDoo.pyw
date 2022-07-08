#!/usr/bin/env python3
# 
# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
import datetime
import os
import tempfile
import time
import wx
from impl.task import Epic, Task, TaskComment, TaskFilter, TaskStatus
from ui.app_gui import ActiveListMenuBase, AppWindowBase
import yaml
from ui.comment_list import CommentAttrProvider
from ui.task_list import TaskListDropTarget, TaskStatusRenderer, EVT_TASK_LIST_DROP
import wx.lib.agw.persist as persist

# TODO: move to impl
class NoAliasDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True


class MSWTLWHandler(persist.TLWHandler):
    def __init__(self, pObject):
        super().__init__(pObject)

    def Save(self):
        tlw, obj = self._window, self._pObject

        pos = tlw.normal_pos
        obj.SaveValue(persist.PERSIST_TLW_X, pos.x)
        obj.SaveValue(persist.PERSIST_TLW_Y, pos.y)

        size = tlw.normal_size
        obj.SaveValue(persist.PERSIST_TLW_W, size.x)
        obj.SaveValue(persist.PERSIST_TLW_H, size.y)

        obj.SaveValue(persist.PERSIST_TLW_MAXIMIZED, tlw.IsMaximized())
        obj.SaveValue(persist.PERSIST_TLW_ICONIZED, tlw.IsIconized())

        # We explicitly skip the immediate superclass here because it would
        # overwrite our saved values.
        return persist.AUIHandler.Save(self)

    def GetKind(self):
        return "MSWWindow"


class ActiveListMenu(ActiveListMenuBase):
    def OnImportFromClipboard(self, event):  # wxGlade: ActiveListMenuBase.<event_handler>
        if not wx.TheClipboard.IsOpened():
            data_obj = wx.TextDataObject()
            wx.TheClipboard.Open()
            success = wx.TheClipboard.GetData(data_obj)
            wx.TheClipboard.Close()
            if success:
                event.EventObject.InvokingWindow.ImportPlainText(data_obj.GetText())
        event.Skip()

    def OnImportFromFile(self, event):  # wxGlade: ActiveListMenuBase.<event_handler>
        event.EventObject.InvokingWindow.ImportPlainTextFile()
        event.Skip()


class AppWindow(AppWindowBase):

    # TODO: initialize somewhere else? or otherwise instances of this class will
    # be sharing the list and dict
    tasks_pool = {}
    epics_pool = {}
    selected_task: Task = None
    # We need this to resize and repaint the correct row in grid_tasks
    selected_task_row: int = 0
    font = None

    board_id = None
    # RichTextCtrl.ChangeValue() should not be sending EVT_TEXT events; however,
    # due to a bug in wxWindows, it does send them. As a result, sometimes we
    # need to ignore the events. This field can be removed as soon as the bug
    # gets fixed.
    ignore_edit_change = False

    autosave_timer = None
    # seconds
    AUTOSAVE_DELAY = 120
    board_modified = False

    search_timer = None
    # milliseconds
    SEARCH_DELAY = 500

    normal_pos: wx.Point = None
    normal_size: wx.Size = None

    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        self.SetName("MainFrame")
        # TODO: how will this be stored with multiple tabs? a unique name for each tab?
        self.splitter_main.SetName("MainSplitter")

        self.normal_pos = wx.Point(0, 0)
        self.normal_size = wx.Size(650, 550)

        self.font = wx.Font(wx.Size(0, 14), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI")

        self.grid_tasks.SetGridLineColour(wx.Colour(224, 224, 224))
        self.grid_tasks.AutoSizeColLabelSize(0)
        self.grid_tasks.HideRowLabels()
        self.grid_tasks.HideColLabels()
        self.grid_tasks.EnableDragCell()
        self.grid_tasks.DisableDragColSize()
        self.grid_tasks.DisableDragRowSize()
        self.grid_tasks.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        # This editor is a bit cumbersome when it comes to adding a lot of text to a 
        # single-line cell, but that's what we probably have to put up with for now.
        self.grid_tasks.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.grid_tasks.SetDefaultCellFont(self.font)
        self.grid_tasks.SetLabelFont(self.font)
        self.grid_tasks.SetSelectionMode(wx.grid.Grid.GridSelectRows)

        read_only_cell_attr = wx.grid.GridCellAttr()
        read_only_cell_attr.SetReadOnly()
        status_attr = wx.grid.GridCellAttr()
        status_attr.SetReadOnly()
        status_attr.SetRenderer(TaskStatusRenderer())
        # Note: we cannot use a different font in the first column because this
        # will break row auto-sizing in the 2nd column.  It's a bug in wxWidgets.
        # status_attr.SetFont(wx.Font(wx.Size(0, 10), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))
        self.grid_tasks.SetColAttr(0, status_attr.Clone())
        self.grid_tasks.SetTabBehaviour(wx.grid.Grid.TabBehaviour.Tab_Leave)

        self.grid_tasks.Bind(wx.EVT_SIZE, self.OnGridSize)
        self.grid_tasks.Bind(wx.EVT_CHAR, self.OnGridChar)
        self.grid_tasks.Bind(wx.EVT_KEY_DOWN, self.OnGridKeyDown)
        self.grid_tasks.Bind(EVT_TASK_LIST_DROP, self.OnGridDropItems)

        self.grid_done.SetGridLineColour(wx.Colour(224, 224, 224))
        self.grid_done.AutoSizeColLabelSize(0)
        self.grid_done.HideRowLabels()
        self.grid_done.HideColLabels()
        # TODO: we need a special drop target here
        self.grid_done.EnableDragCell()
        self.grid_done.DisableDragColSize()
        self.grid_done.DisableDragRowSize()
        self.grid_done.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        self.grid_done.SetDefaultCellFont(self.font)
        self.grid_done.EnableEditing(False)
        # We don't want to let user position tasks in the 'done' list during 
        # drag'n'drop. The task being dragged needs to be inserted at the top
        # of the list.
        self.grid_done.SetDropTarget(TaskListDropTarget(self.grid_done, 0))
        self.grid_done.SetSelectionMode(wx.grid.Grid.GridSelectRows)
        self.grid_done.SetColAttr(0, status_attr)
        self.grid_done.SetTabBehaviour(wx.grid.Grid.TabBehaviour.Tab_Leave)

        self.grid_done.Bind(wx.EVT_SIZE, self.OnGridSize)
        self.grid_done.Bind(EVT_TASK_LIST_DROP, self.OnGridDropItems)

        self.grid_comments.HideRowLabels()
        self.grid_comments.HideColLabels()
        self.grid_comments.DisableDragColSize()
        self.grid_comments.DisableDragRowSize()

        # Workaround begins: we need two columns to be able to auto-size rows,
        # because the grid computes line height incorrectly for the column 0.
        # It does not set the font in the DC before calculating line height,
        # so column 0 uses the default font, and all other columns use the font
        # from the previous column.
        self.grid_comments.SetColMinimalAcceptableWidth(0)
        self.grid_comments.SetColSize(0, 1)
        # Workaround ends.

        self.grid_comments.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        self.grid_comments.SetDefaultCellFont(self.font)
        self.grid_comments.EnableEditing(False)
        self.grid_comments.SetGridLineColour(wx.Colour(224, 224, 224))
        # Unfortunately Table doesn't take ownership on SetAttrProvider(), 
        # even though the doc says otherwise. We need to keep this object around
        # until the table gets destroyed (i.e. until the frame is closed).
        self.comment_attr_provider = CommentAttrProvider()
        self.grid_comments.Table.SetAttrProvider(self.comment_attr_provider)
        self.grid_comments.SetTabBehaviour(wx.grid.Grid.TabBehaviour.Tab_Leave)

        self.grid_comments.Bind(wx.EVT_SIZE, self.OnGridSize)

        self.edit_search.Bind(wx.EVT_CHAR, self.OnEditSearchChar)
        self.search_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnSearchTimer, self.search_timer)

        self.edit_desc.Bind(wx.EVT_TEXT, self.OnEditDescTextChange)
        self.edit_desc.Bind(wx.EVT_KEY_DOWN, self.OnEditDescKeyDown)

        # TODO: think about para spacing. Might be good to just leave it as is.
        # We'll need to use blank lines anyway, or otherwise it's going to be like
        # that shitty RTF editor in Jira. E.g. can we properly set spacing between
        # a para and a list? between list items? Are we going to have lists, anyway?
        # Where outside of WhaddaDoo can we use the task description? Copy it somewhere?
        # Will text without blank lines become unreadable?
        style = wx.TextAttr(wx.Colour(0, 0, 0), font=self.font)
        style.SetParagraphSpacingAfter(8)
        self.edit_desc.SetDefaultStyle(wx.TextAttr(style))
        self.edit_comment.SetDefaultStyle(wx.TextAttr(style))
        self.edit_comment.Bind(wx.EVT_KEY_DOWN, self.OnEditCommentKeyDown)

        self.date_deadline.SetNullText("")

        self.edit_labels.Bind(wx.EVT_KILL_FOCUS, self.OnEditLabelsKillFocus)

        self.label_done.SetBuddy(self.grid_done)
        self.label_active.SetBuddy(self.grid_tasks)

        # These drop targets include the collapser 'buttons' and static lines
        self.panel_done_tasks.SetDropTarget(TaskListDropTarget(self.grid_done, 0))
        self.panel_active_tasks.SetDropTarget(TaskListDropTarget(self.grid_tasks, 0))

        # For some reason wxGlade does not generate grid.Hide() for a custom
        # grid when the 'hidden' attribute is turned on. Let's collapse this
        # grid explicitly.
        self.label_done.Expand(False)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)

        self.autosave_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnAutosaveTimer, self.autosave_timer)

        self.persist_mgr = persist.PersistenceManager.Get()
        # TODO: find a better place for this config file
        config_file = os.path.join(os.getcwd(), "WhaddaDoo_UI.ini")
        self.persist_mgr.SetPersistenceFile(config_file)
        self.persist_mgr.Register(self, MSWTLWHandler)
        self.persist_mgr.Restore(self)

        self.grid_tasks.SetFocus()

    def OnSize(self, event):
        if not self.IsMaximized() and not self.IsIconized():
            self.normal_size = event.Size
        event.Skip()

    def OnMove(self, event):
        if not self.IsMaximized() and not self.IsIconized():
            # Note: we cannot use `event.Position` because it contains the screen
            # coordinates of the *client area*, whereas we need the screen coords
            # of the window itself.  There's no easy way to convert from one to
            # the other; the function GetClientAreaOrigin() seems to work incorrectly
            # and always return (0, 0).
            self.normal_pos = self.GetScreenPosition()
        event.Skip()

    def OnClose(self, event):
        # TODO: make sure it's also called when the app is being closed due to
        # the system shutdown
        self.search_timer.Stop()
        self.SaveTaskChanges()
        self.SaveLabels()
        self.SaveBoard()
        self.persist_mgr.SaveAndUnregister(self.splitter_main)
        self.persist_mgr.SaveAndUnregister(self)
        event.Skip()

    def AskIfDiscardDescChanges(self):
        dlg = wx.MessageDialog(self, "Discard all changes you've made to the task description?", "Discard changes", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.LoadTaskDesc()

    def OnBtnDescDiscard(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.AskIfDiscardDescChanges()
        event.Skip()

    def OnBtnDescSave(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.SaveTaskChanges()
        event.Skip()

    def OnEditDescTextChange(self, event):
        if not self.ignore_edit_change:
            self.ShowDescButtons()
        event.Skip()

    def OnEditDescKeyDown(self, event):
        # TODO: also unblock Alt+F4
        # TODO: make a subclass of richtextctrl and handle the tab key in that class
        if event.KeyCode == wx.WXK_TAB:
            event.GetEventObject().Navigate(wx.NavigationKeyEvent.NavigationKeyEventFlags.FromTab + 
                (0 if event.ShiftDown() else wx.NavigationKeyEvent.NavigationKeyEventFlags.IsForward))
        else:
            if self.panel_desc_buttons.Shown:
                if event.KeyCode == wx.WXK_ESCAPE and not event.HasAnyModifiers():
                    self.AskIfDiscardDescChanges()
                elif event.KeyCode == wx.WXK_RETURN and event.GetModifiers() == wx.MOD_CONTROL:
                    self.SaveTaskChanges()
            event.Skip()

    # TODO: group the richtext and apply/cancel buttons into a separate widget
    # and reduce code duplication here. Well, maybe it's not a good idea because
    # the description and the comments show the apply/cancel buttons on different
    # conditions.
    def OnEditCommentKeyDown(self, event):
        if event.KeyCode == wx.WXK_ESCAPE and not event.HasAnyModifiers():
            really_cancel = (self.edit_comment.Value == "")
            if not really_cancel:
                dlg = wx.MessageDialog(self, "Discard the comment text typed so far?", "Discard comment", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
                really_cancel = (dlg.ShowModal() == wx.ID_OK)
                dlg.Destroy()

            if really_cancel:
                self.ShowCommentEditor(False)
                self.grid_comments.SetFocus()
        elif event.KeyCode == wx.WXK_RETURN and event.GetModifiers() == wx.MOD_CONTROL:
            self.AddNewComment()

        event.Skip()

    def OnGridChar(self, event):
        if event.KeyCode == wx.WXK_INSERT and not event.HasAnyModifiers():
            # If the table is empty, GridCursorRow might well be -1, and we
            # can't insert items at -1.  That's why we limit it at 0.
            self.InsertNewTask(max(self.grid_tasks.GridCursorRow, 0))

        event.Skip()

    def OnGridKeyDown(self, event):
        if event.GetModifiers() == wx.MOD_CONTROL and \
            (event.KeyCode == wx.WXK_UP or event.KeyCode == wx.WXK_DOWN):

            # Moving the selected items up or down
            self.grid_tasks.MoveSelectedItems(-1 if event.KeyCode == wx.WXK_UP else 1)
            # MoveSelectedItems will generate a TaskListDropEvent, which in turn fires
            # HandleBoardChange(), so we don't need to signal the board change separately.

        elif event.KeyCode == wx.WXK_RETURN:
            # Preventing the grid from moving the cursor down after editing
            if self.grid_tasks.IsCellEditControlEnabled():
                self.grid_tasks.DisableCellEditControl()
            else:
                # If there's no editor, let the grid do the default stuff
                event.Skip()

        else:
            event.Skip()

    def OnGridTasksSelectCell(self, event):
        # This handler is used for both grid_tasks and grid_done
        grid = event.GetEventObject()
        if event.GetCol() == 0:
            grid.SetGridCursor(event.GetRow(), 1)
            # Note: we deliberately disallow the grid to handle this event, otherwise
            # it will reset the position to column 0 even after our SetGridCursor call.
            event.Veto()
        else:
            # TODO: do we need to save anything before changing the selection pointer?
            self.SaveTaskChanges()
            self.SaveLabels()
            self.selected_task_row = event.GetRow()
            try:
                self.selected_task = grid.GetTable().GetItem(self.selected_task_row)
            except IndexError:
                # Sometimes we might go out of range, e.g. when the table is empty
                self.selected_task = None
            self.LoadTaskDetails()
            event.Skip()

    # TODO: as soon as the bug in wxWidgets that breaks row auto-sizing gets
    # fixed, remove this handler (and remove column 0).
    def OnGridCommentsSelectCell(self, event):  # wxGlade: AppWindowBase.<event_handler>
        if event.GetCol() == 0:
            event.GetEventObject().SetGridCursor(event.GetRow(), 1)
            # Note: we deliberately disallow the grid to handle this event, otherwise
            # it will reset the position to column 0 even after our SetGridCursor call.
            event.Veto()
        else:
            event.Skip()

    def ShowDescButtons(self, show: bool = True):
        # TODO: We should probably restrict Tab navigation to this panel only,
        # i.e. rich edit box - discard - save.

        # self.panel_desc_buttons.Layout()
        # self.panel_desc_buttons.ShowWithEffect(wx.SHOW_EFFECT_SLIDE_TO_BOTTOM)
        # TODO: do something to prevent flickering. The panel initially
        # shows up in the top left corner of the right pane, and with a
        # weird size. Then, Layout() places it where it belongs.
        self.panel_desc_buttons.Show(show)
        # self.sizer_right_pane.Show(2)
        self.sizer_right_pane.Layout()
        # self.panel_desc_buttons.Layout()

    def SaveTaskChanges(self):
        # TODO: check if validators can/should be used instead
        task = self.selected_task
        if task is None:
            return

        desc = self.edit_desc.GetValue()
        paragraphs = desc.split("\n")
        summary = paragraphs[0]
        desc = "\n".join(paragraphs[1:])
        # Updating the 'modified' flag
        self.HandleBoardChange(task.desc != desc or task.summary != summary)

        task.desc = desc
        if summary != task.summary:
            task.summary = summary
            # TODO: tell the grid to update only the task we've modified
            self.grid_tasks.AutoSizeRow(self.selected_task_row)
            self.grid_tasks.ForceRefresh()

        self.ShowDescButtons(False)

    def LoadTaskDesc(self):
        task = self.selected_task
        # TODO: properly clear the right panel if the selected task is None
        if task is None:
            return
        self.ignore_edit_change = True
        self.edit_desc.ChangeValue(task.get_full_desc())
        self.ignore_edit_change = False
        self.ShowDescButtons(False)
        # TODO: adjust edit_desc size to fit contents

    def LoadTaskDetails(self):
        task = self.selected_task
        # TODO: properly clear the right panel if the selected task is None
        if task is None:
            return

        # TODO: if the task is completed (done or cancel), disable editing
        # (except for comments).
        self.LoadTaskDesc()
        # TODO: think whether we want to gray it out
        is_active = (task.status == TaskStatus.ACTIVE)
        self.edit_desc.Enabled = is_active
        self.panel_active_workflow_buttons.Show(is_active)
        self.panel_completed_workflow_buttons.Show(not is_active)
        self.panel_active_workflow_buttons.ContainingSizer.Layout()

        self.label_created.LabelText = task.creation_date.isoformat(" ", "minutes")
        has_close_date = task.close_date is not None
        if has_close_date:
            self.label_closed.LabelText = task.close_date.isoformat(" ", "minutes")
        self.panel_closed_date.Show(has_close_date)
        self.panel_closed_date.ContainingSizer.Layout()

        self.edit_labels.Value = " ".join(task.labels)

        if task.deadline is None:
            # First set it to a specific value (tomorrow) - when the user clicks
            # the checkbox, this value will be selected by default.
            self.date_deadline.Value = wx.DateTime.Today().Add(wx.DateSpan(days = 1))
            # Now set it to a null date in order to uncheck the checkbox.
            self.date_deadline.Value = wx.DefaultDateTime
        else:
            d = task.deadline
            self.date_deadline.Value = wx.DateTime.FromDMY(d.day, d.month - 1, d.year)
        self.date_deadline.Enabled = is_active

        # TODO: can this be broken via epics.yaml so that it throws a ValueError?
        index = 0
        if task.epic is not None:
            epic_list = sorted(self.epics_pool.values(), key=lambda epic: epic.name)
            index = epic_list.index(task.epic)
        self.combo_epic.Select(index)
        self.combo_epic.Enabled = is_active

        self.grid_comments.Table.SetList(task.comments)
        self.grid_comments.AutoSizeRows()
        # TODO: fill in the remaining controls

    def OnDateDeadlineChanged(self, event):  # wxGlade: AppWindowBase.<event_handler>
        if self.selected_task is not None:
            self.HandleBoardChange()
            dt = event.GetEventObject().Value
            self.selected_task.deadline = datetime.date(dt.year, dt.month + 1, dt.day) if dt.IsValid() \
                else None
            # TODO: only repaint the current task, and ideally only the status cell
            self.grid_tasks.ForceRefresh()
        event.Skip()

    def OnComboEpicChanged(self, event):  # wxGlade: AppWindowBase.<event_handler>
        if self.selected_task is not None:
            self.HandleBoardChange()
            combo = event.GetEventObject()
            sel_epic_id = combo.GetClientData(combo.GetSelection())
            self.selected_task.epic = self.epics_pool[sel_epic_id] if sel_epic_id is not None \
                else None
            # TODO: only repaint the current task, and ideally only the status cell
            self.grid_tasks.ForceRefresh()
            
        event.Skip()

    def SaveLabels(self):
        if self.selected_task is not None:
            new_labels = sorted(self.edit_labels.Value.split())
            self.HandleBoardChange(self.selected_task.labels != new_labels)
            self.selected_task.labels = new_labels
            # TODO: only repaint the current task, and ideally only the status cell
            self.grid_tasks.ForceRefresh()
            self.grid_done.ForceRefresh()

    def OnEditLabelsKillFocus(self, event):
        self.SaveLabels()
        event.Skip()

    def OnEditLabelsTextEnter(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.SaveLabels()
        event.Skip()

    def ResizeGridColumns(self, grid):
        #
        # Resizes the last column in the grid to fit the client area, 
        # if possible. Then, auto-sizes all the rows because the change to
        # column width might be causing changes in word wrapping.
        #
        last_col = grid.GetNumberCols() - 1
        new_width = grid.GetClientSize().width
        for i in range(0, last_col):
            new_width -= grid.GetColSize(i)

        # If there's too little or no space for the column, limit its width
        # to 20. It would be better to use the header width instead, but
        # Grid does not provide a way to retrieve it.
        grid.SetColSize(last_col, max(new_width, 20))
        grid.AutoSizeRows()

    def OnGridSize(self, event):
        self.ResizeGridColumns(event.GetEventObject())
        event.Skip()

    def OnGridTasksCellChanged(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.HandleBoardChange()
        self.grid_tasks.AutoSizeRow(event.GetRow())
        # We need to reload the description box on the right side.
        self.LoadTaskDetails()
        event.Skip()
        
    def OnFrameShow(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.ResizeGridColumns(self.grid_tasks)
        self.ResizeGridColumns(self.grid_done)
        self.ResizeGridColumns(self.grid_comments)

        # Can't do it in the frame's __init__() because for a maximized frame,
        # maximizing actually happens *after* __init__(), and the frame remains
        # in the 'restored' state all the way through __init__().
        self.persist_mgr.RegisterAndRestore(self.splitter_main)

        for f in os.scandir("."):
            if f.is_dir() and os.path.isfile(os.path.join(f.path, "tasks.yaml")):
                self.LoadBoard(f.name)
                # TODO: remove this line after adding support for multiple boards
                break

        if self.board_id is None:
            # If we couldn't find any boards, let's create a new one
            self.NewBoard("Main")

        event.Skip()

    def NewBoard(self, board_id):
        self.board_id = board_id
        self.board_modified = False
        self.tasks_pool = {}
        self.epics_pool = {}
        self.InitBoardWidgets([], [])

    # TODO: think on naming conventions. Are "Save/Load" about disk I/O? If so,
    # how should we name methods dealing with memory objects and widgets?
    def SaveBoard(self):
        # TODO: only save the board if it has been modified? Add a 'force' parm?
        # At least we don't want extra writing when called from OnClose().

        # TODO: keep a sequential list of IDs from the reading op, and use it
        # to determine the sequence in which the Task objects should be
        # written to the output file.
        dir_name = self.board_id
        try:
            try:
                os.mkdir(dir_name)
            except FileExistsError:
                # It's ok for the directory to already exist
                pass
            
            # TODO: we can append new data to tasks.yaml if it's known to have
            # no changes to the old contents (e.g. the user only added new tasks
            # and didn't touch the *contents* of the old ones). Caveat: we do
            # store the status inside of tasks.yaml. Maybe it's wrong.

            tasks_file_name = None
            with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, delete=False,
                encoding='utf8', prefix="tasks.", suffix=".yaml") as f:

                yaml.dump(self.tasks_pool, f, default_flow_style=False,
                    allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper)
                # Keep it for future reference
                tasks_file_name = f.name

            index_file_name = None
            with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, delete=False,
                encoding='utf8', prefix="active.", suffix=".txt") as f:

                for task in self.grid_tasks.GetTable().GetList():
                    f.write(task.id + "\n")
                # Keep it for future reference
                index_file_name = f.name

            # Note: we do not implement a full transaction-like rename here
            # because the new files have been created successfully, so even
            # in the worst scenario when something breaks in the middle, the
            # user can manually rename them. A full rename (renaming the
            # old files first) would help implement a clean recovery in case
            # of errors, and would also help in case the old files are
            # locked (on Windows). But it's too complicated for such a
            # simple tool.
            self.ReplaceFile(os.path.join(dir_name, "tasks.yaml"), tasks_file_name)
            self.ReplaceFile(os.path.join(dir_name, "active.txt"), index_file_name)

            self.board_modified = False

        except OSError:
            # TODO: !!IMPORTANT!! show an error message
            pass

    @staticmethod
    def ReplaceFile(old_name, new_name):
        try:
            os.remove(old_name)
        except FileNotFoundError:
            # It's okay, we've just created a new file, no old version here
            pass
        os.rename(new_name, old_name)

    def InitBoardWidgets(self, active_tasks, completed_tasks):
        self.tabs_boards.SetPageText(0, self.board_id)
        self.combo_epic.Clear()
        # Note: we want the 'no epic' (blank) string to be at the top of the
        # list, and therefore can't rely on the native sorting provided by 
        # ComboBox itself.
        self.combo_epic.Append("", None)
        # for (id, epic) in sorted(self.epics_pool.items(), key=lambda item: item[1].name):
        #     self.combo_epic.Append(epic.name, id)
        for epic in sorted(self.epics_pool.values(), key=lambda epic: epic.name):
            self.combo_epic.Append(epic.name, epic.id)
        # Adding the 'no epic' item to the pool, too.  Can't do it earlier.
        self.epics_pool[None] = Epic()

        # TODO: sort tasks by completion date, newer to older
        self.grid_done.SetTaskList(completed_tasks, self.tasks_pool)
        self.grid_done.AutoSizeRows()
        self.grid_done.SetGridCursor(0, 1)

        # Note: we're loading grid_tasks after grid_done in order to get the
        # first *active* task displayed in the right pane (i.e. we want
        # grid_tasks.SetGridCursor() to go after grid_done.SetGridCursor(),
        # not before it).
        self.grid_tasks.SetTaskList(active_tasks, self.tasks_pool)
        self.grid_tasks.AutoSizeRows()
        self.grid_tasks.SetGridCursor(0, 1)
    
    def LoadBoard(self, board_id):
        self.board_id = board_id
        self.board_modified = False
        self.tasks_pool = {}
        active_tasks = []
        dir_name = self.board_id
        self.epics_pool = {}
        try:
            with open(os.path.join(dir_name, "epics.yaml"), "r", encoding='utf8') as f:
                obj_pool = yaml.load(f, Loader=yaml.SafeLoader)
                # TODO: verify that obj_pool is a dict
                for (k, v) in obj_pool.items():
                    self.epics_pool[k] = Epic.from_plain_object(k, v)
        except FileNotFoundError:
            # We don't care if there are no epics
            pass
        # TODO: handle key lookup exceptions that Epic.from_plain_object might
        # throw (or add another exception to from_plain_object that would better 
        # describe the error).

        # TODO: handle exceptions
        completed_set = {}
        active_set = {}
        with open(os.path.join(dir_name, "tasks.yaml"), "r", encoding='utf8') as f:
            # Since we don't save object tags in save_board(), it's ok to use
            # the SafeLoader here - YAML won't be able to deduce class names
            # anyway.
            obj_pool = yaml.load(f, Loader=yaml.SafeLoader)
            # TODO: verify that obj_pool is a dict
            for (k, v) in obj_pool.items():
                task = Task.from_plain_object(k, v, self.epics_pool)
                self.tasks_pool[k] = task
                if task.status == TaskStatus.ACTIVE:
                    active_set[k] = task
                else:
                    completed_set[k] = task

        with open(os.path.join(dir_name, "active.txt"), "r", encoding='utf8') as f:
            for task_id in f.readlines():
                task_id = task_id.strip()
                if task_id in self.tasks_pool:
                    # TODO: make sure the status is 'active'
                    active_tasks.append(self.tasks_pool[task_id])
                    del active_set[task_id]
                else:
                    # TODO: show an error message. Maybe throw an exception.
                    # But we probably want to recover as much of the board 
                    # contents as we can in case of such errors.
                    pass

        # TODO: verify that active_set is empty
        self.InitBoardWidgets(active_tasks, list(completed_set.values()))

    def MarkCompleted(self, final_status=TaskStatus.DONE):
        task = self.selected_task
        if task is None:
            # Nothing to do here
            return
        self.HandleBoardChange()
        task.set_status(final_status)
        self.grid_tasks.DeleteRows(self.selected_task_row)
        self.grid_done.GetTable().InsertItems(0, [task])
        self.grid_done.AutoSizeRow(0)
        # TODO: store the close date in Task attributes

        # We need to refresh the right panel so that the controls get into
        # correct state.
        self.LoadTaskDetails()

    def ReopenTask(self):
        task = self.selected_task
        if task is None:
            # Nothing to do here
            return
        self.HandleBoardChange()
        task.set_status(TaskStatus.ACTIVE)
        self.grid_done.DeleteRows(self.selected_task_row)
        self.grid_tasks.GetTable().InsertItems(0, [task])
        self.grid_tasks.AutoSizeRow(0)
        # TODO: add a comment like 'Reopened' to somehow remember the date.
        # It would be nice to also store the date when the task was closed
        # last time.
        
        # We need to refresh the right panel so that the controls get into
        # correct state.
        self.LoadTaskDetails()

    def InsertNewTask(self, row):
        self.HandleBoardChange()
        task = Task()
        self.tasks_pool[task.id] = task
        self.grid_tasks.Table.InsertItems(row, [task])
        self.grid_tasks.AutoSizeRow(row)
        self.grid_tasks.SetGridCursor(row, 1)
        self.grid_tasks.EnableCellEditControl()

    def OnBtnCancel(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.MarkCompleted(TaskStatus.CANCELLED)
        event.Skip()

    def OnBtnDone(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.MarkCompleted()
        event.Skip()

    def OnBtnReopen(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.ReopenTask()
        event.Skip()

    def OnBtnNewTask(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.InsertNewTask(0)
        event.Skip()

    def ShowCommentEditor(self, show=True):
        self.edit_comment.Show(show)
        self.panel_comment_buttons.Show(not show)
        self.panel_comment_edit_buttons.Show(show)
        self.edit_comment.ContainingSizer.Layout()

    def OnBtnComment(self, event):  # wxGlade: AppWindowBase.<event_handler>
        if self.selected_task is None:
            event.Skip()
            return
        # When the user clicks "Comment", we open the editor but don't add the
        # comment to the list just yet.
        self.edit_comment.Value = ""
        self.ShowCommentEditor()
        self.edit_comment.SetFocus()
        # comment = self.grid_comments.Table.AddNewComment()
        # self.grid_comments.GoToCell(self.grid_comments.NumberRows - 1, 0)
        # self.selected_task.comments.append()
        event.Skip()

    def OnBtnCommentCancel(self, event):  # wxGlade: AppWindowBase.<event_handler>
        # Just hiding the editor and doing nothing else.
        self.ShowCommentEditor(False)
        event.Skip()

    def AddNewComment(self):
        # TODO: make sure there's a selected task (e.g. can't add a comment if
        # the board is empty)
        self.HandleBoardChange()
        comment = TaskComment(self.edit_comment.Value)
        self.grid_comments.Table.AddNewComment(comment)
        self.ShowCommentEditor(False)
        last_row = self.grid_comments.NumberRows - 1
        self.grid_comments.AutoSizeRow(last_row - 1)
        self.grid_comments.AutoSizeRow(last_row)
        self.grid_comments.GoToCell(last_row, 0)
        self.grid_comments.SetFocus()

    def OnBtnCommentSave(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.AddNewComment()
        event.Skip()

    def FilterTasks(self, query):
        print("Filter called")
        self.grid_done.Filter(TaskFilter(query))
        self.grid_tasks.Filter(TaskFilter(query))

    def OnEditSearchCancel(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.FilterTasks("")
        event.Skip()

    def OnEditSearchSeach(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.FilterTasks(event.GetString())
        event.Skip()

    def OnEditSearchChange(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.search_timer.StartOnce(self.SEARCH_DELAY)
        event.Skip()

    def OnEditSearchChar(self, event):
        # We need some special handling for Esc and Enter
        if event.KeyCode == wx.WXK_ESCAPE and not event.HasAnyModifiers():
            # TODO: prevent double filtering (first call here and then another
            # call on timer set up in OnEditSearchChange)
            event.GetEventObject().Clear()
            self.FilterTasks("")
        elif event.KeyCode == wx.WXK_RETURN and not event.HasAnyModifiers():
            self.FilterTasks(event.GetEventObject().Value)

        event.Skip()

    def OnSearchTimer(self, event):
        self.FilterTasks(self.edit_search.Value)
        event.Skip()

    def OnBtnActiveMore(self, event):  # wxGlade: AppWindowBase.<event_handler>
        menu_bar = ActiveListMenu()
        # TODO: disable the 'import from clipboard' item if the clipboard
        # contents is not suitable
        menu = menu_bar.GetMenu(0)
        # Need to detach it from the MenuBar before attaching to the frame
        menu.Detach()
        # Since wxGlade generates event handlers in the MenuBar subclass, we need
        # to forward menu events to the menu bar.
        self.Bind(wx.EVT_MENU, lambda event: menu_bar.GetEventHandler().ProcessEvent(event))
        pt = self.ScreenToClient(self.btn_active_more.ScreenRect.BottomLeft)
        self.PopupMenu(menu, pt)
        # Clean it up
        self.Unbind(wx.EVT_MENU)
        menu.Destroy()

        event.Skip()

    # TODO: we probably need some options, e.g. separate tasks by empty lines
    # (i.e. sequential non-empty lines go to the description of the same task)
    def ImportPlainText(self, text):
        self.HandleBoardChange()
        new_tasks = [ Task(summary=line.strip()) for line in text.splitlines() if len(line.strip()) > 0 ]
        
        base_id = int(time.time() * 100)
        for task in new_tasks:
            # Overriding the default task ID, because it's not guaranteed to be
            # unique for tasks series created too fast.
            task.set_numeric_id(base_id)
            # We don't want a clash with other default IDs, so let's add a prefix
            task.id = "imp-" + task.id
            base_id -= 1
            self.tasks_pool[task.id] = task

        self.grid_tasks.Table.InsertItems(0, new_tasks)
        self.grid_tasks.AutoSizeRows()
        self.grid_tasks.SetGridCursor(0, 1)
        self.grid_tasks.SelectBlock(0, 0, len(new_tasks) - 1, 1)


    def ImportPlainTextFile(self):
        with wx.FileDialog(self, "Import tasks", wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() != wx.ID_CANCEL:
                try:
                    with open(fileDialog.GetPath(), "r") as f:
                        self.ImportPlainText(f.read())
                except IOError:
                    # TODO: show an error message
                    pass

    def HandleBoardChange(self, really_modified = True):
        """
        Processes a change to the board contents.  If `really_modified` is True,
        the 'dirty' flag is triggered, and the auto-save timer is started.
        If `really_modified` is False, does nothing - this can be used in places
        where the caller needs to compare new contents against the old one.
        """
        if really_modified:
            self.board_modified = True
            self.autosave_timer.StartOnce(self.AUTOSAVE_DELAY * 1000)

    def OnAutosaveTimer(self, event):
        self.SaveBoard()
        event.Skip()

    def OnGridDropItems(self, event):
        print("Drop event")
        self.HandleBoardChange()
        event.Skip()


class MyApp(wx.App):
    def OnInit(self):
        yaml.add_representer(Task, Task.yaml_representer)
        yaml.add_representer(TaskStatus, TaskStatus.yaml_representer)
        yaml.add_representer(TaskComment, TaskComment.yaml_representer)
        yaml.add_representer(datetime.datetime, self.yaml_date_representer)

        self.frame = AppWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)

        self.frame.Show()
        return True

    @staticmethod
    def yaml_date_representer(self, data):
        value = data.isoformat(" ", "seconds")
        return self.represent_scalar('tag:yaml.org,2002:timestamp', value)


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
