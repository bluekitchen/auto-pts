#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.ptsprojects.btstack.gmap_wid import gmap_wid_hdl
from autopts.client import get_unique_name
from autopts.pybtp.types import Addr
from autopts.utils import ResultWithFlag


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("GMAP", "TSPX_time_guard", "180000")
    pts.set_pixit("GMAP", "TSPX_use_implicit_send", "TRUE")


def sync_commands_for_wid_list(tc_name, wids):
    cmds = []
    tc_name_lt2 = tc_name + "_LT2"
    for (wid_lt1, wid_lt2) in  wids:
        cmds += [TestFunc(get_stack().synch.add_synch_element, [
                    SynchPoint(tc_name, wid_lt1),
                    SynchPoint(tc_name_lt2, wid_lt2)])]
    return cmds


def test_cases(ptses):
    """
    Returns a list of GMAP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # declare iut_addr as a kind of future
    iut_addr = ResultWithFlag()
    def set_addr(addr):
        iut_addr.set(addr)

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "GMAP", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(stack.pacs_init),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(stack.ascs_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_gmap),
        TestFunc(stack.gmap_init),
        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    test_case_name_list = pts.get_test_case_list('GMAP')
    tc_list = []

    test_cases_with_lt2 = {
        # tc_name: (wid lt1, wid lt2)
        "GMAP/UGG/LLU/BV-75-C":  (311, 311),
        "GMAP/UGG/LLU/BV-76-C":  (311, 311),
        "GMAP/UGG/LLU/BV-05-C":  (311, 311),
        "GMAP/UGG/LLU/BV-06-C":  (311, 311),
        "GMAP/UGG/LLU/BV-07-C":  (311, 311),
        "GMAP/UGG/LLU/BV-08-C":  (311, 311),
        "GMAP/UGG/LLU/BV-97-C":  (313, 313),
        "GMAP/UGG/LLU/BV-98-C":  (313, 313),
        "GMAP/UGG/LLU/BV-99-C":  (313, 313),
        "GMAP/UGG/LLU/BV-100-C": (313, 313),
        "GMAP/UGG/LLU/BV-41-C":  (313, 313),
        "GMAP/UGG/LLU/BV-42-C":  (313, 313),
        "GMAP/UGG/LLU/BV-21-C":  (313, 313),
        "GMAP/UGG/LLU/BV-22-C":  (313, 313),
        "GMAP/UGG/LLU/BV-23-C":  (313, 313),
        "GMAP/UGG/LLU/BV-24-C":  (313, 313),
        "GMAP/UGG/LLU/BV-25-C":  (313, 313),
        "GMAP/UGG/LLU/BV-26-C":  (313, 313),
        "GMAP/UGG/LLU/BV-77-C":  (313, 313),
        "GMAP/UGG/LLU/BV-78-C":  (313, 313),
        "GMAP/UGG/LLU/BV-105-C": (313, 311),
        "GMAP/UGG/LLU/BV-106-C": (313, 311),
        "GMAP/UGG/LLU/BV-107-C": (313, 311),
        "GMAP/UGG/LLU/BV-108-C": (313, 311),
        "GMAP/UGG/LLU/BV-81-C":  (313, 311),
        "GMAP/UGG/LLU/BV-82-C":  (313, 311),
        "GMAP/UGG/LLU/BV-33-C":  (311, 313),
        "GMAP/UGG/LLU/BV-34-C":  (311, 313),
        "GMAP/UGG/LLU/BV-35-C":  (311, 313),
        "GMAP/UGG/LLU/BV-36-C":  (311, 313),
        "GMAP/UGG/LLU/BV-37-C":  (311, 313),
        "GMAP/UGG/LLU/BV-38-C":  (311, 313),
        "GMAP/UGG/LLU/BV-113-C": (313, 313),
        "GMAP/UGG/LLU/BV-114-C": (313, 313),
        "GMAP/UGG/LLU/BV-115-C": (313, 313),
        "GMAP/UGG/LLU/BV-116-C": (313, 313),
        "GMAP/UGG/LLU/BV-85-C":  (313, 313),
        "GMAP/UGG/LLU/BV-86-C":  (313, 313),
        "GMAP/UGG/LLU/BV-45-C":  (313, 313),
        "GMAP/UGG/LLU/BV-46-C":  (313, 313),
        "GMAP/UGG/LLU/BV-49-C":  (313, 313),
        "GMAP/UGG/LLU/BV-50-C":  (313, 313),
    }

    # For test case with 2 LTs, specify the correct WID to sync
    for tc_name in test_case_name_list:
        if tc_name in test_cases_with_lt2:
            tc_name_lt2 = tc_name + "_LT2"
            wid_lt1, wid_lt2 = test_cases_with_lt2[tc_name]
            instance = ZTestCase('GMAP', tc_name,
                                 cmds=pre_conditions +
                                      sync_commands_for_wid_list(tc_name, [(20100, 20100), (20106, 20106), (wid_lt1, wid_lt2)]),
                                 generic_wid_hdl=gmap_wid_hdl, lt2=tc_name_lt2)
        else:
            instance = ZTestCase('GMAP', tc_name, cmds=pre_conditions, generic_wid_hdl=gmap_wid_hdl)
        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
        TestFunc(lambda: pts2.update_pixit_param(
            "GMAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    # Test cases LT2
    for tc_name in test_cases_with_lt2.keys():
        tc_name_lt2 = tc_name + "_LT2"
        tc_list.append(ZTestCaseSlave("GMAP", tc_name_lt2,
                           cmds=pre_conditions_lt2,
                           generic_wid_hdl=gmap_wid_hdl))

    return tc_list
