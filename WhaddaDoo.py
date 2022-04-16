from ctypes import resize
import wx
from AppGui import AppWindowBase

class AppWindow(AppWindowBase):
    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        self.grid_tasks.HideRowLabels()
        self.grid_tasks.HideColLabels()
        self.grid_tasks.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        # This editor is a bit cumbersome when it comes to adding a lot of text to a 
        # single-line cell, but that's what we probably have to put up with for now.
        self.grid_tasks.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.grid_tasks.SetDefaultCellFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))

        self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)

        self.drag_start = None

        # self.rtc_tasks.Bind(wx.EVT_LEFT_DOWN, self.on_rtc_tasks_mouse_down)
        # self.rtc_tasks.Bind(wx.EVT_MOTION, self.on_rtc_tasks_mouse_move)

    def on_rtc_tasks_mouse_down(self, event):
        # hit, col, row = self.rtc_tasks.HitTestXY(event.GetPosition())
        # if hit != wx.TE_HT_UNKNOWN and hit != wx.TE_HT_BELOW:
        #     self.drag_start = event.GetPosition()
        #     self.drag_curr_row = row
        #     # print("Hit a task! " + self.rtc_tasks.GetLineText(row))
        # else:
        #     self.drag_start = None
        event.Skip()

    def on_rtc_tasks_mouse_move(self, event):
        if event.Dragging() and self.drag_start is not None:
            # TODO: if the starting direction is not vertical, allow
            # the regular selection mechanism to fire
            tasks_view = self.rtc_tasks
            # TODO: we can move the insertion point to mid-line if
            # we add (or subtract?) half a line height here before doing the hit test
            hit, col, row = tasks_view.HitTestXY(event.GetPosition())

            # The last condition excludes mouse positions above the first line
            # (in this case, the hit test is BEYOND and the row points to the last line)
            if hit != wx.TE_HT_UNKNOWN and \
                (row < self.drag_curr_row or row > self.drag_curr_row + 1) and \
                (row < tasks_view.GetNumberOfLines()-1 or hit != wx.TE_HT_BEYOND):

                # print(f"Dragging, cur = {self.drag_curr_row}, new = {row}, hit = {hit}")

                # calculating the exact insertion position based off mid-row pos
                # TODO: it appears to be a 'mission impossible' for the moment
                # Buffer.GetRangeSize() might be of help, if we find a way to supply 
                # the DC and drawing context

                curr_row = self.drag_curr_row
                line_length = tasks_view.GetLineLength(curr_row)
                range = wx.richtext.RichTextRange(tasks_view.XYToPosition(0, curr_row),
                    tasks_view.XYToPosition(line_length, curr_row))

                tasks_view.Freeze()
                tasks_view.BeginSuppressUndo()

                buf = tasks_view.Buffer
                # para = buf.GetParagraphAtLine(curr_row)
                field = buf.GetLeafObjectAtPosition(range.GetStart())
                # TODO: make sure it's a field. If not, what to do? cancel drag?
                if type(field) is wx._richtext.RichTextField:
                    props = field.GetProperties()
                    print(f"{props.GetProperty('task_id')}")

                container = wx.richtext.RichTextParagraphLayoutBox()
                buf.CopyFragment(range, container)
                # print(f"Copy: {range}")
                # print(f"CopyFragment = {res}")
                buf.DeleteRange(range)

                # TODO: do we need to account for line numbers shift after Delete() ?
                # - yes, otherwise it will jump around. Doc it in a comment.
                # TODO: with the current implementation, there's no chance to
                # move a task to the very end since we always insert *before* a task
                if (row > curr_row):
                    row -= 1

                # buf.InsertFragment(tasks_view.XYToPosition(0, row), container)
                # print(f"Insert at: {tasks_view.XYToPosition(0, row)}")
                buf.InsertParagraphsWithUndo(tasks_view.XYToPosition(0, row), container, tasks_view, 0)
                buf.InvalidateHierarchy(range)
                tasks_view.SetSelection(tasks_view.XYToPosition(0, row), tasks_view.XYToPosition(range.GetLength() - 1, row))

                tasks_view.EndSuppressUndo()
                tasks_view.Thaw()

                self.drag_curr_row = row

                # TODO: enable undo for the last movement (how? should we disable it after first move?) -> See BatchingUndo()
                # TODO: refresh the index
                # TODO: extract a function from here, so that we can handle Ctrl+Up/Down

        else:
            event.Skip()

    def resize_grid_columns(self):
        self.grid_tasks.SetColSize(0, self.grid_tasks.GetClientSize().width)
        self.grid_tasks.AutoSizeRows()

    def on_grid_tasks_size(self, event):
        self.resize_grid_columns()
        event.Skip()

    def on_grid_tasks_cell_changed(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.grid_tasks.AutoSizeRow(event.GetRow())
        event.Skip()

    def on_frame_show(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.resize_grid_columns()
        event.Skip()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = AppWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        
        self.read_tasks()

        self.frame.Show()
        return True

    def read_tasks(self):
        tasks_view = self.frame.grid_tasks
        # tasks_view.CreateGrid(102, 1)
        # Just some dummy data for now
        # TODO: is there a Freeze/Undo capability? Should we use it?
        tasks_view.SetCellValue(0, 0, "First task")
        tasks_view.SetCellValue(1, 0, "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")

        for i in range(0, 8):
            r = tasks_view.SetCellValue(i + 2, 0, f"test - line {i}")

        return

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
