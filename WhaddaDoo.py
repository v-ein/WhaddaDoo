import datetime
import os
import tempfile
import wx
from impl.task import Task, TaskComment, TaskStatus
from ui.app_gui import AppWindowBase
import yaml

# TODO: move to impl
class NoAliasDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True

class AppWindow(AppWindowBase):

    # TODO: initialize somewhere else? or otherwise instances of this class will
    # be sharing the list and dict
    active_tasks = []
    tasks_pool = {}
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

    def __init__(self, *args, **kwds):
        AppWindowBase.__init__(self, *args, **kwds)

        self.board_id = "test-board"

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
        # TODO: make the first column read-only

        self.grid_tasks.Bind(wx.EVT_SIZE, self.on_grid_tasks_size)
        # self.grid_tasks.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.on_grid_select_cell)

        self.grid_comments.HideRowLabels()
        self.grid_comments.HideColLabels()
        self.grid_comments.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        self.grid_comments.SetDefaultCellFont(self.font)

        self.grid_comments.Bind(wx.EVT_SIZE, self.on_grid_comments_size)

        self.edit_desc.Bind(wx.EVT_TEXT, self.on_edit_desc_text_change)
        self.edit_desc.Bind(wx.EVT_KILL_FOCUS, self.on_edit_kill_focus)
        # self.btn_desc_discard.Bind(wx.EVT_KILL_FOCUS, self.on_edit_kill_focus)
        # self.btn_desc_save.Bind(wx.EVT_KILL_FOCUS, self.on_edit_kill_focus)

        # TODO: think about para spacing. Might be good to just leave it as is.
        # We'll need to use blank lines anyway, or otherwise it's going to be like
        # that shitty RTF editor in Jira. E.g. can we properly set spacing between
        # a para and a list? between list items? Are we going to have lists, anyway?
        # Where outside of WhaddaDoo can we use the task description? Copy it somewhere?
        # Will text without blank lines become unreadable?
        style = wx.TextAttr(wx.Colour(0, 0, 0), font=self.font)
        style.SetParagraphSpacingAfter(8)
        self.edit_desc.SetDefaultStyle(style)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        # TODO: make sure it's also called when the app is being closed due to
        # the system shutdown
        self.save_board()
        event.Skip()

    def on_btn_desc_discard(self, event):  # wxGlade: AppWindowBase.<event_handler>
        dlg = wx.MessageDialog(self, "Discard all changes you've made to the task description?", "Discard changes", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.load_task_desc()
        event.Skip()

    def on_btn_desc_save(self, event):  # wxGlade: AppWindowBase.<event_handler>
        self.save_task_changes()
        event.Skip()

    def on_edit_desc_text_change(self, event):
        if not self.ignore_edit_change:
            self.show_desc_buttons()
        event.Skip()

    def on_edit_kill_focus(self, event):
        new_focus = event.GetWindow()
        if new_focus != self.btn_desc_discard and new_focus != self.btn_desc_save:
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
            try:
                self.selected_task = self.grid_tasks.GetTable().get_item(self.selected_task_row)
            except IndexError:
                # Sometimes we might go out of range, e.g. when the table is empty
                self.selected_task = None
            self.load_task_details()
            event.Skip()

    def show_desc_buttons(self, show: bool = True):
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

    def save_task_changes(self):
        # TODO: check if validators can/should be used instead
        task = self.selected_task
        if task is None:
            return

        desc = self.edit_desc.GetValue()
        paragraphs = desc.split("\n")
        summary = paragraphs[0]
        desc = "\n".join(paragraphs[1:])
        # TODO: we need to compare desc in order to set the modified flag for the board
        task.desc = desc
        if summary != task.summary:
            task.summary = summary
            # TODO: tell the grid to update only the task we've modified
            self.grid_tasks.AutoSizeRow(self.selected_task_row)
            self.grid_tasks.ForceRefresh()

        self.show_desc_buttons(False)

    def load_task_desc(self):
        task = self.selected_task
        # TODO: properly clear the right panel if the selected task is None
        if task is None:
            return
        self.ignore_edit_change = True
        self.edit_desc.ChangeValue(task.get_full_desc())
        self.ignore_edit_change = False
        self.show_desc_buttons(False)

    def load_task_details(self):
        task = self.selected_task
        # TODO: properly clear the right panel if the selected task is None
        if task is None:
            return

        self.load_task_desc()

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
        # TODO: we should iterate over the sub-directories in the repo and
        # for every directory with "tasks.yaml" inside, load it as a board.
        # We *don't know* the board name beforehand.
        self.load_board()
        self.load_tasks_list()
        self.resize_grid_columns()
        self.resize_comments_columns()
        event.Skip()

    # TODO: throw away this method? rename it? It no longer serves the purpose it did before
    def load_tasks_list(self):
        self.grid_tasks.set_task_list(self.active_tasks, self.tasks_pool)
        self.grid_tasks.SetGridCursor(0, 1)

    # TODO: think on naming conventions. Are "Save/Load" about disk I/O? If so,
    # how should we name methods dealing with memory objects and widgets?
    def save_board(self):
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

                for task in self.grid_tasks.GetTable().get_list():
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
            self.replace_file(os.path.join(dir_name, "tasks.yaml"), tasks_file_name)
            self.replace_file(os.path.join(dir_name, "active.txt"), index_file_name)

        except OSError:
            # TODO: !!IMPORTANT!! show an error message
            pass

    @staticmethod
    def replace_file(old_name, new_name):
        try:
            os.remove(old_name)
        except FileNotFoundError:
            # It's okay, we've just created a new file, no old version here
            pass
        os.rename(new_name, old_name)

    def load_board(self):
        self.tasks_pool = {}
        self.active_tasks = []

        dir_name = self.board_id
        # TODO: handle exceptions
        with open(os.path.join(dir_name, "tasks.yaml"), "r", encoding='utf8') as f:
            # Since we don't save object tags in save_board(), it's ok to use
            # the SafeLoader here - YAML won't be able to deduce class names
            # anyway.
            obj_pool = yaml.load(f, Loader=yaml.SafeLoader)
            # TODO: verify that obj_pool is a dict
            for (k, v) in obj_pool.items():
                self.tasks_pool[k] = Task.from_plain_object(k, v)

        with open(os.path.join(dir_name, "active.txt"), "r", encoding='utf8') as f:
            for task_id in f.readlines():
                task_id = task_id.strip()
                if task_id in self.tasks_pool:
                    # TODO: make sure the status is 'active'
                    self.active_tasks.append(self.tasks_pool[task_id])
                else:
                    # TODO: show an error message. Maybe throw an exception.
                    # But we probably want to recover as much of the board 
                    # contents as we can in case of such errors.
                    pass


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
