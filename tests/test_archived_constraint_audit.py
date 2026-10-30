import io
import unittest

from scripts.audit_archived_constraint import audit_stream, digest_start, digest_item


class ArchivedConstraintAuditTests(unittest.TestCase):
    def fixture(self, sense="E", rhs=0):
        text = (f"NAME test\nROWS\n N OBJ\n {sense} balance\n L unrelated\n"
                "COLUMNS\n x OBJ 1 balance 2\n x unrelated 1\n y balance -3\n"
                f"RHS\n rhs balance {rhs}\nBOUNDS\n FR b x\nENDATA\n")
        ordering = dict(variables=2, constraints=2)
        for kind, names in (("variable", [("x", ""), ("y", "")]),
                            ("constraint", [("balance", {"E":"=", "L":"<", "G":">"}[sense]), ("unrelated", "<")])):
            h = digest_start(kind, 2)
            for i, (name, auxiliary) in enumerate(names):
                digest_item(h, i, name, auxiliary)
            ordering[kind+"_order_digest"] = dict(sha256=h.hexdigest())
        return text, ordering

    def test_signed_activity_and_units_not_assumed(self):
        text, order = self.fixture(rhs=2)
        result = audit_stream(io.StringIO(text), [3, 1], order, 0)
        self.assertEqual(result["lhs"], 3)
        self.assertEqual(result["violation"], 1)
        self.assertEqual(result["row_magnitude"], 6)
        self.assertEqual(result["relative_violation"], 1/6)
        self.assertEqual(len(result["terms"]), 2)
        self.assertIn("NOT_ASSESSED", result["scientific_acceptance"])

    def test_sense_and_zero_rhs(self):
        for sense, expected in (("E", 3), ("L", 3), ("G", 0)):
            text, order = self.fixture(sense)
            self.assertEqual(audit_stream(io.StringIO(text), [3, 1], order, 0)["violation"], expected)

    def test_reject_wrong_order_or_missing_target(self):
        text, order = self.fixture()
        order["variable_order_digest"]["sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "ordering digest mismatch"):
            audit_stream(io.StringIO(text), [3, 1], order, 0)
        with self.assertRaisesRegex(ValueError, "Target row index absent"):
            audit_stream(io.StringIO(text), [3, 1], order, 2)

    def test_reject_ranged_and_integer_rows(self):
        text, order = self.fixture()
        with self.assertRaisesRegex(ValueError, "Ranged"):
            audit_stream(io.StringIO(text.replace("BOUNDS", "RANGES\n r balance 1\nBOUNDS")), [3, 1], order, 0)
        with self.assertRaisesRegex(ValueError, "Integer"):
            audit_stream(io.StringIO(text.replace("COLUMNS\n", "COLUMNS\n mark 'MARKER' 'INTORG'\n")), [3, 1], order, 0)


if __name__ == "__main__":
    unittest.main()
