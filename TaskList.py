import pickle
import sys
from   random import choice
import wx


class TaskList(wx.grid.Grid):
    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        self.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.on_begin_drag)
        self.SetDropTarget(TaskListDropTarget(self))


    def GetItemInfo(self, idx):
        """
        Collect all relevant data of a listitem, and put it in a list.
        """

        l = []
        l.append(idx) # We need the original index, so it is easier to eventualy delete it.
        # l.append(self.GetItemData(idx)) # Itemdata.
        # l.append(self.GetItemText(idx)) # Text first column.
        # for i in range(1, self.GetColumnCount()): # Possible extra columns.
        #     l.append(self.GetItem(idx, i).GetText())
        return l


    def on_begin_drag(self, event):
        """
        Put together a data object for drag-and-drop _from_ this list.
        """

        drag_data = {}
        # drag_data["source_id"] = self.GetID()

        sel_row_blocks = self.GetSelectedRowBlocks()
        # drag_data["row_blocks"] = sel_row_blocks

        items = []
        for block in sel_row_blocks:
            for i in range(block.GetTopRow(), block.GetBottomRow() + 1):
                items.append(self.GetCellValue(i, 0))
        drag_data["items"] = items
        print(f"{items} {items[0]}")

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

        # We need to detect whether we're dropping to the same list where the
        # items originated. It's a dirty trick but I couldn't quickly find a better way.
        self.drop_ins_pos = None

        # Create drop source and begin drag-and-drop.
        drag_source = wx.DropSource(self)
        drag_source.SetData(composite)
        res = drag_source.DoDragDrop(flags=wx.Drag_DefaultMove)

        # if self.drop_ins_pos is not None:

        # If there was no drop into this list (i.e. dragging to another list),
        # there's no need to correct positions on deleteion - we're preventing this by
        # using an insertion point beyond the end of list.
        ins_pos = self.drop_ins_pos if self.drop_ins_pos is not None else self.GetNumberRows()
        self.delete_dragged_items(sel_row_blocks, ins_pos, len(items))

        # If a move has been requested, we want to remove the source rows from this list.
        # For now, we always do a 'move' drag'n'drop. We might need a 'copy' method
        # within the single list later (e.g. to duplicate tasks - but only in the backlog list).

        # for block in sel_row_blocks:
            # If we're dropping to the same list, we need to correct the row indices
            # below the insertion point
        # if res == wx.DragMove:
            # It's possible we are dragging/dropping from this list to this list.
            # In which case, the index we are removing may have changed...

            # Find correct position.
            # l.reverse() # Delete all the items, starting with the last item.
            # TODO: this should be different for Grid
            # for i in l:
            #     pos = self.FindItem(i[0], i[2])
            #     self.DeleteItem(pos)

    # TODO: PEP 8 here around =0
    def delete_dragged_items(self, row_blocks, ins_pos = 0, ins_len = 0):

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

        # Find insertion point.
        # index, flags = self.HitTest((x, y))

        # TODO: probably translate x,y to logical coords
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
        source: source listctrl.
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
