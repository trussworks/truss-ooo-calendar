#! /usr/bin/env python3
"""
My Truss OOO main file.
"""

__author__ = "Mark Ferlatte <mark@truss.works>"
__version__ = "0.0.1"
__license__ = "Apache 2.0"

import csv

def nameFromPaylocityName(p: str) -> str:
    names = p.split(",")
    return names[1].strip() + " " + names[0].strip()
    
def eventFromPaylocityCSVRow(row):
    # row[6] is lastname, firstname
    # row[8] is type
    # row[9] is the start date
    # row[10] is the end date
    # row[13] is the status (Taken, Approved, Cancelled)
    event = {
        "name": nameFromPaylocityName(row[6]),
        "type": row[8],
        "start_date": row[9],
        "end_date": row[10],
        "status": row[13]
    }
    return event
    
def PaylocityCSVToData(csv_file):
    csvreader = csv.reader(csv_file)
    events = []
    try:
        for row in csvreader:
            event = eventFromPaylocityCSVRow(row)
            events.append(event)
    except csv.Error as e:
        print('line {}: {}'.format(csvreader.line_num, e))
    print(events)
    return "test"
        
def main():
    print(PaylocityCSVToData("Hello world"))

if __name__ == "__main__":
    main()
