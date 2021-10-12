#! /usr/bin/env python3
"""
My Truss OOO main file.
"""

__author__ = "Mark Ferlatte <mark@truss.works>"
__version__ = "0.0.1"
__license__ = "Apache 2.0"

import csv
from icalendar import Calendar, Event  # type: ignore
from datetime import datetime
from typing import TextIO
from enum import Enum, auto


class LeaveType(Enum):
    VACATION = auto()
    SICK = auto()
    SURGE = auto()
    BEREAVEMENT = auto()
    LEAVE = auto()

    @staticmethod
    # LeaveType is a string literal here because the class LeaveType isn't
    # defined yet; this is how Python implements forward references.
    def from_str(label: str) -> "LeaveType":
        if label in ("Vacation", "Floating Holiday"):
            return LeaveType.VACATION
        elif label in ("Sick", "COVID Childcare"):
            return LeaveType.SICK
        elif label in ("Surge"):
            return LeaveType.SURGE
        elif label in ("Bereavement"):
            return LeaveType.BEREAVEMENT
        elif label in ("Military Leave", "Jury Duty"):
            return LeaveType.LEAVE
        else:
            raise NotImplementedError("Unknown LeaveType: " + label)


class LeaveStatus(Enum):
    TAKEN = auto()
    CANCELED = auto()
    DECLINED = auto()
    APPROVED = auto()
    REQUESTED = auto()

    @staticmethod
    def from_str(label: str) -> "LeaveStatus":
        if label in ("Taken"):
            return LeaveStatus.TAKEN
        elif label in ("Cancelled"):
            return LeaveStatus.CANCELED
        elif label in ("Declined"):
            return LeaveStatus.DECLINED
        elif label in ("Approved"):
            return LeaveStatus.APPROVED
        elif label in ("Submitted"):
            return LeaveStatus.REQUESTED
        else:
            raise NotImplementedError("Unknown LeaveStatus: " + label)


class LeaveEvent:
    name: str
    type: LeaveType
    start_date: datetime
    end_date: datetime
    status: LeaveStatus

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LeaveEvent):
            return NotImplemented
        return (
            self.name == other.name
            and self.type == other.type
            and self.start_date == other.start_date
            and self.end_date == other.end_date
            and self.status == other.status
        )


def nameFromPaylocityName(p: str) -> str:
    names = p.split(",")
    return names[1].strip() + " " + names[0].strip()


def eventFromPaylocityCSVRow(row: list[str]) -> LeaveEvent:
    # row[6] is lastname, firstname
    # row[8] is type (Vacation, Sick, etc.)
    # row[9] is the start date
    # row[10] is the end date
    # row[13] is the status (Taken, Approved, Cancelled, etc.)
    event = LeaveEvent()
    event.name = nameFromPaylocityName(row[6])
    event.type = LeaveType.from_str(row[8])
    event.start_date = datetime.strptime(row[9], "%m/%d/%Y")
    event.end_date = datetime.strptime(row[10], "%m/%d/%Y")
    event.status = LeaveStatus.from_str(row[13])
    return event


def PaylocityCSVToLeaveEvents(csv_file: TextIO) -> list[LeaveEvent]:
    csvreader = csv.reader(csv_file)
    events = []
    try:
        for row in csvreader:
            # The CSV from Paylocity has empty lines, which the
            # CSVReader "helpfully" returns as a row with 0 items.
            if len(row) < 15:
                continue
            event = eventFromPaylocityCSVRow(row)
            events.append(event)
    except csv.Error as e:
        print("line {}: {}".format(csvreader.line_num, e))
    return events


def main() -> None:
    with open("test_data.csv", newline="") as csvfile:
        data = PaylocityCSVToLeaveEvents(csvfile)
    exit(0)


if __name__ == "__main__":
    main()
