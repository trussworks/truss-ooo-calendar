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
import argparse
import os


class TimeOffType(Enum):
    VACATION = auto()
    SICK = auto()
    SURGE = auto()
    BEREAVEMENT = auto()
    LEAVE = auto()

    @staticmethod
    # LeaveType is a string literal here because the class LeaveType isn't
    # defined yet; this is how Python implements forward references.
    def from_str(label: str) -> "TimeOffType":
        if label in ("Vacation", "Floating Holiday"):
            return TimeOffType.VACATION
        elif label in ("Sick", "COVID Childcare"):
            return TimeOffType.SICK
        elif label in ("Surge"):
            return TimeOffType.SURGE
        elif label in ("Bereavement"):
            return TimeOffType.BEREAVEMENT
        elif label in ("Military Leave", "Jury Duty"):
            return TimeOffType.LEAVE
        else:
            raise NotImplementedError("Unknown TimeOffType: " + label)


class TimeOffStatus(Enum):
    TAKEN = auto()
    CANCELED = auto()
    DECLINED = auto()
    APPROVED = auto()
    REQUESTED = auto()

    @staticmethod
    def from_str(label: str) -> "TimeOffStatus":
        if label in ("Taken"):
            return TimeOffStatus.TAKEN
        elif label in ("Cancelled"):
            return TimeOffStatus.CANCELED
        elif label in ("Declined"):
            return TimeOffStatus.DECLINED
        elif label in ("Approved"):
            return TimeOffStatus.APPROVED
        elif label in ("Submitted"):
            return TimeOffStatus.REQUESTED
        else:
            raise NotImplementedError("Unknown TimeOffStatus: " + label)


class PaylocityTimeOffEvent:
    name: str
    type: TimeOffType
    start_date: date
    end_date: date
    status: TimeOffStatus

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PaylocityTimeOffEvent):
            return NotImplemented
        return (
            self.name == other.name
            and self.type == other.type
            and self.start_date == other.start_date
            and self.end_date == other.end_date
            and self.status == other.status
        )

    @staticmethod
    def from_paylocity_time_off_row(row: list[str]) -> "PaylocityTimeOffEvent":
        # row[6] is lastname, firstname
        # row[8] is type (Vacation, Sick, etc.)
        # row[9] is the start date
        # row[10] is the end date
        # row[13] is the status (Taken, Approved, Cancelled, etc.)
        event = PaylocityTimeOffEvent()
        event.name = nameFromPaylocityName(row[6])
        event.type = TimeOffType.from_str(row[8])
        # Need timezone aware datetime. strptime doesn't let us do that
        # directly, so we use replace() to add timezone info.
        event.start_date = datetime.strptime(row[9], "%m/%d/%Y").date()
        event.end_date = datetime.strptime(row[10], "%m/%d/%Y").date()
        event.status = TimeOffStatus.from_str(row[13])
        return event


def nameFromPaylocityName(p: str) -> str:
    names = p.split(",")
    return names[1].strip() + " " + names[0].strip()


def PaylocityCSVToLeaveEvents(
    csv_file: Union[TextIO, SFTPFile]
) -> list[PaylocityTimeOffEvent]:
    csvreader = csv.reader(csv_file)
    events = []
    try:
        for row in csvreader:
            # The CSV from Paylocity has empty lines, which the
            # CSVReader "helpfully" returns as a row with 0 items.
            if len(row) < 15:
                continue
            event = PaylocityTimeOffEvent.from_paylocity_time_off_row(row)
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


def vEventFromLeaveEvent(e: PaylocityTimeOffEvent) -> Event:
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


def iCalendarFromLeaveEvents(events: list[PaylocityTimeOffEvent]) -> Calendar:
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


def main(args: argparse.Namespace) -> None:
    cal = sftpLatestPaylocityReportToCalendar(args.server, args.username, args.password)
    with open(args.ics_file, "wb") as f:
        f.write(cal.to_ical())
    exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server", action="store", default="ftp.paylocity.com", help="SFTP server"
    )
    parser.add_argument(
        "--username", action="store", default="Trussworks", help="SFTP username"
    )
    parser.add_argument(
        "--ics-file",
        action="store",
        default="output.ics",
        help="Path to output the ICS file",
    )
    parser.add_argument(
        "--password",
        action="store",
        default=os.environ["PAYLOCITY_SFTP_PASSWORD"],
        help="Password for the SFTP user",
    )
    args = parser.parse_args()
    main(args)
