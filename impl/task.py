# Copyright © 2022 Vladimir Ein. All rights reserved.
# License: http://opensource.org/licenses/MIT
# 
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import shlex
import time
from typing import Any, Dict, List, Optional
from yaml import Dumper, Node


class TaskStatus(Enum):
    ACTIVE = "active"
    DONE = "done"
    CANCELLED = "cancelled"

    @staticmethod
    def yaml_representer(dumper: Dumper, data: "TaskStatus") -> Node:
        return dumper.represent_str(data.value)


@dataclass
class Epic:
    # Unlike Task objects, this ID is shown to the user, and is supposed to be
    # readable (to a certain extent).  It's auto-generated based off the epic
    # name, but can be edited by the user.
    # Note: even though we store epics in a dict by their ID and could use that
    # dict's keys to exclusively store IDs, this makes it difficult to map Epics
    # back to IDs.  That's why we also store the ID inside the Epic object.
    id: str = ""
    name: str = ""
    # TODO: add a field for user-defined color (which we'll be using for labels
    # in the status cell)

    @staticmethod
    def from_plain_object(id: str, obj: Dict) -> "Epic":
        """
        Construct an epic based off a plain object read from YAML.

        We can't use YAML constructors directly because we don't save tags into
        YAML, and therefore PyYAML can't deduce object types on reading.
        """
        return Epic(id, obj["name"])


class TaskComment:
    date: datetime
    text: str = ""

    def __init__(self, text_: str, date_: Optional[datetime] = None):
        self.text = text_
        self.date = date_ if date_ is not None else datetime.now()

    @staticmethod
    def yaml_representer(dumper: Dumper, data: "TaskComment") -> Node:
        filtered = {
            "date": data.date,
            "text": data.text
        }
        return dumper.represent_mapping('tag:yaml.org,2002:map', filtered)


_ID_BASE_TIMESTAMP = datetime(2022, 1, 1).timestamp()
_ID_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"


class Task:

    id: str = ""
    status: TaskStatus = TaskStatus.ACTIVE

    # For convenience, we store the first line of the description separately,
    # in `summary`, since that's what will be displayed in the task list. The 
    # rest of the description goes into the `desc` field.

    # TODO: do we need to annotate the type on simple types like string?
    summary: str = ""
    desc: str = ""
    comments: List[TaskComment]
    # TODO: decide on data type here. Do we want to include time? timezone?
    deadline: Optional[date] = None
    epic: Optional[Epic] = None
    labels: List[str]
    creation_date: datetime
    close_date: Optional[datetime] = None
    # TODO: think if we need the 'reopened' flag

    def __init__(self, summary: str = "", desc: str = "") -> None:
        self.gen_id()
        self.creation_date = datetime.now()
        self.comments = []
        self.labels = []
        self.summary = summary
        self.desc = desc

    def gen_id(self) -> str:
        """
        Generates an ID for this task based off the current date and time.
        Since the tasks are typically created manually, timestamp-based IDs
        are going to be sufficiently unique; in case of automated procedures,
        however, we'll need to improve this process.

        Returns the generated id (and assigns it to Task.id, too).
        """
        ts = int((time.time() - _ID_BASE_TIMESTAMP) * 100)
        return self.set_numeric_id(ts)

    def set_numeric_id(self, num_id: int) -> str:
        """
        Converts `num_id` to text representation (as a base-36 number) and
        assigns it to this Task object. Returns the string ID.

        As a public method, intended mostly for debugging/testing purposes
        since the tasks created by the user are supposed to have timestamp-based
        IDs, generated by the Task object internally.
        """
        # Surprisingly enough, Python (as of 3.8) doesn't have a built-in
        # to convert an integer to a base-36 string.
        # For negative `ts` (e.g. a dead battery in the system clock :) ),
        # the code below will produce a "36's complement" number, but we have to
        # restrict its length. Let's max it at 7 characters, which should be
        # sufficient to span the next 24 years. Yes, the IDs will wrap-around
        # every 24 years or so, but the chances of a clash with a 24-year-old
        # task are negligibly low.
        text_id = ""
        while (num_id != 0 or text_id == "") and len(text_id) < 7:
            text_id = _ID_DIGITS[num_id % 36] + text_id
            num_id //= 36

        self.id = text_id

        return text_id

    def get_full_desc(self) -> str:
        return self.summary + ("\n" + self.desc if self.desc else "")

    # TODO: not sure if we really need this. A static method that returns 
    # a tuple might be more useful.
    def set_full_desc(self, desc: str) -> None:
        paragraphs = desc.split("\n")
        self.summary = paragraphs[0]
        self.desc = "\n".join(paragraphs[1:])


    @staticmethod
    def yaml_representer(dumper: Dumper, data: "Task") -> Node:
        # Note: the order of keywords *does matter*. They will be written
        # to YAML in this order.
        filtered = {
            "status": data.status,
            "created": data.creation_date,
            "closed": data.close_date,
            "deadline": data.deadline,
            "labels": " ".join(data.labels) if len(data.labels) > 0 
                else None,
            "epic": data.epic.id if data.epic is not None 
                else None,
            "desc": data.get_full_desc(),
            "comments": data.comments if len(data.comments) > 0 
                else None
        }
        filtered = dict((k, v) for (k, v) in filtered.items() if v is not None)
        return dumper.represent_mapping('tag:yaml.org,2002:map', filtered)

    @staticmethod
    def datetime_from_yaml(value: Any) -> Optional[datetime]:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        if isinstance(value, datetime):
            return value
        # TODO: raise an exception?
        return None

    @staticmethod
    def date_from_yaml(value: Any) -> Optional[date]:
        if isinstance(value, str):
            return date.fromisoformat(value)
        if isinstance(value, date):
            return value
        # TODO: raise an exception?
        return None

    @staticmethod
    def from_plain_object(id: str, obj: Dict, epics: Dict[str, Epic]) -> "Task":
        """
        Construct a task based off a plain object read from YAML.

        We can't use YAML constructors directly because we don't save tags into
        YAML, and therefore PyYAML can't deduce object types on reading.

        Since Task can reference Epic objects, this method requires an epic pool
        to be populated beforehand, and passed to it in the epics parameter.
        """
        task = Task()
        task.id = id
        # TODO: validate the object and throw an exception (which?) if it's 
        # missing required fields. Or are all the fields optional?
        # TODO: this certainly can be beautified somehow. Also, it should
        # probably be a constructor of Task that accepts a dictionary
        if "status" in obj:
            # TODO: it can throw an exception. Should we just pass it up to the
            # caller? Then probably all other similar exceptions, too?
            task.status = TaskStatus(obj["status"])
        if "desc" in obj:
            task.set_full_desc(obj["desc"])
        if "epic" in obj:
            task.epic = epics[obj["epic"]]
        if "comments" in obj:
            # TODO: make sure it's a list
            for c in obj["comments"]:
                if "text" in c and "date" in c:
                    dt = Task.datetime_from_yaml(c["date"])
                    if dt is not None:
                        task.comments.append(TaskComment(c["text"], dt))
        if "labels" in obj:
            # TODO: make sure it's a string
            task.labels = sorted(obj["labels"].split())

        # TODO: surely it can be simplified. And less copy-paste, please.
        if "created" in obj:
            dt = Task.datetime_from_yaml(obj["created"])
            if dt is not None:
                task.creation_date = dt
        if "closed" in obj:
            dt = Task.datetime_from_yaml(obj["closed"])
            if dt is not None:
                task.close_date = dt
        if "deadline" in obj:
            d = Task.date_from_yaml(obj["deadline"])
            if d is not None:
                task.deadline = d
        return task
    
    def set_status(self, new_status: TaskStatus) -> None:
        if self.status != new_status:
            if new_status == TaskStatus.ACTIVE:
                # Going from inactive to active means reopen
                self.close_date = None
                # TODO: add a comment containing the reopen date
            else:
                # Going from active to something else: either done or cancel
                self.close_date = datetime.now()

            self.status = new_status


