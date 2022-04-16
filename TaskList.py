import pickle
import sys
from   random import choice
import wx


class TaskList(wx.grid.Grid):
    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.on_begin_drag)
        self.SetDropTarget(TaskListDropTarget(self))


    def on_begin_drag(self, event):
        """
        Put together a data object for drag-and-drop _from_ this list, and
        initiate the drag-and-drop operation.
        """

        drag_data = {}

        sel_row_blocks = self.GetSelectedRowBlocks()

        items = []
        for block in sel_row_blocks:
            for i in range(block.GetTopRow(), block.GetBottomRow() + 1):
                items.append(self.GetCellValue(i, 0))
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

        # Create drop source and begin drag-and-drop.
        drag_source = wx.DropSource(self)
        drag_source.SetData(composite)
        res = drag_source.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If a move has been requested, we want to remove the source rows from this list.
        # For now, we always do a 'move' drag'n'drop. We might need a 'copy' method
        # within the single list later (e.g. to duplicate tasks - but only in the backlog list).

        # If there was no drop into this list (i.e. dragging to another list),
        # there's no need to correct positions on deleteion - we're preventing this by
        # using an insertion point beyond the end of list.
        ins_pos = self.drop_ins_pos if self.drop_ins_pos is not None else self.GetNumberRows()
        self.delete_dragged_items(sel_row_blocks, ins_pos, len(items))


    def delete_dragged_items(self, row_blocks, ins_pos=0, ins_len=0):
        """
        Delete the specified rows from the list, correcting row positions
        as necessary for the drag-and-drop insertion that occurred earler.
        """
        # Going through the row blocks bottom-up and deleting them
        for block in reversed(row_blocks):
            # If we're dropping items to the same list, we need to correct
            # the row indices below the insertion point
            # TODO: this is not going to work if we drop the rows in the middle
            # of a row block. We need to handle this on a per-row basis, or maybe
            # split each block
            start = block.TopRow
            if start >= ins_pos:
                start += ins_len
            self.DeleteRows(start, block.BottomRow - block.TopRow + 1)


    def insert_dropped_items(self, x, y, items):
        """
        Insert text at given x, y coordinates --- used with drag-and-drop.
        """

        # Find the insertion point
        cell_coords = self.XYToCell(x, y)

        if cell_coords == wx.NOT_FOUND: # Not clicked on an item.
            # TODO: what here?? we need to decide whether it was dropped above
            # the first row or below the last one
            cell_coords = wx.grid.GridCellCoords(0, 0)

            # if flags & (wx.LIST_HITTEST_NOWHERE|wx.LIST_HITTEST_ABOVE|wx.LIST_HITTEST_BELOW): # Empty list or below last item.
            #     index = self.GetItemCount() # Append to end of list.
            # elif self.GetItemCount() > 0:
            #     if y <= self.GetItemRect(0).y: # Clicked just above first item.
            #         index = 0 # Append to top of list.
            #     else:
            #         index = self.GetItemCount() + 1 # Append to end of list.

        # else: # Clicked on an item.
        # TODO: no correction for now, but we'll need it later
        #     # Get bounding rectangle for the item the user is dropping over.
        #     rect = self.GetItemRect(index)

        #     # If the user is dropping into the lower half of the rect,
        #     # we want to insert _after_ this item.
        #     # Correct for the fact that there may be a heading involved.
        #     if y > rect.y - self.GetItemRect(0).y + rect.height/2:
        #         index += 1


        index = cell_coords.GetRow()
        
        # Remember that we got a drop at this position. This might be
        # important if we're dragging items from the same list.
        self.drop_ins_pos = index

        # TODO: maybe block repainting
        self.InsertRows(index, len(items))

        for item in items:
            self.SetCellValue(index, 0, item)
            self.AutoSizeRow(index)
            index += 1


class TaskListDropTarget(wx.DropTarget):
    """
    Drop target for the task list.
    """
    def __init__(self, target_list_):
        """
        Arguments:
        target_list_: the target TaskList widget.
        """
        super().__init__()

        self.target_list = target_list_

        # Specify the type of data we will accept.
        self.data = wx.CustomDataObject("TaskListItems")
        self.SetDataObject(self.data)


    # Called when OnDrop returns True.
    # We need to get the data and do something with it.
    def OnData(self, x, y, defResult):
        """
        ...
        """

        # Copy the data from the drag source to our data object.
        if self.GetData():
            # Convert it back to a list and give it to the viewer.
            pickled_data = self.data.GetData()
            drag_data = pickle.loads(pickled_data)
            self.target_list.insert_dropped_items(x, y, drag_data.get("items", []))

        # What is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return defResult
