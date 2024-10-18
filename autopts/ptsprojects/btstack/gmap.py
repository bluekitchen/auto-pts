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
import struct

from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.ptsprojects.btstack.gmap_wid import gmap_wid_hdl
from autopts.client import get_unique_name
from autopts.pybtp.types import Addr, AdType
from autopts.utils import ResultWithFlag

from enum import IntEnum


class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853
    GMAS = 0x1858


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

    "GMAP/UGG/MXLT/BV-67-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-68-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-33-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-34-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-35-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-36-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-136-C": (311, 311),
    "GMAP/UGG/MXLT/BV-137-C": (311, 311),
    "GMAP/UGG/MXLT/BV-138-C": (311, 311),
    "GMAP/UGG/MXLT/BV-139-C": (311, 311),
    "GMAP/UGG/MXLT/BV-69-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-70-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-09-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-10-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-49-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-50-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-11-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-12-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-71-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-72-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-144-C": (311, 311),
    "GMAP/UGG/MXLT/BV-145-C": (311, 311),
    "GMAP/UGG/MXLT/BV-146-C": (311, 311),
    "GMAP/UGG/MXLT/BV-147-C": (311, 311),
    "GMAP/UGG/MXLT/BV-75-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-76-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-17-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-18-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-53-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-54-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-19-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-20-C":  (311, 311),
    "GMAP/UGG/MXLT/BV-180-C": (311, 311),
    "GMAP/UGG/MXLT/BV-181-C": (311, 311),
    "GMAP/UGG/MXLT/BV-182-C": (311, 311),
    "GMAP/UGG/MXLT/BV-183-C": (311, 311),
    "GMAP/UGG/MXLT/BV-184-C": (311, 311),
    "GMAP/UGG/MXLT/BV-185-C": (311, 311),
    "GMAP/UGG/MXLT/BV-186-C": (311, 311),
    "GMAP/UGG/MXLT/BV-187-C": (311, 311),
    "GMAP/UGG/MXLT/BV-188-C": (311, 311),
    "GMAP/UGG/MXLT/BV-189-C": (311, 311),
}

test_cases_with_audio_locations = {
    "GMAP/BGR/AL/BV-01-C": 1,
    "GMAP/BGR/AL/BV-02-C": 2,
    "GMAP/BGR/AL/BV-03-C": 3,
}

def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("GMAP", "TSPX_time_guard", "180000")
    pts.set_pixit("GMAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("GMAP", "TSPX_delete_ltk", "TRUE")


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
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
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
        TestFunc(btp.gap_set_extended_advertising_on),
        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    # Setup Advertising Data for UGT
    adv_data, rsp_data = {}, {}
    # - Incomplete UUIDs: ASCS
    adv_data[AdType.uuid16_some] = [struct.pack('<H', Uuid.ASCS)]
    # - Service Data: ASCS { Targeted Announcement, Sink Contexts, Source Contexts, Metadata]
    # - Service Data: GMAS { Role ]
    adv_data[AdType.uuid16_svc_data] = [struct.pack('<HBHHB', Uuid.ASCS, 0x01, 0x000d, 0x000d, 0)] + [struct.pack('<HB', Uuid.GMAS, 0x0f)]
    setup_advertising = [TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data)]

    test_case_name_list = pts.get_test_case_list('GMAP')
    tc_list = []

    for tc_name in test_case_name_list:
        if tc_name in test_cases_with_lt2:
            # For test case with 2 LTs, specify the correct WID to sync
            tc_name_lt2 = tc_name + "_LT2"
            wid_lt1, wid_lt2 = test_cases_with_lt2[tc_name]
            instance = ZTestCase('GMAP', tc_name,
                                 cmds=pre_conditions +
                                      sync_commands_for_wid_list(tc_name, [(20100, 20100), (20106, 20106), (wid_lt1, wid_lt2)]),
                                 generic_wid_hdl=gmap_wid_hdl, lt2=tc_name_lt2)
        elif (tc_name.startswith("GMAP/UGT")
              or tc_name.startswith("GMAP/SR")
              or 'DDI' in tc_name):
            # For tests where we're peripheral, enable advertisements
            instance = ZTestCase('GMAP', tc_name, cmds=pre_conditions + setup_advertising, generic_wid_hdl=gmap_wid_hdl)
        elif tc_name in test_cases_with_audio_locations:
            locations = test_cases_with_audio_locations[tc_name];
            set_sink_location = [TestFunc(btp.pacs_set_location, 1, locations)]
            instance = ZTestCase('GMAP', tc_name, cmds=pre_conditions + setup_advertising + set_sink_location, generic_wid_hdl=gmap_wid_hdl)
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
