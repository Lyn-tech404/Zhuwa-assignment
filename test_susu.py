import unittest
from decimal import Decimal
from susu import SusuGroup

class TestSusuGroup(unittest.TestCase):

    def test_create_group_and_add_members(self):
        # Test valid instantiation and uniqueness constraint
        group = SusuGroup("50.00")
        group.add_member("Ama")
        group.add_member("Kofi")
        
        self.assertEqual(len(group.members), 2)
        with self.assertRaises(ValueError):
            group.add_member("Ama")  # Duplicate check

    def test_reject_invalid_inputs(self):
        group = SusuGroup("50.00")
        group.add_member("Ama")
        
        # Test negative payment validation
        with self.assertRaises(ValueError):
            group.record_contribution("Ama", "-10.00")
            
        # Test overpayment validation
        with self.assertRaises(ValueError):
            group.record_contribution("Ama", "60.00")
            
        # Test unknown member validation
        with self.assertRaises(ValueError):
            group.record_contribution("Unknown", "20.00")

    def test_partial_payment_allowed(self):
        group = SusuGroup("50.00")
        group.add_member("Esi")
        
        # Verify initial state and partial payment behavior
        group.record_contribution("Esi", "30.00")
        report = group.get_report()
        self.assertEqual(report["owes_what"]["Esi"], Decimal("20.00"))

    def test_week_cannot_close_if_balances_incomplete(self):
        group = SusuGroup("50.00")
        group.add_member("Ama")
        group.add_member("Kofi")
        
        group.record_contribution("Ama", "50.00")
        group.record_contribution("Kofi", "30.00") # Kofi paid partially
        
        success, msg = group.close_week()
        self.assertFalse(success)
        self.assertIn("Kofi owes 20.00 GHS", msg)
        self.assertEqual(group.current_week, 1) # Must remain on week 1

    def test_successful_week_closure_and_rotation(self):
        group = SusuGroup("50.00")
        group.add_member("Ama")
        group.add_member("Kofi")
        
        # Week 1: Everyone pays in full
        group.record_contribution("Ama", "50.00")
        group.record_contribution("Kofi", "50.00")
        
        success, msg = group.close_week()
        self.assertTrue(success)
        self.assertEqual(group.current_week, 2)
        
        # Verify first joined (Ama) gets the pot
        report = group.get_report()
        self.assertEqual(len(report["payout_history"]), 1)
        self.assertEqual(report["payout_history"][0]["member"], "Ama")
        self.assertEqual(report["payout_history"][0]["amount"], Decimal("100.00"))

    def test_no_rounding_errors_with_decimals(self):
        # Validating absolute exactness with fractional currency representations
        group = SusuGroup("33.33")
        group.add_member("Ama")
        group.add_member("Kofi")
        group.add_member("Esi")
        
        group.record_contribution("Ama", "11.11")
        group.record_contribution("Ama", "22.22") # Exactly 33.33
        
        report = group.get_report()
        self.assertIn("Ama", report["paid_in_full"])

if __name__ == "__main__":
    unittest.main()
