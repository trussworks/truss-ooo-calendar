import unittest
import main

class TestMain(unittest.TestCase):

    def test_PaylocityCSVToData(self) -> None:
        with open('test_data.csv', newline='') as csvfile:
            data = main.PaylocityCSVToData(csvfile)
        self.assertEqual(data, "test")

    def test_eventFromPaylocityCSVRow(self) -> None:
        row = ["Company:  (123456)", "GL Categor: ", "Practice: ",
               "Department: ", ": ", ": ", "Lastname, Firstname ", "000",
               "Vacation", "01/01/2000", "01/02/2000", "8.00", "100.00",
               "Taken", "Bosslast, Bossfirst"]
        testEvent = {
            "name": "Firstname Lastname",
            "type": "Vacation",
            "start_date": "01/01/2000",
            "end_date": "01/02/2000",
            "status": "Taken"
        }
        event = main.eventFromPaylocityCSVRow(row)
        self.assertEqual(event, testEvent)

    def test_nameFromPaylocityName(self) -> None:
        testName = "Lastname, Firstname "
        self.assertEqual(main.nameFromPaylocityName(testName),
                         "Firstname Lastname")

