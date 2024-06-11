#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
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

from enum import IntEnum
import struct

from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.client import get_unique_name
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp import btp
from autopts.ptsprojects.btstack.tmap_wid import tmap_wid_hdl
from autopts.pybtp.types import Addr, AdType, Context
from autopts.utils import ResultWithFlag

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853
    TMAP = 0x1855


sink_contexts = Context.LIVE | Context.CONVERSATIONAL | Context.MEDIA | Context.RINGTONE
source_contexts = Context.LIVE | Context.CONVERSATIONAL


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("TMAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("TMAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("TMAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("TMAP", "TSPX_time_guard", "180000")
    pts.set_pixit("TMAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("TMAP", "TSPX_tester_database_file",
                  r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_TMAP_db.xml")
    pts.set_pixit("TMAP", "TSPX_mtu_size", "64")
    pts.set_pixit("TMAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("TMAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("TMAP", "TSPX_pin_code", "0000")
    pts.set_pixit("TMAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("TMAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("TMAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("TMAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("TMAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("TMAP", "TSPX_Connection_Interval", "120")
    pts.set_pixit("TMAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("TMAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("TMAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("TMAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("TMAP", "TSPX_TARGET_LATENCY", "TARGET_LOWER_LATENCY")
    pts.set_pixit("TMAP", "TSPX_TARGET_PHY", "LE_2M_PHY")


def announcements(adv_data, rsp_data, targeted):
    """Setup Announcements"""

    # CAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] = [struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]

    # BAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] += [struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, sink_contexts, source_contexts, 0) ]

    # Generate the Resolvable Set Identifier (RSI)
    # rsi = btp.cas_get_member_rsi()
    # adv_data[AdType.rsi] = struct.pack('<6B', *rsi)

    # TMAP Role: all roles supported
    tmap_role = 0x3f
    adv_data[AdType.uuid16_svc_data] += [struct.pack('<HH', Uuid.TMAP, tmap_role) ]

    stack = get_stack()
    stack.gap.ad = adv_data


def test_cases(ptses):
    """
    Returns a list of TMAP test cases
    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    adv_data, rsp_data = {}, {}

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param("TMAP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str())),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_tbs),
        TestFunc(stack.tbs_init),
        TestFunc(btp.core_reg_svc_ccp),
        TestFunc(stack.ccp_init),
        TestFunc(btp.core_reg_svc_tmap),
        TestFunc(stack.tmap_init),
        TestFunc(btp.core_reg_svc_vcp),
        TestFunc(stack.vcp_init),
        TestFunc(btp.gap_set_extended_advertising_on),
        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    general_conditions = [
        TestFunc(announcements, adv_data, rsp_data, False),
        TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data),
        TestFunc(lambda: pts.update_pixit_param("TMAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str()))
    ]

    test_case_name_list = pts.get_test_case_list('TMAP')
    tc_list = []

    custom_test_cases = [
        ZTestCase("TMAP", "TMAP/CG/VRC/BV-02-I", cmds=pre_conditions +
            [TestFunc(get_stack().synch.add_synch_element, [
             SynchPoint("TMAP/CG/VRC/BV-02-I", 20100),
             SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 20100)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 500),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 500)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 504),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 504)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 502),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 502)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 20107),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 20107)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 20110),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 20110)]),
            TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-02-I", 503),
              SynchPoint("TMAP/CG/VRC/BV-02-I_LT2", 503)]),
            ],
            generic_wid_hdl=tmap_wid_hdl, lt2="TMAP/CG/VRC/BV-02-I_LT2"),
        ZTestCase("TMAP", "TMAP/CG/VRC/BV-03-I", cmds=pre_conditions +
            [TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-03-I", 20100),
              SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 20100)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 500),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 500)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 504),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 504)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 502),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 502)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 20107),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 20107)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 20110),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 20110)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-03-I", 503),
               SynchPoint("TMAP/CG/VRC/BV-03-I_LT2", 503)]),
            ],
            generic_wid_hdl=tmap_wid_hdl, lt2="TMAP/CG/VRC/BV-03-I_LT2"),
        ZTestCase("TMAP", "TMAP/CG/VRC/BV-09-I", cmds=pre_conditions +
            [TestFunc(get_stack().synch.add_synch_element, [
              SynchPoint("TMAP/CG/VRC/BV-09-I", 20100),
              SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 20100)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 500),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 500)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 504),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 504)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 502),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 502)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 20107),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 20107)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 20110),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 20110)]),
            TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/CG/VRC/BV-09-I", 503),
               SynchPoint("TMAP/CG/VRC/BV-09-I_LT2", 503)]),
            ],
            generic_wid_hdl=tmap_wid_hdl, lt2="TMAP/CG/VRC/BV-09-I_LT2"),
        ZTestCase("TMAP", "TMAP/UMS/VRC/BV-02-I", cmds=pre_conditions +
            [TestFunc(get_stack().synch.add_synch_element, [
               SynchPoint("TMAP/UMS/VRC/BV-02-I", 20100),
               SynchPoint("TMAP/UMS/VRC/BV-02-I_LT2", 20100)]),
            TestFunc(get_stack().synch.add_synch_element, [
                SynchPoint("TMAP/UMS/VRC/BV-02-I", 521),
                SynchPoint("TMAP/UMS/VRC/BV-02-I_LT2", 521)]),
            ],
            generic_wid_hdl=tmap_wid_hdl, lt2="TMAP/UMS/VRC/BV-02-I_LT2"),
        # TMAP/*/DDI/*
        ZTestCase("TMAP", "TMAP/CG/DDI/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/DDI/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/UMS/DDI/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/BMS/DDI/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/BMR/DDI/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        # TMAP/UMR/*
        ZTestCase("TMAP", "TMAP/UMR/VRC/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/UMR/ASC/BV-04-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/UMR/ASC/BV-05-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/UMR/ASC/BV-06-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-01-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-02-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-03-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-04-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-05-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
        ZTestCase("TMAP", "TMAP/CT/VRC/BV-06-I", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=tmap_wid_hdl),
    ]

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('TMAP', tc_name, cmds=pre_conditions,
                             generic_wid_hdl=tmap_wid_hdl)

        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break
        tc_list.append(instance)

    if len(ptses) < 2:
        return tc_list

    pts2 = ptses[1]

    pre_conditions_lt2 = [
        TestFunc(lambda: pts2.update_pixit_param(
            "CAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("TMAP", "TMAP/CG/VRC/BV-02-I_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=tmap_wid_hdl),
        ZTestCaseSlave("TMAP", "TMAP/CG/VRC/BV-03-I_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=tmap_wid_hdl),
        ZTestCaseSlave("TMAP", "TMAP/CG/VRC/BV-09-I_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=tmap_wid_hdl),
        ZTestCaseSlave("TMAP", "TMAP/UMS/VRC/BV-02-I_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=tmap_wid_hdl),
    ]

    return tc_list + test_cases_lt2
