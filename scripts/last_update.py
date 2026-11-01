#!/usr/bin/env python3
"""Print the London date of the last successful update, or 'never'."""
import datetime
import json
import os
from zoneinfo import ZoneInfo

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "standings.json")
try:
    stamp = json.load(open(OUT))["generated"]
    when = datetime.datetime.fromisoformat(stamp).astimezone(ZoneInfo("Europe/London"))
    print(when.date())
except Exception:
    print("never")
