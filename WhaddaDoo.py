from ctypes import resize
import wx
from impl.task import Task
from ui.app_gui import AppWindowBase

class AppWindow(AppWindowBase):

    active_tasks = []
    active_tasks_pool = {}

    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        self.grid_tasks.SetGridLineColour(wx.Colour(224, 224, 224))
        self.grid_tasks.AutoSizeColLabelSize(0)
        self.grid_tasks.HideRowLabels()
        self.grid_tasks.HideColLabels()
        self.grid_tasks.EnableDragCell()
        self.grid_tasks.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        # This editor is a bit cumbersome when it comes to adding a lot of text to a 
        # single-line cell, but that's what we probably have to put up with for now.
        self.grid_tasks.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.grid_tasks.SetDefaultCellFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))

        self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)
        self.grid_tasks.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_grid_select_cell)

        self.grid_comments.HideRowLabels()
        self.grid_comments.HideColLabels()


    def on_grid_select_cell(self, event):
        if event.GetCol() == 0:
            event.GetEventObject().SetGridCursor(event.GetRow(), 1)
            # Note: we deliberately disallow the grid to handle this event, otherwise
            # it will reset the position to column 0 even after our SetGridCursor call.
            event.Veto()
        else:
            event.Skip()


    def resize_grid_columns(self):
        task_list = self.grid_tasks
        task_list.SetColSize(1, task_list.GetClientSize().width - task_list.GetColSize(0))
        task_list.AutoSizeRows()


    def on_grid_tasks_size(self, event):
        self.resize_grid_columns()
        
        event.Skip()

    def on_grid_tasks_cell_changed(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.grid_tasks.AutoSizeRow(event.GetRow())
        event.Skip()
        

    def on_frame_show(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.load_tasks_list()
        self.resize_grid_columns()
        event.Skip()

    # TODO: throw away this method? rename it? It no longer serves the purpose it did before
    def load_tasks_list(self):
        self.active_tasks_pool = {t.id: t for t in self.active_tasks if t is not None}
        self.grid_tasks.set_task_list(self.active_tasks, self.active_tasks_pool)


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
        task.set_numeric_id(-2)
        self.frame.active_tasks.append(task)

        for i in range(0, 8):
            task = Task()
            task.summary = f"test - line {i}"
            task.set_numeric_id(i)
            self.frame.active_tasks.append(task)

        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)

        tasks_view.SetGridCursor(0, 1)

        return

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
