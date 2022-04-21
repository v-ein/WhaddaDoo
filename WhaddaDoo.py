from ctypes import resize
from errno import EDEADLK
import wx
from impl.task import Task, TaskComment
from ui.app_gui import AppWindowBase

class AppWindow(AppWindowBase):

    # TODO: initialize somewhere else? or otherwise instances of this class will
    # be sharing the list and dict
    active_tasks = []
    active_tasks_pool = {}
    selected_task: Task = None
    # We need this to resize and repaint the correct row in grid_tasks
    selected_task_row: int = 0
    font = None

    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

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

        self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)
        # self.grid_tasks.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_grid_select_cell)

        self.grid_comments.HideRowLabels()
        self.grid_comments.HideColLabels()
        self.grid_comments.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        self.grid_comments.SetDefaultCellFont(self.font)

        self.grid_comments.Bind(wx.EVT_SIZE, self.on_grid_comments_size)

        self.edit_desc.Bind(wx.EVT_KILL_FOCUS, self.on_edit_kill_focus)


    def on_edit_kill_focus(self, event):
        self.save_task_changes()
        event.Skip()

    def on_grid_tasks_select_cell(self, event):
        if event.GetCol() == 0:
            event.GetEventObject().SetGridCursor(event.GetRow(), 1)
            # Note: we deliberately disallow the grid to handle this event, otherwise
            # it will reset the position to column 0 even after our SetGridCursor call.
            event.Veto()
        else:
            # TODO: do we need to save anything before changing the selection pointer?
            self.save_task_changes()
            self.selected_task_row = event.GetRow()
            self.selected_task = self.grid_tasks.GetTable().get_item(self.selected_task_row)
            self.load_task_details()
            event.Skip()

    def save_task_changes(self):
        # TODO: check if validators can/should be used instead
        task = self.selected_task
        if task is None:
            return

        desc = self.edit_desc.GetValue()
        paragraphs = desc.split("\n")
        summary = paragraphs[0]
        desc = "\n".join(paragraphs[1:])
        task.desc = desc
        if summary != task.summary:
            task.summary = summary
            # TODO: tell the grid to update the task we've modified
            # self.grid_tasks.ForceRefresh()
            self.grid_tasks.AutoSizeRow(self.selected_task_row)
            self.grid_tasks.ForceRefresh()

    def load_task_details(self):
        task = self.selected_task
        # self.edit_desc.Clear()
        # TODO: clear `edit_desc` better - do not leave the empty paragraph
        # self.edit_desc.Delete(wx.richtext.RichTextRange(0, 1))
        # TODO: do we really need to set up style each time, or can we do this
        # in the constructor?
        style = wx.TextAttr(wx.Colour(0, 0, 0), font=self.font)
        # TODO: think about para spacing. Might be good to just leave it as is.
        # We'll need to use blank lines anyway, or otherwise it's going to be like
        # that shitty RTF editor in Jira. E.g. can we properly set spacing between
        # a para and a list? between list items? Are we going to have lists, anyway?
        # Where outside of WhaddaDoo can we use the task description? Copy it somewhere?
        # Will text without blank lines become unreadable?
        style.SetParagraphSpacingAfter(8)
        # style.SetLeftIndent(0, 30)
        # style.SetLineSpacing(8)
        self.edit_desc.SetDefaultStyle(style)

        # self.edit_desc.AddParagraph(task.summary)
        # TODO: Should it be WriteText instead?
        # self.edit_desc.AddParagraph(task.desc)
        self.edit_desc.SetValue(task.summary + ("\n" + task.desc if task.desc else ""))
        # TODO: adjust edit_desc size to fit contents
        # self.edit_desc.
        grid_comments = self.grid_comments
        rows = grid_comments.GetNumberRows()
        if rows > 0:
            grid_comments.DeleteRows(0, rows)
        grid_comments.AppendRows(2 * len(task.comments))
        row = 0
        for comment in task.comments:
            # TODO: format it properly
            # TODO: set cell attributes (or use a custom attribute provider to
            # implement striping)
            grid_comments.SetCellValue(row, 0, comment.date.isoformat(' ', 'seconds'))
            grid_comments.SetCellValue(row + 1, 0, comment.text)
            row += 2
        self.resize_comments_columns()
        # TODO: fill in the remaining controls


    def resize_grid_columns(self):
        task_list = self.grid_tasks
        task_list.SetColSize(1, task_list.GetClientSize().width - task_list.GetColSize(0))
        task_list.AutoSizeRows()


    def on_grid_tasks_size(self, event):
        self.resize_grid_columns()
        event.Skip()

    # TODO: combine it with resize_grid_columns - we can always auto-size the
    # last column
    def resize_comments_columns(self):
        grid_comments = self.grid_comments
        grid_comments.SetColSize(0, grid_comments.GetClientSize().width)
        grid_comments.AutoSizeRows()

    def on_grid_comments_size(self, event):
        self.resize_comments_columns()
        event.Skip()

    def on_grid_tasks_cell_changed(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.grid_tasks.AutoSizeRow(event.GetRow())
        # We need to reload the description box on the right side.
        self.load_task_details()
        event.Skip()
        

    def on_frame_show(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.load_tasks_list()
        self.resize_grid_columns()
        self.resize_comments_columns()
        event.Skip()

    # TODO: throw away this method? rename it? It no longer serves the purpose it did before
    def load_tasks_list(self):
        self.active_tasks_pool = {t.id: t for t in self.active_tasks if t is not None}
        self.grid_tasks.set_task_list(self.active_tasks, self.active_tasks_pool)
        self.grid_tasks.SetGridCursor(0, 1)


class MyApp(wx.App):
    def OnInit(self):
        self.frame = AppWindow(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        
        self.read_tasks()

        self.frame.Show()
        return True

    def read_tasks(self):
        tasks_view = self.frame.grid_tasks
        # Just some dummy data for now
        # TODO: is there a Freeze/Undo capability? Should we use it?
        task = Task()
        task.summary = "First task"
        task.set_numeric_id(-1)
        self.frame.active_tasks.append(task)
        task = Task()
        task.summary = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        for i in range(0, 10):
            task.comments.append(TaskComment(f"Test comment {i}"))
        task.set_numeric_id(-2)
        self.frame.active_tasks.append(task)

        for i in range(0, 8):
            task = Task()
            task.summary = f"test - line {i}"
            task.set_numeric_id(i)
            self.frame.active_tasks.append(task)

        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)


        return

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
