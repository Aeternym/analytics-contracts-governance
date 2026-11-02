import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from contracts_governance.validator import validate_directory
from contracts_governance.cli import main


class ValidatorTest(unittest.TestCase):
    def copy_catalog(self, target: Path) -> None:
        root = Path(__file__).resolve().parents[1] / "examples" / "contracts"
        for source in root.rglob("*.md"):
            copied = target / source.relative_to(root)
            copied.parent.mkdir(parents=True, exist_ok=True)
            copied.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def test_synthetic_catalog_passes(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "contracts"
        report = validate_directory(root)
        self.assertEqual("PASS", report["verdict"], report["issues"])
        self.assertEqual(6, report["contracts_parsed"])

    def test_unknown_reference_fails(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "contracts"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.copy_catalog(target)
            metric = target / "metrics" / "MET-0002-demo-repeat-orders.md"
            metric.write_text(metric.read_text(encoding="utf-8").replace("[MET-0001]", "[MET-9999]"), encoding="utf-8")
            report = validate_directory(target)
            self.assertEqual("NOT_READY", report["verdict"])
            self.assertTrue(any(item["rule"] == "reference" for item in report["issues"]))

    def test_missing_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist"
            report = validate_directory(missing)
            self.assertEqual("NOT_READY", report["verdict"])
            self.assertTrue(any(item["rule"] == "source_missing" for item in report["issues"]))

    def test_missing_directory_cli_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does-not-exist"
            with redirect_stdout(StringIO()):
                exit_code = main([str(missing)])
            self.assertNotEqual(0, exit_code)

    def test_empty_directory_fails_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_directory(Path(tmp))
            self.assertEqual("NOT_READY", report["verdict"])
            self.assertTrue(any(item["rule"] == "empty_catalog" for item in report["issues"]))

    def test_empty_directory_can_be_explicitly_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_directory(Path(tmp), allow_empty=True)
            self.assertEqual("PASS", report["verdict"], report["issues"])
            self.assertEqual(0, report["contracts_parsed"])

    def test_reference_type_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.copy_catalog(target)
            metric = target / "metrics" / "MET-0001-demo-completed-orders.md"
            metric.write_text(
                metric.read_text(encoding="utf-8").replace("dimension_ids: [DIM-0001]", "dimension_ids: [SEG-0001]"),
                encoding="utf-8",
            )
            report = validate_directory(target)
            self.assertTrue(any(item["rule"] == "reference_type" for item in report["issues"]))

    def test_owner_reference_must_point_to_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.copy_catalog(target)
            dimension = target / "dimensions" / "DIM-0001-demo-channel.md"
            dimension.write_text(
                dimension.read_text(encoding="utf-8").replace("owner_id: OWNER-0001", "owner_id: MET-0001"),
                encoding="utf-8",
            )
            report = validate_directory(target)
            self.assertTrue(any(item["rule"] == "reference_type" for item in report["issues"]))

    def test_duplicate_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.copy_catalog(target)
            source = target / "metrics" / "MET-0001-demo-completed-orders.md"
            duplicate = target / "metrics" / "MET-0001-duplicate.md"
            duplicate.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            report = validate_directory(target)
            self.assertTrue(any(item["rule"] == "unique_id" for item in report["issues"]))

    def test_invalid_status_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.copy_catalog(target)
            metric = target / "metrics" / "MET-0002-demo-repeat-orders.md"
            metric.write_text(metric.read_text(encoding="utf-8").replace("status: draft", "status: active"), encoding="utf-8")
            report = validate_directory(target)
            self.assertTrue(any(item["rule"] == "status" for item in report["issues"]))


if __name__ == "__main__":
    unittest.main()

