#!/usr/bin/env python3
"""Fail loudly if the published goals have gone stale.

The schedule once broke silently for six weeks because every run decided it
had nothing to do and exited 0. A skipped run is only correct if the data is
already current, so this asserts that — turning a silent stall into a red X
and the failure email that goes with it.
"""
import datetime
import json
import os
import sys

MAX_AGE_DAYS = 8  # one missed Sunday is already a problem
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "standings.json")

try:
    stamp = json.load(open(OUT))["generated"]
    age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(stamp)
except Exception as exc:
    sys.exit("Could not read the last update time from %s: %s" % (OUT, exc))

days = age.total_seconds() / 86400
if days > MAX_AGE_DAYS:
    sys.exit("Goals are %.1f days old (limit %d). The weekly update is not "
             "getting through — check the gate in .github/workflows/update.yml."
             % (days, MAX_AGE_DAYS))
print("Goals are %.1f days old — fine." % days)
