# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
import pickle
import wx

from impl.task import TaskStatus


class TaskListTable(wx.grid.GridTableBase):

    # This list may contain elements set to None - e.g. to designate a 
    # placeholder for a new task, or a temporary cell
    task_list = None

    # TODO: will we also need the task pool? Or should we serialize the task
    # entirely on drag'n'drop?
    def __init__(self):
        super().__init__()
        self.task_list = []
    
    def CanMeasureColUsingSameAttr(self, col):
        # We always use the same renderer and font for all cells within a column
        return True

    def GetNumberCols(self):
        return 2

    def GetNumberRows(self):
        return len(self.task_list)

    def GetValue(self, row, col):
        if col == 0:
            return ""
        task = self.task_list[row]
        return "" if task == None else task.summary

    def SetValue(self, row, col, value):
        if col == 1:
            self.task_list[row].summary = value

    def InsertRows(self, pos=0, numRows=1):
        # Slicing inserts one list into another at the `pos` index,
        # and the list being inserted is just a list of None's.
        self.task_list[pos:pos] = [None] * numRows
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, pos, numRows)
        return True

    def DeleteRows(self, pos=0, numRows=1):
        del self.task_list[pos : pos+numRows]
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, pos, numRows)
        return True

    # TODO: do we need this? - probably yes, for auto-size
    def GetColLabelValue(self, col):
        return "Status" if col == 0 else ""

    # TODO: finally decide on the naming style. Looks like we should be using wx naming
    # here, otherwise it really looks like crap.
    def NotifyGrid(self, notification, pos, numRows):
        msg = wx.grid.GridTableMessage(self, notification, pos, numRows)
        self.GetView().ProcessTableMessage(msg)

    def GetList(self):
        """
        Returns the internal list of tasks, e.g. for serialization purposes.

        Do NOT modify the returned list.  Modifications outside of the 
        TaskListTable class will not be reflected in the grid widget, and will
        eventually break the display.
        """
        return self.task_list

    def GetItem(self, row):
        return self.task_list[row]

    def GetItems(self, start, end):
        return self.task_list[start:end]

    def InsertItems(self, pos, items):
        """Inserts the passed Task objects into the list, updating the grid."""
        self.task_list[pos:pos] = items
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, pos, len(items))

    def LoadList(self, items):
        """
        Initializes the table with the `items`, discarding all previous
        contents.  Note: the table makes a shallow copy of the `items` list,
        and even though the `items` list will not be modified by the table
        in future, individual Task objects may and will be modified if the user
        edits the table.
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
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, 0, len(self.task_list))
        self.task_list = list(items)
        self.NotifyGrid(wx.grid.GRIDTABLE_NOTIFY_ROWS_INSERTED, 0, len(self.task_list))


class TaskList(wx.grid.Grid):

    # A dirty trick to link the drop target to the drag source. We need
    # some special handling when the source and the target of a drag'n'drop
    # operation is the same wxGrid control.
    drop_placeholder_pos = None
    drag_start_row = None

    task_pool = None

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        # Note: whatever the doc says about AssignTable being identical
        # to SetTable(takeOwnership=True), seems to be wrong for wxPython 4.1.1.
        # SetTable works fine whereas AssignTable loses the table object
        # and causes a crash.
        self.SetTable(TaskListTable(), takeOwnership=True)

        # TODO: maybe use system colors?
        self.drop_placeholder_attr = wx.grid.GridCellAttr()
        self.drop_placeholder_attr.SetReadOnly()
        self.drop_placeholder_attr.SetBackgroundColour(wx.Colour(224, 224, 224))

        self.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.OnBeginDrag)
        self.SetDropTarget(TaskListDropTarget(self))


    def SetTaskList(self, task_list, task_pool_):
        self.task_pool = task_pool_
        self.GetTable().LoadList(task_list)

    def GetColGridLinePen1(self, col):
        # pen = wx.Pen(wx.Colour(0, 255, 255), 1, style=wx.PENSTYLE_USER_DASH)
        # pen.SetDashes([2, 2])

        # TODO: attempts to use PENSTYLE_TRANSPARENT or PENSTYLE_USER_DASH
        # lead to black lines appearing where the background should be untouched
        # (e.g. between the dashes). This is definitely not caused by the pen
        # itself because the wxPen is implemented correctly on Windows, and
        # does even return PS_NULL for PENSTYLE_TRANSPARENT. The grid itself
        # probably draws a black line (or leaves a piece of the black background)
        # before drawing the line with GetColGridLinePen().
        # Any other dashed styles have the same issue.
        # Try to find out why it happens, and maybe fix it in wxWidgets itself.
        pen = wx.Pen(wx.Colour(255, 255, 255), 1, style=wx.PENSTYLE_SOLID)
        # pen = wx.Pen(wx.Colour(255, 255, 255), 1, style=wx.PENSTYLE_TRANSPARENT)
        return pen

    def OnBeginDrag(self, event):
        """
        Put together a data object for drag-and-drop _from_ this list, and
        initiate the drag-and-drop operation.
        """

        drag_data = {}

        sel_row_blocks = self.GetSelectedRowBlocks()
        if len(sel_row_blocks) == 0:
            cursor = self.GetGridCursorCoords()
            sel_row_blocks = [wx.grid.GridBlockCoords(cursor.Row, cursor.Col, cursor.Row, cursor.Col)]

        items = []
        table = self.GetTable()
        for block in sel_row_blocks:
            items.extend([t.id for t in table.GetItems(block.GetTopRow(), block.GetBottomRow() + 1)])
        drag_data["items"] = items

        # TODO: maybe use JSON instead of pickle for security reasons
        pickled_data = pickle.dumps(drag_data, 4)
        # Create our own data format and use it in a custom data object
        data_obj = wx.CustomDataObject("TaskListItems")
        data_obj.SetData(pickled_data)
        # TODO: do we really need a composite object? Why no just put data_obj
        # into the drag source?
        # Now make a data object for the  item list.
        composite = wx.DataObjectComposite()
        composite.Add(data_obj)

        # We need to detect whether we're dropping to the same list where the items
        # originated from. It's a dirty trick but I couldn't quickly find a better way.
        self.drop_ins_pos = None
        self.drag_start_row = event.Row

        # Create drop source and begin drag-and-drop.
        drag_source = wx.DropSource(self)
        drag_source.SetData(composite)
        res = drag_source.DoDragDrop(flags=wx.Drag_DefaultMove)
        if res == wx.DragCopy or res == wx.DragMove:
            # If a move has been requested, we want to remove the source rows from this list.
            # For now, we always do a 'move' drag'n'drop. We might need a 'copy' method
            # within the single list later (e.g. to duplicate tasks - but only in the backlog list).

            # If there was no drop into this list (i.e. dragging to another list),
            # there's no need to correct positions on deletion - we're preventing this by
            # using an insertion point beyond the end of list.
            ins_pos = self.drop_ins_pos if (self.drop_ins_pos is not None) else self.GetNumberRows()
            self.DeleteDraggedItems(sel_row_blocks, ins_pos, len(items))

        self.drag_start_row = None

    def DeleteDraggedItems(self, row_blocks, ins_pos=0, ins_len=0):
        """
        Delete the specified rows from the list, correcting row positions
        as necessary for the drag-and-drop insertion that occurred earler.
        """
        cursor_row = self.GridCursorRow
        # Going through the row blocks bottom-up and deleting them
        with wx.grid.GridUpdateLocker(self):
            for block in reversed(row_blocks):
                # If we're dropping items to the same list, we need to correct
                # the row indices below the insertion point
                # TODO: this is not going to work if we drop the rows in the middle
                # of a row block. We need to handle this on a per-row basis, or maybe
                # split each block
                start = block.TopRow
                if start >= ins_pos:
                    start += ins_len
                block_size = block.BottomRow - block.TopRow + 1
                self.DeleteRows(start, block_size)
                # Correcting cursor position
                # TODO: think if we can correct cursor position in response to insert/delete
                # events rather than micro-manage it here and there. Right now, cursor
                # correction doesn't work properly when the last item in the list is
                # being dragged - events should probably resolve this.
                # TODO: this, again, is not going to work if the cursor is in the
                # middle of a selected block.
                if start < cursor_row:
                    cursor_row -= block_size

            self.GoToCell(cursor_row, self.GridCursorCol)

    def PrepareItemsForDropping(self, items):
        """
        Takes a list of items from the drop target and performs all the
        necessary preprocessing before inserting them into the table.  Returns
        the list of items to be inserted.  The actual Task objects may differ
        from what was passed into this function.
        """
        # The simplest implementation just takes tasks from the task pool,
        # protecting the list from having items absent in the pool.
        return [self.task_pool.get(id, None) for id in items]

    def InsertDroppedItemsAtPoint(self, x, y, items):
        """
        Inserts the Task objects with the IDs listed in `items` at the (x, y)
        position in the grid. The tasks are retrieved from the task pool.
        Used with drag'n'drop.
        """
        # Find the insertion point
        self.InsertDroppedItems(self.GetDropRow(x, y))

    def InsertDroppedItems(self, index, items):
        """
        Inserts the Task objects with the IDs listed in `items` at the `index`
        row in the grid. The tasks are retrieved from the task pool.
        Used with drag'n'drop.
        """
        if index == wx.NOT_FOUND:
            index = 0

        # Remember that we got a drop at this position. This might be
        # important if we're dragging items from the same list.
        self.drop_ins_pos = index

        with wx.grid.GridUpdateLocker(self):
            self.DeleteDropPlaceholder()
            self.GetTable().InsertItems(index, self.PrepareItemsForDropping(items))

            for i in range(0, len(items)):
                self.AutoSizeRow(index + i)

            # TODO: set cursor or selection to the items we've just inserted
            # (still need the 'else' branch here)
            if len(items) == 1:
                self.SetGridCursor(index, 1)


    def MoveDropPlaceholder(self, index):
        # If it's pointing at the current placeholder position, nothing to do here
        if index == self.drop_placeholder_pos:
            return

        with wx.grid.GridUpdateLocker(self):
            self.DeleteDropPlaceholder()
            # We're not inserting a placeholder if no actual move is going to happen
            # at the drop position - that is, when the supposed insertion point is
            # pointing at the row being dragged, or at the next row.
            if self.drag_start_row is None or \
                index < self.drag_start_row or index > self.drag_start_row + 1:
                
                self.InsertDropPlaceholder(index)

    def InsertDropPlaceholder(self, row_pos):

        cursor = self.GetGridCursorCoords()
        self.InsertRows(row_pos, 1)
        if cursor.Row >= row_pos:
            cursor.Row += 1
            self.SetGridCursor(cursor)

        # Need to copy the attributes object, or otherwise it will get deleted
        # in C++ when the placeholder is deleted. Please note: Even though
        # GridCellAttr has a constructor that accepts another GridCellAttr
        # object, that constructor doesn't make a copy, but instead sets an
        # internal reference to a 'default' attr object. While it seems to yield
        # similar results e.g. on GetBackgroundColour(), the grid somehow
        # ignores the default attributes object. That's why we have to use
        # Clone().
        drop_placeholder_attr = self.drop_placeholder_attr.Clone()
        self.SetRowAttr(row_pos, drop_placeholder_attr)
        # TODO: placeholder height?
        self.drop_placeholder_pos = row_pos


    def DeleteDropPlaceholder(self):

        if self.drop_placeholder_pos is None:
            return

        self.DeleteRows(self.drop_placeholder_pos, 1)

        cursor = self.GetGridCursorCoords()
        if cursor.Row > self.drop_placeholder_pos:
            cursor.Row -= 1
            self.SetGridCursor(cursor)

        self.drop_placeholder_pos = None


    def GetDropRow(self, x, y):
        # 
        # Returns the index of the row where the dragged items should be
        # inserted upon dropping them.  The index is calculated for the table
        # that does not have the drop placeholder, i.e. it does *not* need any
        # further correction related to placeholder removal.
        # 

        pt = self.CalcGridWindowUnscrolledPosition(wx.Point(x, y), None)

        # See what row the y coord is pointing at
        index = self.YToRow(pt.y, clipToMinMax=True)
        if index == wx.NOT_FOUND: # Not clicked on an item.
            # TODO: what here?? we need to decide whether it was dropped above
            # the first row or below the last one
            index = 0

        if index == self.drop_placeholder_pos:
            # Mouse is pointing at the placeholder - that's where the items
            # are going to be inserted
            return index

        # Outside of the placeholder - see if we'll need correction
        corr = 0 if self.drop_placeholder_pos is None or index <= self.drop_placeholder_pos \
            else -1

        # Now let's see whether we want to insert a new row before or after the
        # one the user is pointing at.  We're going to compare the y coord with
        # that of the center of the row.
        cell_rect = self.CellToRect(index, 0)
        if y >= (cell_rect.Top + cell_rect.Bottom) / 2:
            corr += 1

        return index + corr


class ActiveTaskList(TaskList):
    def PrepareItemsForDropping(self, items):
        tasks_from_pool = super().PrepareItemsForDropping(items)
        for task in tasks_from_pool:
            task.set_status(TaskStatus.ACTIVE)
        return tasks_from_pool


class CompletedTaskList(TaskList):
    def PrepareItemsForDropping(self, items):
        tasks_from_pool = super().PrepareItemsForDropping(items)
        for task in tasks_from_pool:
            # Only close if it comes from the 'active' list
            if task.status == TaskStatus.ACTIVE:
                task.set_status(TaskStatus.DONE)
        return tasks_from_pool


class TaskListDropTarget(wx.DropTarget):
    """
    Drop target for the task list.
    """

    last_drag_point_y = None
    fixed_index = None

    def __init__(self, target_list, fixed_index=None):
        """
        Arguments:
        target_list: the target TaskList widget.
        fixed_index: if set to None, the items being dragged will be dropped
            at the mouse cursor position. If set to an int, the items will
            always be dropped at the specified row index, no matter what mouse
            position is. This can be used to create a widget that simply accepts
            the fact of dropping, and always inserts the item e.g. first in 
            the list.
        """
        super().__init__()

        self.target_list = target_list
        self.fixed_index = fixed_index

        # Specify the type of data we will accept.
        self.data = wx.CustomDataObject("TaskListItems")
        self.SetDataObject(self.data)


    def GetDropPos(self, x, y):
        return self.fixed_index if self.fixed_index is not None \
            else self.target_list.GetDropRow(x, y)

    # Called when OnDrop returns True.
    # We need to get the data and do something with it.
    def OnData(self, x, y, defResult):
        """
        ...
        """

        # No need to cache it anymore
        self.last_drag_point_y = -1

        # Copy the data from the drag source to our data object.
        if self.GetData():
            # Convert it back to a list and give it to the viewer.
            pickled_data = self.data.GetData()
            drag_data = pickle.loads(pickled_data)
            self.target_list.InsertDroppedItems(self.GetDropPos(x, y), drag_data.get("items", []))

        # What is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return defResult


    def OnDragOver(self, x, y, defResult):
        # print(f"OnDragOver at {x}, {y}")

        # This handler is called a lot with the same coords, so let's
        # use some caching to prevent extra processing
        if y != self.last_drag_point_y:
            self.last_drag_point_y = y
            # TODO: we need to remove the placeholder when the drag is cancelled, too
            self.target_list.MoveDropPlaceholder(self.GetDropPos(x, y))

        return defResult

    def OnEnter(self, x, y, defResult):
        self.last_drag_point_y = y
        self.target_list.MoveDropPlaceholder(self.GetDropPos(x, y))
        return defResult

    def OnLeave(self):
        self.last_drag_point_y = None
        self.target_list.DeleteDropPlaceholder()
