import unittest
import main

class TestMain(unittest.TestCase):

    def test_PaylocityCSVToData(self):
        csv_string = "TESTSTRING"
        self.assertEqual(main.PaylocityCSVToData(csv_string), csv_string)

        
