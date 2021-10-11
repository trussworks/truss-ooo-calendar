#! /usr/bin/env python3
"""
My Truss OOO main file.
"""

__author__ = "Mark Ferlatte <mark@truss.works>"
__version__ = "0.0.1"
__license__ = "Apache 2.0"

import csv
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
    def from_str(label: str) -> 'LeaveType':
        if label in ('Vacation', 'Floating Holiday'):
            return LeaveType.VACATION
        elif label in ('Sick', 'COVID Childcare'):
            return LeaveType.SICK
        elif label in ('Surge'):
            return LeaveType.SURGE
        elif label in ('Bereavement'):
            return LeaveType.BEREAVEMENT
        elif label in ('Military Leave', 'Jury Duty'):
            return LeaveType.LEAVE
        else:
            raise NotImplementedError('Unknown LeaveType: ' + label)

class LeaveStatus(Enum):
    TAKEN = auto()
    CANCELED = auto()
    DECLINED = auto()
    APPROVED = auto()
    REQUESTED = auto()

    @staticmethod
    def from_str(label: str) -> 'LeaveStatus':
        if label in ('Taken'):
            return LeaveStatus.TAKEN
        elif label in ('Cancelled'):
            return LeaveStatus.CANCELED
        elif label in ('Declined'):
            return LeaveStatus.DECLINED
        elif label in ('Approved'):
            return LeaveStatus.APPROVED
        elif label in ('Submitted'):
            return LeaveStatus.REQUESTED
        else:
            raise NotImplementedError('Unknown LeaveStatus: ' + label)
class LeaveEvent:
    name: str
    type: LeaveType
    start_date: str
    end_date: str
    status: LeaveStatus
    
def nameFromPaylocityName(p: str) -> str:
    names = p.split(",")
    return names[1].strip() + " " + names[0].strip()
    
def eventFromPaylocityCSVRow(row: list[str]) -> LeaveEvent:
    # row[6] is lastname, firstname
    # row[8] is type
    # row[9] is the start date
    # row[10] is the end date
    # row[13] is the status (Taken, Approved, Cancelled)
    event = LeaveEvent()
    event.name = nameFromPaylocityName(row[6])
    event.type = LeaveType.from_str(row[8])
    event.start_date = row[9]
    event.end_date = row[10]
    event.status = LeaveStatus.from_str(row[13])
    
    # event = {
    #     "name": nameFromPaylocityName(row[6]),
    #     "type": LeaveType.from_str(row[8]),
    #     "start_date": row[9],
    #     "end_date": row[10],
    #     "status": LeaveStatus.from_str(row[13])
    # }
    return event
    
def PaylocityCSVToData(csv_file: TextIO) -> str:
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
        print('line {}: {}'.format(csvreader.line_num, e))
    print(events)
    return "test"
        
def main() -> None:
    with open('test_data.csv', newline='') as csvfile:
        data = PaylocityCSVToData(csvfile)
    exit(0)

if __name__ == "__main__":
    main()
