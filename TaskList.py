import pickle
import sys
from   random import choice
import wx

# class MyFrame
# class MyDragList
# class MyListDrop
# class MyApp

#---------------------------------------------------------------------------

# items = ['Foo', 'Bar', 'Baz', 'Zif', 'Zaf', 'Zof']

# #---------------------------------------------------------------------------

# class MyFrame(wx.Frame):
#     def __init__(self, parent, id):
#         wx.Frame.__init__(self, parent, id,
#                           "Sample one",
#                           size=(450, 295))

#         #------------

#         self.SetIcon(wx.Icon('icons/wxwin.ico'))
#         self.SetMinSize((450, 295))

#         #------------

#         dl1 = MyDragList(self, style=wx.LC_LIST)
#         dl1.SetBackgroundColour("#e6ffd0")

#         dl2 = MyDragList(self, style=wx.LC_REPORT)
#         dl2.InsertColumn(0, "Column - 0", wx.LIST_FORMAT_LEFT)
#         dl2.InsertColumn(1, "Column - 1", wx.LIST_FORMAT_LEFT)
#         dl2.InsertColumn(2, "Column - 2", wx.LIST_FORMAT_LEFT)
#         dl2.SetBackgroundColour("#f0f0f0")

#         maxs = -sys.maxsize - 1

#         for item in items:
#             dl1.InsertItem(maxs, item)
#             idx = dl2.InsertItem(maxs, item)
#             dl2.SetItem(idx, 1, choice(items))
#             dl2.SetItem(idx, 2, choice(items))

#         #------------

#         sizer = wx.BoxSizer(wx.HORIZONTAL)

#         sizer.Add(dl1, proportion=1, flag=wx.EXPAND)
#         sizer.Add(dl2, proportion=1, flag=wx.EXPAND)

#         self.SetSizer(sizer)
#         self.Layout()

#---------------------------------------------------------------------------

class TaskList(wx.grid.Grid):
    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)

        #------------

        self.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.StartDrag)

        #------------

        dt = TaskListDropTarget(self)
        self.SetDropTarget(dt)

    #-----------------------------------------------------------------------

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


    def StartDrag(self, event):
        """
        Put together a data object for drag-and-drop _from_ this list.
        """

        l = []
        for block in self.GetSelectedRowBlocks():
            for i in range(block.GetTopRow(), block.GetBottomRow() + 1):
                l.append(self.GetItemInfo(i))

        # Pickle the items list.
        itemdata = pickle.dumps(l, 1)
        # Create our own data format and use it
        # in a Custom data object.
        ldata = wx.CustomDataObject("TaskListItems")
        ldata.SetData(itemdata)
        # Now make a data object for the  item list.
        data = wx.DataObjectComposite()
        data.Add(ldata)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we want to remove the item from this list.
        if res == wx.DragMove:
            # It's possible we are dragging/dropping from this list to this list.
            # In which case, the index we are removing may have changed...

            # Find correct position.
            l.reverse() # Delete all the items, starting with the last item.
            # TODO: this should be different for Grid
            # for i in l:
            #     pos = self.FindItem(i[0], i[2])
            #     self.DeleteItem(pos)


    def Insert(self, x, y, seq):
        """
        Insert text at given x, y coordinates --- used with drag-and-drop.
        """

        # Find insertion point.
        # index, flags = self.HitTest((x, y))

        # TODO: probably translate x,y to logical coords
        cell_coords = self.XYToCell(x, y)

        if cell_coords == wx.NOT_FOUND: # Not clicked on an item.
            # TODO: what here??
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
        self.InsertRows(index, len(seq))

        # TODO: fill in the cells
        # for i in seq: # Insert the item data.

        #     idx = self.InsertItem(index, i[2])
        #     self.SetItemData(idx, i[1])
        #     for j in range(1, self.GetColumnCount()):
        #         try: # Target list can have more columns than source.
        #             self.SetItem(idx, j, i[2+j])
        #         except:
        #             pass # Ignore the extra columns.
        #     index += 1

#---------------------------------------------------------------------------

class TaskListDropTarget(wx.DropTarget):
    """
    Drop target for the task list.
    """
    def __init__(self, source):
        """
        Arguments:
        source: source listctrl.
        """
        super().__init__()

        #------------

        self.dv = source

        #------------

        # Specify the type of data we will accept.
        self.data = wx.CustomDataObject("TaskListItems")
        self.SetDataObject(self.data)

    #-----------------------------------------------------------------------

    # Called when OnDrop returns True.
    # We need to get the data and do something with it.
    def OnData(self, x, y, d):
        """
        ...
        """

        # Copy the data from the drag source to our data object.
        if self.GetData():
            # Convert it back to a list and give it to the viewer.
            ldata = self.data.GetData()
            l = pickle.loads(ldata)
            self.dv.Insert(x, y, l)

        # What is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d
