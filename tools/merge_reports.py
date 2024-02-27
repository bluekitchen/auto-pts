#!/usr/bin/env python
import os
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

# date format for XML fields
date_format_xml = "%A, %B %d, %Y, %H:%M:%S"

# date format for filenames
date_format_files = '%Y_%m_%d_%H_%M_%S'

# processing instruction in report header
report_header = '''
<?xml-stylesheet type='text/css' href='file:///C:\\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\\bin\\ReportStylesheet.css'?>
<?xml-stylesheet type='text/css' href='http://www.bluetooth.org/pts/ref/ReportStylesheetWeb.css'?>
'''

def find_report_files(project, folder):
    testreport_xml_path = None
    report_xml_path = None
    report_zip_path = None
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file.startswith("TestReport_" + project):
                testreport_xml_path = file
            if file.startswith("Report_" + project) and file.endswith(".xml"):
                report_xml_path = file
            if file.startswith("Report_" + project) and file.endswith(".zip"):
                report_zip_path = file
    else:
        print(f"Folder '{folder}' does not exist.")
    return testreport_xml_path, report_xml_path, report_zip_path


def get_datetime_from_filename(filename):
    string = filename.replace(".xml", "")
    parts = string.split('_')
    datetime_str = '_'.join(parts[2:])
    datetime_obj = datetime.strptime(datetime_str, date_format_files)
    return datetime_obj


def get_tests_from_testreport(testreport_xml_path):
    tests = []
    tree = ET.parse(testreport_xml_path)
    root = tree.getroot()
    testcases = root.find('TestCases')
    for testcase in testcases:
        verdict = None
        name = None
        date = None
        for desc in testcase.iter():
            if desc.tag == 'Name':
                name = desc.text
            if desc.tag == "Verdict":
                verdict = desc.text
            if desc.tag == "Date":
                date = datetime.strptime(desc.text, date_format_xml)
        if verdict == "PASS":
            tests.append((name, date))
    return tests


