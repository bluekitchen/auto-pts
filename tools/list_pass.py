#!/usr/bin/env python
import sys
import xml.etree.ElementTree as ET
from datetime import datetime


# date format for "01/30/2024 16:30:10"
date_format = "%m/%d/%Y %H:%M:%S"

def get_tests(tc_log):
    tests = []

    tree = ET.parse(tc_log)
    root = tree.getroot()

    for tcase in root:
        verdict = "FAIL"
        log  = None
        name = None
        date = None
        for desc in tcase.iter():
            if desc.tag == 'NAME':
                name = desc.text
            if desc.tag == "VERDICT":
                verdict = desc.text
            if desc.tag == "LOG":
                log = desc.text
            if desc.tag == "DATE":
                date = date1 = datetime.strptime(desc.text, date_format)
        if verdict == "PASS":
            tests.append((name, date, log))
    return tests

def print_tests(project, workspaces):
    latest_tests = {}
    for workspace in workspaces:
        tc_log = workspace + "/" + project + "/tc_log.xml"
        tests = get_tests(tc_log)
        for (name, date, log) in tests:
            if name in latest_tests:
                latest_date, latest_log, _ = latest_tests[name]
                if latest_date > date:
                    continue
            latest_tests[name] = (date, log, workspace)
    for name in sorted(latest_tests.keys()):
        latest_date, latest_log, workspace = latest_tests[name]
        print("%-30s %25s %s" % (name, latest_date, workspace))

if __name__ == "__main__":
    # Check if the user provided the XML file name as a command-line argument
    if len(sys.argv) < 3:
        print("List passing tests in set of PTS Workspaces for a given <project>")
        print("Usage: ./%s <project> <path/to/workspace> [<path/to/workspace>] ..." % sys.argv[0])
        sys.exit(1)
    
    project = sys.argv[1].upper()
    workspaces = sys.argv[2:]
    print_tests(project, workspaces)
