import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from xml.dom import minidom

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
LOG_PATH = REPORT_DIR / "test-report.txt"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

parser = argparse.ArgumentParser(description="Run tests (optional coverage).")
parser.add_argument("--coverage", action="store_true", help="Enable coverage reporting.")
args = parser.parse_args()

if args.coverage:
    cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        "-e",
        "XML_REPORT_DIR=/app/reports",
        "-e",
        "COVERAGE_FILE=/app/reports/.coverage",
        "web",
        "sh",
        "-lc",
        "cd /app/bdclimats && "
        "coverage run --rcfile /app/.coveragerc -m pytest "
        "--junitxml /app/reports/TEST-pytest.xml; "
        "status=$?; "
        "coverage xml --rcfile /app/.coveragerc -o /app/reports/coverage.xml; "
        "coverage html --rcfile /app/.coveragerc -d /app/reports/htmlcov; "
        "coverage report --rcfile /app/.coveragerc; "
        "exit $status",
    ]
else:
    cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        "-e",
        "XML_REPORT_DIR=/app/reports",
        "web",
        "sh",
        "-lc",
        "cd /app/bdclimats && pytest --junitxml /app/reports/TEST-pytest.xml",
    ]

start = time.time()
proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
end = time.time()

output = proc.stdout.replace("\x00", "")
status = "OK" if proc.returncode == 0 else "FAILED"

header = f"== Test run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==\nStatus: {status}\nExit code: {proc.returncode}\n\n"
LOG_PATH.write_text(header + output, encoding="utf-8")

# Pretty-print XML reports if present.
for xml_path in (REPORT_DIR / "TEST-pytest.xml",):
    if not xml_path.exists():
        continue
    try:
        pretty = minidom.parse(str(xml_path)).toprettyxml(indent="  ")
        xml_path.write_text(pretty, encoding="utf-8")
    except Exception:
        pass

print(f"Log written to {LOG_PATH}")
print(f"JUnit XML written to {REPORT_DIR} (pytest output)")
if args.coverage:
    print(f"Coverage XML written to {REPORT_DIR / 'coverage.xml'}")
    print(f"Coverage HTML written to {REPORT_DIR / 'htmlcov' / 'index.html'}")

sys.exit(proc.returncode)
