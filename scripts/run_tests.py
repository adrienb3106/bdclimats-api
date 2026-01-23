import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
LOG_PATH = REPORT_DIR / "test-report.txt"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

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
    "cd /app/bdclimats && python manage.py test -v 2 --testrunner=bdclimats.test_runner.XMLTestRunner",
]

start = time.time()
proc = subprocess.run(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)
end = time.time()

output = proc.stdout.replace("\x00", "")
status = "OK" if proc.returncode == 0 else "FAILED"

header = f"== Test run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ==\nStatus: {status}\nExit code: {proc.returncode}\n\n"
LOG_PATH.write_text(header + output, encoding="utf-8")

print(f"Log written to {LOG_PATH}")
print(f"JUnit XML written to {REPORT_DIR} (xmlrunner output)")

sys.exit(proc.returncode)
