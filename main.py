#! /usr/bin/env python3
"""
My Truss OOO main file.
"""

__author__ = "Mark Ferlatte <mark@truss.works>"
__version__ = "0.0.1"
__license__ = "Apache 2.0"

import csv
from icalendar import Calendar, Event  # type: ignore
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import TextIO, Union
from enum import Enum, auto
from uuid import uuid4
from paramiko import SSHClient, SFTPClient, SFTPFile, AutoAddPolicy


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
    start_date: date
    end_date: date
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
    # Need timezone aware datetime. strptime doesn't let us do that
    # directly, so we use replace() to add timezone info.
    event.start_date = datetime.strptime(row[9], "%m/%d/%Y").date()
    event.end_date = datetime.strptime(row[10], "%m/%d/%Y").date()
    event.status = LeaveStatus.from_str(row[13])
    return event


def PaylocityCSVToLeaveEvents(csv_file: Union[TextIO, SFTPFile]) -> list[LeaveEvent]:
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


def makeCalendar() -> Calendar:
    cal = Calendar()
    # PRODID and VERSION are required by RFC 5545
    cal.add("PRODID", "works.truss.truss-ooo-calendar")
    cal.add("VERSION", "2.0")
    return cal


def vEventFromLeaveEvent(e: LeaveEvent) -> Event:
    event = Event()
    now = datetime.now(ZoneInfo("UTC"))
    u = uuid4()
    one_day = timedelta(days=1)
    event.add("SUMMARY", e.name + " is OOO")
    event.add("DTSTART", e.start_date)
    # "All day" events have their end date be 1 day *past* where
    # the calendar event display. Ex: You're OOO from 1/1/2021
    # to 1/2/2021. The VEVENT would have a DTSTART of 1/1/2021, and a
    # DTEND of 1/3/2021.
    event.add("DTEND", e.end_date + one_day)
    event.add("DTSTAMP", now)  # Must be in UTC according to RFC 5545
    event.add("UID", u.hex)
    return event


def iCalendarFromLeaveEvents(events: list[LeaveEvent]) -> Calendar:
    cal = makeCalendar()
    for e in events:
        vevent = vEventFromLeaveEvent(e)
        cal.add_component(vevent)
    return cal


def PaylocityCSVToiCalendar(csv: Union[TextIO, SFTPFile]) -> Calendar:
    events = PaylocityCSVToLeaveEvents(csv)
    cal = iCalendarFromLeaveEvents(events)
    return cal


def sftpLatestPaylocityReportToCalendar(
    server: str, username: str, password: str
) -> Calendar:
    with SSHClient() as c:
        c.set_missing_host_key_policy(AutoAddPolicy)
        c.connect(server, username=username, password=password)
        sftp = c.open_sftp()
        files = sftp.listdir()
        # The reports are named Time_Off_Requests_20211012.csv, so sorting and taking the last item gives us the most
        # recent report.
        files.sort()
        latest_report = files[-1]
        with sftp.open(latest_report) as r:
            cal = PaylocityCSVToiCalendar(r)
            return cal


def main() -> None:
    cal = sftpLatestPaylocityReportToCalendar("ftp.paylocity.com", "Trussworks", "")
    with open("output.ics", "wb") as f:
        f.write(cal.to_ical())
    exit(0)


if __name__ == "__main__":
    main()
