import unittest
from pathlib import Path


class VerificationWorkflowContract(unittest.TestCase):
    def test_guards(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/independent-math-evidence.yml").read_text()
        for requirement in ("gh api", "git rev-parse HEAD", "continue-on-error: true",
                            "steps.oracle.outcome", "independent_math_review", "PENDING",
                            "persist-credentials: false", "retention-days: 90",
                            "pr: 489", "pr: 472", "pr: 484"):
            self.assertIn(requirement, workflow)
        self.assertNotIn("permissions: write-all", workflow)


if __name__ == "__main__":
    unittest.main()
