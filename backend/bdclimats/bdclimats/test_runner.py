import os
from pathlib import Path

from django.test.runner import DiscoverRunner
import xmlrunner


class XMLTestRunner(DiscoverRunner):
    """Django test runner that writes JUnit XML via unittest-xml-reporting."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "XML_REPORT_DIR" in os.environ:
            self.output_dir = os.environ["XML_REPORT_DIR"]
        else:
            # Default to /app/reports in container to avoid backend/reports.
            self.output_dir = str(Path(__file__).resolve().parents[2] / "reports")

    def run_suite(self, suite, **kwargs):
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        runner = xmlrunner.XMLTestRunner(output=self.output_dir, verbosity=self.verbosity)
        return runner.run(suite)
