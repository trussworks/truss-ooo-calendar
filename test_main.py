import unittest
import main
from datetime import datetime


class TestMain(unittest.TestCase):
    def test_PaylocityCSVToLeaveEvents(self) -> None:
        with open("test_data.csv", newline="") as csvfile:
            data = main.PaylocityCSVToLeaveEvents(csvfile)
        # We're just checking the number of rows is the same; this
        # isn't a great test but it is a decent smoke test.
        self.assertEqual(len(data), 906)

    def test_eventFromPaylocityCSVRow(self) -> None:
        row = [
            "Company:  (123456)",
            "GL Categor: ",
            "Practice: ",
            "Department: ",
            ": ",
            ": ",
            "Lastname, Firstname ",
            "000",
            "Vacation",
            "01/01/2000",
            "01/02/2000",
            "8.00",
            "100.00",
            "Taken",
            "Bosslast, Bossfirst",
        ]
        testEvent = main.LeaveEvent()
        testEvent.name = "Firstname Lastname"
        testEvent.type = main.LeaveType.VACATION
        testEvent.start_date = datetime(2000, 1, 1)
        testEvent.end_date = datetime(2000, 1, 2)
        testEvent.status = main.LeaveStatus.TAKEN
        event = main.eventFromPaylocityCSVRow(row)
        self.assertEqual(event, testEvent)

    def test_nameFromPaylocityName(self) -> None:
        testName = "Lastname, Firstname "
        self.assertEqual(main.nameFromPaylocityName(testName), "Firstname Lastname")