def print_tests():
    global name, latest_date, folder
    print("%-30s| %-25s| %-10s" % ("Test name", "Latest passing run", "Folder"))
    print("-" * 69)
    for name in sorted(latest_tests.keys()):
        latest_date, folder = latest_tests[name]
        print("%-30s| %-25s| %s" % (name, latest_date, folder))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Merge PTS reports for a given <project>")
        print("Usage: ./%s <project> <path/to/report-folder> [<path/to/report-folder>] ..." % sys.argv[0])
        sys.exit(1)

    # command line params
    the_project = sys.argv[1].upper()
    report_folders = sys.argv[2:]

    if the_project in report_folders:
        print("Merged report will be stored in %s, please avoid %s for report folders" % (the_project, the_project))
        sys.exit(1)

    # first pass over report folders:
    # - get all reports files
    # - find latest report
    # - get latest passing testcases
    reports = {}
    latest_folder = None
    latest_datetime = None
    latest_tests = {}
    for folder in report_folders:
        testreport_xml_path, report_xml_path, report_zip_path = find_report_files(the_project, folder)
        if testreport_xml_path is None:
            print("Cannot find TestReport_*.xml")
            continue
        if report_xml_path is None:
            print("Cannot find Report_*.xml")
            continue
        if report_zip_path is None:
            print("Cannot find Report_*.zip")
            continue

        reports[folder] = testreport_xml_path, report_xml_path, report_zip_path

        # latest report
        datetime = get_datetime_from_filename(testreport_xml_path)
        if latest_datetime is None or datetime > latest_datetime:
            latest_folder = folder
            latest_datetime = datetime

        # get tests
        print("[-] Get passing tests from", testreport_xml_path)
        tests = get_tests_from_testreport(folder + "/" + testreport_xml_path)

        # cache latest test
        for (name, date) in tests:
            if name in latest_tests:
                latest_date, report_folder = latest_tests[name]
                if latest_date > date:
                    continue
            latest_tests[name] = (date, folder)

    # get tests cases from summary lists and results in report xml
    summary_test_cases = {}
    results_test_cases = {}
    tests_missing = []
    for folder in report_folders:
        report_xml_path = folder + "/" + reports[folder][1]
        print("[-] Get Summary List from", report_xml_path)
        tree = ET.parse(report_xml_path)
        root = tree.getroot()
        test_case_summary_found = False
        test_case_results_found = False
        for element in root:
            if element.tag == "SECTION_HEADER":
                if element.text == "Summary List of All Performed Test Cases":
                    test_case_summary_found = True
                if element.text == "Test case results":
                    test_case_results_found = True
            if test_case_summary_found and element.tag == "TABLE":
                test_case_summary_found = False
                for row in element.findall("./ROW"):
                    name = row.find("./TEXT").text
                    if name in latest_tests:
                        test_folder = latest_tests[name][1]
                        if test_folder == folder:
                            summary_test_cases[name] = row
            if test_case_results_found and element.tag == "RESULTS":
                # each test case has two tables
                test_case_results_found = False
                first_table = None
                name = None
                datetime_obj = None
                for table in element.findall("./TABLE"):
                    if first_table is None:
                        first_table = table
                        # get name and date
                        name = table.find(".//TEST_CASE_ID").text
                        datetime_str = table.find(".//RESULTS_TEXT").text
                        datetime_obj = datetime.strptime(datetime_str, date_format_xml)
                    else:
                        # check if we need it
                        if name in latest_tests:
                            test_datetime, test_folder = latest_tests[name]
                            if test_folder == folder and test_datetime == datetime_obj:
                                results_test_cases[name] = first_table, table
                        else:
                            if name not in tests_missing:
                                tests_missing.append(name)
                        first_table = None

    # get tests cases from testreport xml
    test_report_test_cases = {}
    for folder in report_folders:
        testreport_xml_path = folder + "/" + reports[folder][0]
        print("[-] Get Testcases from", testreport_xml_path)
        tree = ET.parse(testreport_xml_path)
        root = tree.getroot()
        testcases = root.find('TestCases')
        for testcase in testcases:
            date = None
            name = None
            for desc in testcase.iter():
                if desc.tag == 'Name':
                    name = desc.text
                if desc.tag == "Verdict":
                    verdict = desc.text
                if desc.tag == "Date":
                    date = datetime.strptime(desc.text, date_format_xml)
            if name is not None and name in latest_tests:
                test_datetime, test_folder = latest_tests[name]
                if test_folder == folder and test_datetime == date:
                    test_report_test_cases[name] = testcase

    # re-create output folder
    output_folder = the_project
    print("[-] Create Output folder", output_folder)
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.mkdir(output_folder)

    # merge Report_PROJECT_DATE.xml
    # - remove existing test cases and add merged set
    # - write to file
    report_xml_path = latest_folder + "/" + reports[latest_folder][1]
    tree = ET.parse(report_xml_path)
    root = tree.getroot()
    test_case_summary_found = False
    test_case_results_found = False
    for element in root:
        if element.tag == "SECTION_HEADER":
            if element.text == "Summary List of All Performed Test Cases":
                test_case_summary_found = True
            if element.text == "Test case results":
                test_case_results_found = True
        if test_case_summary_found and element.tag == "TABLE":
            test_case_summary_found = False
            for row in element.findall("./ROW"):
                element.remove(row)
            for row_name in sorted(summary_test_cases.keys()):
                row = summary_test_cases[row_name]
                element.append(row)
        if test_case_results_found and element.tag == "RESULTS":
            # each test case has two tables
            test_case_results_found = False
            for table in element.findall("./TABLE"):
                element.remove(table)
            for name in sorted(results_test_cases.keys()):
                first_table, second_table = results_test_cases[name]
                element.append(first_table)
                element.append(second_table)
    output_report_xml_file = output_folder + "/" + reports[latest_folder][1]
    print("[-] Create Report XML", output_report_xml_file)
    report_xml_data = report_header + ET.tostring(root, encoding="unicode")
    with open(output_report_xml_file, "wt") as f:
        f.write(report_xml_data)

    # merge Report_PROJECT_DATE.zip
    # - copy individual test case folders into archive;
    # - add report xml file
    output_zip = output_folder + "/" + reports[latest_folder][2]
    print("[-] Create Report ZIP", output_zip)
    with zipfile.ZipFile(output_zip, 'w') as output_zipfile:
        for folder in report_folders:
            testreport_zip_path = folder + "/" + reports[folder][2]
            with zipfile.ZipFile(testreport_zip_path, 'r') as input_zipfile:
                for name in latest_tests.keys():
                    latest_date, latest_folder = latest_tests[name]
                    if latest_folder == folder:
                        test_folder = (name + "_" + latest_date.strftime(date_format_files)).replace('/','_').replace('-','_')
                        files_in_folder = [f for f in input_zipfile.namelist() if f.startswith(test_folder)]
                        for file in files_in_folder:
                            with input_zipfile.open(file) as input_file:
                                output_zipfile.writestr(file, input_file.read())
        output_zipfile.writestr(reports[latest_folder][1], report_xml_data)

    # merge TestReport_PROJECT_DATE.xml
    testreport_xml_path = latest_folder + "/" + reports[latest_folder][0]
    tree = ET.parse(testreport_xml_path)
    root = tree.getroot()
    testcases = root.find('TestCases')
    for testcase in testcases.findall('TestCase'):
        testcases.remove(testcase)
    for name in sorted(test_report_test_cases.keys()):
        testcases.append(test_report_test_cases[name])
    output_testreport_xml_file = output_folder + "/" + reports[latest_folder][0]
    print("[-] Create TestReport XML", output_testreport_xml_file)
    tree.write(output_testreport_xml_file)

    # list passing tests
    print()
    print_tests()

    # list missing tests
    print()
    print("Missing tests")
    print("-" * 25)
    for test in sorted(tests_missing):
        print(test)

    print()
    print("=" * 20)
    print("Passing test: ", len(latest_tests))
    print("Missing tests:", len(tests_missing))
    print("=" * 20)