class TaskFilter:
    always_pass: bool
    # Words are stored in lower case in order to perform case-insensitive search
    words: List[str]
    exact_phrases: List[str]
    epic: str = ""
    labels: List[str]

    def __init__(self, query: str = "") -> None:
        self.always_pass = (query == "")
        # Query syntax:
        #   epic:<epicname> or e:epicname
        #   label:<labelname> or l:labelname
        # maybe 'created'/'closed'? what about status?
        # Quoted parts should be exact matches and should not be tied to word
        # boundaries.
        self.words = []
        self.exact_phrases = []
        self.labels = []
        for word in shlex.split(query.lower(), posix=False):
            if word[0] == '"':
                # All quoted parts should give an exact match (except they're
                # still case-insensitive), but are not necessarily tied to 
                # a word boundary.
                # When adding to the list, we're trimming off the quotes.
                self.exact_phrases.append(word[1:-1])
            else:
                handled = False
                if ':' in word:
                    keyword, value = word.split(':', 1)
                    if value != "":
                        if keyword == "e" or keyword == "epic":
                            self.epic = value
                            handled = True
                        elif keyword == "l" or keyword == "label":
                            self.labels.append(value)
                            handled = True
                # If not a known keyword, just add the word to the search list
                if not handled:
                    self.words.append(word)

    def _text_match(self, text: str) -> bool:
        lcase_text = text.lower()
        for phrase in self.exact_phrases:
            if phrase not in lcase_text:
                return False

        text_words = lcase_text.split()
        for word in self.words:
            # TODO: if search becomes too slow, optimize this piece.  Str.lower()
            # is considered inefficient in this case. We can convert the starting
            # portion to lowercase, using len(word) as the limit (but only when
            # exact_phrases are empty and therefore text doesn't need an early
            # conversion to lowercase).
            # Hmm.. actually, we need to convert to lowercase right after split(),
            # and use max of word lengths as the limit.
            if all(not t.startswith(word) for t in text_words):
                return False

        return True

    def match(self, task: Task) -> bool:
        if self.always_pass:
            return True

        # If filtering by epic, we'll remove tasks that don't belong to an epic
        if self.epic != "" and (task.epic is None or task.epic.id.lower() != self.epic):
            return False

        for label in self.labels:
            if label not in [ task_label.lower() for task_label in task.labels ]:
                return False
        
        # TODO: search in comments, too
        return self._text_match(task.summary + "\n" + task.desc)
