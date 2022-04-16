from ctypes import resize
import wx
from AppGui import AppWindowBase

class TaskLabelFieldType(wx.richtext.RichTextFieldTypeStandard):
    def __init__(self, *args, **kwds):
        super().__init__("task-label", "1 day")

    def UpdateField(self, buffer, field):
        print("In UpdateField")
        if buffer is not None:
            print("Has buffer")
            buffer.Reset()
            props = field.GetProperties()
            if props is not None:
                buffer.WriteText(props.GetProperty('task_id'))
        else:
            field.Reset()
            props = field.GetProperties()
            if props is not None:
                field.AddParagraph(str(props.GetProperty('task_id')))
        return super().UpdateField(buffer, field)

    # def GetLabel(self):
    #     props = self.GetProperties()
    #     if props is not None
    #     print(f"{props.GetProperty('task_id')}")

class AppWindow(AppWindowBase):
    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        # self.grid_tasks.HideRowLabels()
        # self.grid_tasks.HideColLabels()
        # self.grid_tasks.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        # # This editor is a bit cumbersome when it comes to adding a lot of text to a 
        # # single-line cell, but that's what we probably have to put up with for now.
        # self.grid_tasks.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        # self.grid_tasks.SetDefaultCellFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))

        # self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)

        self.drag_start = None

        self.rtc_tasks.Bind(wx.EVT_LEFT_DOWN, self.on_rtc_tasks_mouse_down)
        self.rtc_tasks.Bind(wx.EVT_MOTION, self.on_rtc_tasks_mouse_move)
        self.rtc_tasks.Bind(wx.richtext.EVT_RICHTEXT_DELETE, self.on_rtc_delete)

    def on_rtc_delete(self, event):
        print(f"{event.GetPosition()} -> {event.GetRange()}")
        #TODO: check if anything is selected
        text_obj = self.rtc_tasks.Buffer.GetLeafObjectAtPosition(event.GetPosition())
        # Allow to delete anything but fields
        if type(text_obj) is not wx._richtext.RichTextField:
            print(f"Not a field: {type(text_obj).__name__} {text_obj.GetTextForRange(wx.richtext.RichTextRange(0, 1))}")
            event.Skip()

    def on_rtc_tasks_mouse_down(self, event):
        # hit = 0
        # pos = None
        # hitObj = None
        # sel_task, pos, flags = self.rtc_tasks.FindContainerAtPoint(event.GetPosition(), pos, hit)
        # if sel_task is not None:
        #     # print(", ".join(type(i).__name__ for i in sel_task))
        #     # print("Hit a task! " + sel_task.GetText())
        #     print(f"Hit a task!")

        # hit, pos = self.rtc_tasks.HitTest(event.GetPosition())
        # if hit != wx.TE_HT_UNKNOWN and hit != wx.TE_HT_BELOW:
        #     print("Hit a task!")

        hit, col, row = self.rtc_tasks.HitTestXY(event.GetPosition())
        if hit != wx.TE_HT_UNKNOWN and hit != wx.TE_HT_BELOW:
            self.drag_start = event.GetPosition()
            self.drag_curr_row = row
            # print("Hit a task! " + self.rtc_tasks.GetLineText(row))
        else:
            self.drag_start = None
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
                # Or wxRichTextObject.GetRect().

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
        # self.resize_grid_columns()
        event.Skip()

class MyApp(wx.App):
    def OnInit(self):
        self.frame = AppWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        
        self.read_tasks()

        self.frame.Show()
        return True

    def read_tasks(self):
        # Just some dummy data for now

        # self.frame.grid_tasks.SetCellValue(0, 0, "First task")
        # self.frame.grid_tasks.SetCellValue(1, 0, "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")

        # Filling in the rich text control with a test table
        tasks_view = self.frame.rtc_tasks

        tasks_view.Freeze()
        tasks_view.BeginSuppressUndo()

        tasks_view.Clear()

        # table = tasks_view.WriteTable(100, 2)
        # for i in range(0, table.RowCount):
        #     table.GetCell(i, 1).AddParagraph("test")

        # TODO: use the system text color instead of just black
        style = wx.TextAttr(wx.Colour(0, 0, 0), 
            font=wx.Font(wx.Size(0, 14), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))
        style.SetParagraphSpacingAfter(8)
        style.SetLeftIndent(0, 30)
        style.SetLineSpacing(8)
        tasks_view.SetDefaultStyle(style)
        # tasks_view.BeginLeftIndent(0, 30)

        tasks_view.Delete(wx.richtext.RichTextRange(0, 1))
        tasks_view.AddParagraph("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")

        # wx.richtext.RichTextBuffer.AddFieldType(wx.richtext.RichTextFieldTypeStandard("task-label", "1 day", wx.richtext.RichTextFieldTypeStandard.RICHTEXT_FIELD_STYLE_NO_BORDER))
        # wx.richtext.RichTextBuffer.AddFieldType(wx.richtext.RichTextFieldTypeStandard("task-label", "1 day"))
        wx.richtext.RichTextBuffer.AddFieldType(TaskLabelFieldType())

        for i in range(0, 100):
            r = tasks_view.AddParagraph(f"test - line {i}")
            tasks_view.SetInsertionPoint(r.GetStart())
            # field_type = wx.richtext.RichTextFieldTypeStandard()
            props = wx.richtext.RichTextProperties()
            props.SetProperty("task_id", i)
            field = tasks_view.WriteField("task-label", props)
            # field.task_id = i
            # tasks_view.WriteText(f"test - line {i}\n")


        tasks_view.SetCaretPosition(-1, True)

        tasks_view.EndSuppressUndo()
        tasks_view.Thaw()

        return

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
