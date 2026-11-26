"""Deterministic checks for real graph execution and input boundaries.

Run from the kit: .venv/Scripts/python.exe -m unittest discover -s tests -v
These checks never make paid model requests and do not need an API key.
"""

import importlib.util
import io
import os
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

# Numbered teaching filenames are loaded by path for testing, not renamed.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import common

spec = importlib.util.spec_from_file_location("graph_lesson", ROOT / "02_langgraph_workflow.py")
graph_lesson = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_lesson)


class WorkshopTests(unittest.TestCase):
    """Check business decisions, including equality and invalid user inputs."""

    def run_graph(self, days, budget):
        """Run the actual graph offline while forbidding model configuration."""
        with patch.object(graph_lesson, "model_settings", side_effect=AssertionError("API path used")):
            with redirect_stdout(io.StringIO()):
                return graph_lesson.build_graph().invoke({
                    "destination": "Goa", "days": days, "budget": budget, "offline": True,
                })

    def test_affordable_trip_has_every_day(self):
        result = self.run_graph(3, 15000)
        self.assertEqual(result["estimated_cost"], 7500)
        self.assertIn("Day 1:", result["final_plan"])
        self.assertIn("Day 3:", result["final_plan"])
        self.assertNotIn("Day 4:", result["final_plan"])

    def test_low_budget_skips_writer(self):
        with patch.object(graph_lesson, "write_plan", side_effect=AssertionError("Writer used")):
            result = self.run_graph(3, 3000)
        self.assertIn("Try fewer days", result["final_plan"])

    def test_exact_budget_is_affordable(self):
        result = self.run_graph(3, 7500)
        self.assertIn("Day 3:", result["final_plan"])

    def test_one_rupee_below_boundary_warns(self):
        result = self.run_graph(3, 7499)
        self.assertIn("Try fewer days", result["final_plan"])

    def test_warning_path_without_offline_needs_no_model(self):
        with patch.object(graph_lesson, "model_settings", side_effect=AssertionError("API path used")):
            with redirect_stdout(io.StringIO()):
                result = graph_lesson.build_graph().invoke({
                    "destination": "Goa", "days": 3, "budget": 3000, "offline": False,
                })
        self.assertIn("Practice estimate", result["final_plan"])

    def test_day_limits_work(self):
        for days in [1, 7]:
            with self.subTest(days=days):
                result = self.run_graph(days, 100000)
                self.assertEqual(result["final_plan"].count("Day "), days)

    def test_invalid_cli_inputs_exit_before_execution(self):
        invalid = [
            ["--destination", "   "], ["--destination", "x" * 81],
            ["--days", "0"], ["--days", "8"], ["--days", "three"],
            ["--budget", "0"], ["--budget", "-1"], ["--budget", "2.5"],
        ]
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                with patch.object(sys, "argv", ["lesson"] + arguments):
                    with redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            common.read_trip()
                self.assertEqual(error.exception.code, 2)

    def test_trimmed_city_and_offline_switch(self):
        with patch.object(sys, "argv", ["lesson", "--destination", "  New Delhi  ", "--offline"]):
            trip = common.read_trip(allow_offline=True)
        self.assertEqual(trip.destination, "New Delhi")
        self.assertTrue(trip.offline)

    def test_missing_key_is_clear(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                common.model_settings()


if __name__ == "__main__":
    unittest.main()
