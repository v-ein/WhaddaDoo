Here's a list of known issues in the current version of WhaddaDoo. Please keep in mind that it is an alpha version, that is, it's still work in progress.

- Any change to the filter field resets the cursor and selection in the task list. This shows up pretty well when you find the task you need, and want to clear the filter but keep the task on the screen.
- Filtering makes the right pane flicker. Probably related to the cursor/selection issue described above.
- On drag'n'drop, the drop placeholder sometimes doesn't look right. For example, when dragging from 'Done' to 'Active', the placeholder has a different height. This might become irrelevant in the new upcoming version of drag'n'drop code.
- On some systems, the background of the window is painted white, causing the list to visually merge into the window. Probably a wxWidgets issue.
- For closed tasks, there's no way to scroll the description field in the right pane (when the description is too long to fit the field).
- Alt+letter hotkeys don't work properly - seems to be a wxWidgets issue.
- (!) The description field seems to be intermittently losing its default font for no apparent reason. This usually happens when the user interacts with the description box (by entering text or moving the focus), and usually doesn't happen when he navigates the list of tasks.
- Shift+Tab in task lists and in the comment list doesn't move the focus backwards.
- Alt+F4 doesn't close the window if the description field is focused.
- The 'ellipsis' button near the search field doesn't do anything - advanced search is yet to be implemented.
- There's no UI to edit epics - to be implemented.
