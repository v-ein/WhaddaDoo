# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
import wx
from impl.task import TaskComment

class CommentAttrProvider(wx.grid.GridCellAttrProvider):
    date_attr = None
    text_attr = None

    def __init__(self):
        super().__init__()

        self.date_attr = wx.grid.GridCellAttr()
        # self.date_attr.BackgroundColour = wx.Colour(240, 240, 240)
        # TODO: it would be better to set it from the outside
        self.date_attr.Font = wx.Font(wx.Size(0, 12), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI")
        self.date_attr.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTER_VERTICAL)
        # self.date_attr.SetReadOnly()

        self.text_attr = wx.grid.GridCellAttr()
        self.text_attr.Font = wx.Font(wx.Size(0, 14), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName = "Segoe UI")


    def GetAttr(self, row, col, kind):
        if row %2 == 0:
            return self.date_attr.Clone()
        else:
            return super().GetAttr(row, col, kind)

# TODO: try to make a common base class for CommentTable and TaskListTable.
# Surely a table backed up by a list of objects can be generalized... however,
# the comment list uses two rows per list element. So maybe not.
# But at least the notification methods can be moved to the superclass?
class CommentTable(wx.grid.GridTableBase):

    # This list is not supposed to contain None values
    comment_list = None

    def __init__(self):
        super().__init__()
        self.comment_list = []
    
    def GetNumberCols(self):
        return 1

    def GetNumberRows(self):
        return 2 * len(self.comment_list)

    def GetValue(self, row, col):
        comment = self.comment_list[row // 2]
        # For safety... e.g. an empty table
        if comment is None:
            return ""
        return comment.text if row % 2 == 1 \
            else comment.date.isoformat(" ", "minutes")

    def SetValue(self, row, col, value):
        # The list is supposed to be read-only
        pass
        # if row % 2 == 1:
        #     self.comment_list[row].summary = value

    # def InsertRows(self, pos=0, numRows=1):
    #     # Slicing inserts one list into another at the `pos` index,
    #     # and the list being inserted is just a list of None's.
    #     self.task_list[pos:pos] = [None] * numRows
    #     self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, pos, numRows)
    #     return True

    # def DeleteRows(self, pos=0, numRows=1):
    #     del self.task_list[pos : pos+numRows]
    #     self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, pos, numRows)
    #     return True

    # TODO: do we need this? - probably yes, for auto-size
    # def GetColLabelValue(self, col):
    #     return "Status" if col == 0 else ""

    # TODO: finally decide on the naming style. Looks like we should be using wx naming
    # here, otherwise it really looks like crap.
    def NotifyGrid(self, notification, pos, numRows):
        msg = wx.grid.GridTableMessage(self, notification, pos, numRows)
        self.GetView().ProcessTableMessage(msg)

    # def GetList(self):
    #     """
    #     Returns the internal list of tasks, e.g. for serialization purposes.

    #     Do NOT modify the returned list.  Modifications outside of the 
    #     TaskListTable class will not be reflected in the grid widget, and will
    #     eventually break the display.
    #     """
    #     return self.task_list

    # def GetItem(self, row):
    #     return self.task_list[row]

    # def GetItems(self, start, end):
    #     return self.task_list[start:end]

    # def InsertItems(self, pos, items):
    #     """Inserts the passed Task objects into the list, updating the grid."""
    #     self.task_list[pos:pos] = items
    #     self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, pos, len(items))

    def AddNewComment(self, comment_text=""):
        comment = TaskComment(comment_text)
        row = self.GetNumberRows()
        self.comment_list.append(comment)
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, row, 2)
        return comment

    def SetList(self, new_list):
        """
        Initializes the table with a new list, discarding all previous contents.
        Note: the list of comments is not copied, and **must not** be modified
        outside of the table while the table 'owns' it.
        """
        # Believe it or not, as of wxPython 4.1.1 there's *no* way to force the
        # grid to re-request the table size from the table. 
        # TaskListTable.GetNumberRows() is only called once (!!!), when
        # the table gets assigned to the grid. On all other occasions, we have
        # to use notifications to inform the grid about size changes.
        # TODO: maybe we should change the logic, and re-create the table
        # and use SetTable() each time we load a list of tasks. Or maybe even
        # reuse the same table object, just call SetTable(). Need to check what
        # attributes might get lost on resetting the table.
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, 0, 2 * len(self.comment_list))
        self.comment_list = new_list
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, 0, 2 * len(self.comment_list))


class CommentList(wx.grid.Grid):

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        self.SetTable(CommentTable(), takeOwnership=True)

    def GetRowGridLinePen(self, row):
        if row % 2 == 0:
            return wx.Pen(wx.WHITE, 1, wx.SOLID)
        else:
            return self.GetDefaultGridLinePen()
