import unittest
from datetime import time as dtime
import frappe
from frappe.utils import flt
from attendance_policy.tasks import get_grade


class TestLateGrading(unittest.TestCase):
	"""Test late arrival grading boundaries"""
	
	def setUp(self):
		self.settings = frappe._dict({
			"arrival_cutoff": "09:00:00",
			"grade1_end": "10:00:00",
			"grade2_end": "11:00:00",
			"second_half_cutoff": "13:30:00",
			"grade1_deduction": 0.166667,
			"grade2_deduction": 0.333333,
			"grade3_deduction": 0.5,
			"full_day_deduction": 1.0
		})
	
	def test_on_time(self):
		"""Arrival at or before 09:00 is on time"""
		grade, days = get_grade(dtime(8, 30), self.settings)
		self.assertIsNone(grade)
		self.assertEqual(days, 0)
		
		grade, days = get_grade(dtime(9, 0), self.settings)
		self.assertIsNone(grade)
		self.assertEqual(days, 0)
	
	def test_grade1_boundary(self):
		"""Grade 1: after 09:00 up to 10:00"""
		grade, days = get_grade(dtime(9, 0, 1), self.settings)
		self.assertEqual(grade, "Grade 1")
		self.assertAlmostEqual(days, 0.166667, places=4)
		
		grade, days = get_grade(dtime(9, 30), self.settings)
		self.assertEqual(grade, "Grade 1")
		
		grade, days = get_grade(dtime(10, 0), self.settings)
		self.assertEqual(grade, "Grade 1")
	
	def test_grade2_boundary(self):
		"""Grade 2: after 10:00 up to 11:00"""
		grade, days = get_grade(dtime(10, 0, 1), self.settings)
		self.assertEqual(grade, "Grade 2")
		self.assertAlmostEqual(days, 0.333333, places=4)
		
		grade, days = get_grade(dtime(10, 30), self.settings)
		self.assertEqual(grade, "Grade 2")
		
		grade, days = get_grade(dtime(11, 0), self.settings)
		self.assertEqual(grade, "Grade 2")
	
	def test_grade3_half_day(self):
		"""Grade 3: after 11:00 before 13:30"""
		grade, days = get_grade(dtime(11, 0, 1), self.settings)
		self.assertEqual(grade, "Grade 3")
		self.assertAlmostEqual(days, 0.5, places=4)
		
		grade, days = get_grade(dtime(12, 0), self.settings)
		self.assertEqual(grade, "Grade 3")
		
		grade, days = get_grade(dtime(13, 29), self.settings)
		self.assertEqual(grade, "Grade 3")
	
	def test_full_day_late(self):
		"""Arrival at or after 13:30 is full day"""
		grade, days = get_grade(dtime(13, 30), self.settings)
		self.assertEqual(grade, "Grade 3")
		self.assertEqual(days, 1.0)
		
		grade, days = get_grade(dtime(14, 0), self.settings)
		self.assertEqual(grade, "Grade 3")
		self.assertEqual(days, 1.0)


if __name__ == "__main__":
	unittest.main()
