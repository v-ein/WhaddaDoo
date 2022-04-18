import datetime
from enum import Enum


class TaskStatus(Enum):
    ACTIVE = "active"
    DONE = "done"
    CANCELLED = "cancelled"

class Epic:
    name = ""

class Task:

    id: str = None
    status: TaskStatus = TaskStatus.ACTIVE

    # For convenience, we store the first line of the description separately,
    # in `summary`, since that's what will be displayed in the task list. The 
    # rest of the description goes into the `desc` field.

    # TODO: do we need to annotate the type on simple types like string?
    summary: str = ""
    desc: str = ""
    comments = []
    # TODO: decide on data type here. Do we want to include time? timezone?
    deadline: datetime.date = None
    epic: Epic = None
    labels = []

    def __init__(self, *arg, **kw):
        pass

