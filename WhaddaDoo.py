from ctypes import resize
import wx
from AppGui import AppWindowBase

class AppWindow(AppWindowBase):
    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        self.grid_tasks.HideRowLabels()
        self.grid_tasks.HideColLabels()
        self.grid_tasks.EnableDragCell()
        self.grid_tasks.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        # This editor is a bit cumbersome when it comes to adding a lot of text to a 
        # single-line cell, but that's what we probably have to put up with for now.
        self.grid_tasks.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        self.grid_tasks.SetDefaultCellFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI"))

        self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)

        self.drag_start = None
        self.is_dragging = False

        # self.rtc_tasks.Bind(wx.EVT_LEFT_DOWN, self.on_rtc_tasks_mouse_down)
        # self.grid_tasks.Bind(wx.EVT_MOTION, self.on_grid_tasks_mouse_move)
        # self.grid_tasks.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.on_grid_tasks_cell_begin_drag)

    def on_rtc_tasks_mouse_down(self, event):
        # hit, col, row = self.rtc_tasks.HitTestXY(event.GetPosition())
        # if hit != wx.TE_HT_UNKNOWN and hit != wx.TE_HT_BELOW:
        #     self.drag_start = event.GetPosition()
        #     self.drag_curr_row = row
        #     # print("Hit a task! " + self.rtc_tasks.GetLineText(row))
        # else:
        #     self.drag_start = None
        event.Skip()

    def on_grid_tasks_cell_begin_drag(self, event):
        print("Cell dragging begins!")
        for block in self.grid_tasks.GetSelectedRowBlocks():
            print(f"{block.GetTopRow()} - {block.GetBottomRow()}")
        self.is_dragging = True
        event.Skip()
        # return False

    def on_grid_tasks_mouse_move(self, event):
        print("Mouse move")
        if event.Dragging() and self.is_dragging:
            print("Dragging a row")
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
