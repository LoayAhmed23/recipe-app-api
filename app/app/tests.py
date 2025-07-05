from django.test import SimpleTestCase
from app import calc


class CalculationTest(SimpleTestCase):
    def test_add_numbers(self):
        res = calc.add(5, 3)
        self.assertEqual(res, 8)

    def test_subtract_numbers(self):
        res = calc.subtract(5, 3)
        self.assertEqual(res, 2)
