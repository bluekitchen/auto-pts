#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
# Copyright (c) 2023, Codecoup.
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

"""CAP test cases"""
from enum import IntEnum, IntFlag
import struct

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.cap_wid import cap_wid_hdl
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave, ZTestCaseSlave2
from autopts.pybtp.defs import PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL, PACS_AUDIO_CONTEXT_TYPE_MEDIA
from autopts.pybtp.types import Addr, AdType, Context
from autopts.utils import ResultWithFlag

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853


def set_pixits(ptses):
    """Setup CAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of PTS.

    ptses -- list of PyPTS instances"""

    pts = ptses[0]

    pts.set_pixit("CAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("CAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("CAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("CAP", "TSPX_time_guard", "180000")
    pts.set_pixit("CAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("CAP", "TSPX_tester_database_file",
                  r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_BASS_db.xml")
    pts.set_pixit("CAP", "TSPX_mtu_size", "64")
    pts.set_pixit("CAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("CAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("CAP", "TSPX_pin_code", "0000")
    pts.set_pixit("CAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("CAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("CAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("CAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("CAP", "TSPX_TARGET_ASE_CHARACTERISTIC", "SINK_ASE")
    pts.set_pixit("CAP", "TSPX_TARGET_LATENCY", "TARGET_BALANCED_LATENCY_RELIABILITY")
    pts.set_pixit("CAP", "TSPX_TARGET_PHY", "LE_2M_PHY")
    pts.set_pixit("CAP", "TSPX_Codec_ID", "0600000000")
    pts.set_pixit("CAP", "TSPX_VS_Codec_Specific_Configuration", "0001")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Framing", "UNFRAMING")
    pts.set_pixit("CAP", "TSPX_VS_QoS_PHY", "2M_PHY")
    pts.set_pixit("CAP", "TSPX_VS_QoS_SDU_Interval", "64")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Max_SDU", "10000")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Retransmission_Number", "2")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Max_Transport_Latency", "40")
    pts.set_pixit("CAP", "TSPX_VS_QoS_Presentation_Delay", "40000")
    pts.set_pixit("CAP", "TSPX_VS_Company_ID", "0000")
    pts.set_pixit("CAP", "TSPX_VS_Codec_ID", "0000")
    pts.set_pixit("CAP", "TSPX_METADATA_SELECTION", "USE_IXIT_VALUE_FOR_METADATA")
    pts.set_pixit("CAP", "TSPX_METADATA_SINK", "03020200")
    pts.set_pixit("CAP", "TSPX_METADATA_SOURCE", "03020200")
    pts.set_pixit("CAP", "TSPX_broadcast_code", "0102680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CAP", "TSPX_Sync_Timeout", "20000")
    pts.set_pixit("CAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("CAP", "TSPX_STREAMING_DATA_CONFIRMATION_METHOD", "By Playing")
    pts.set_pixit("CAP", "TSPX_CONTEXT_TYPE", "0002")
    pts.set_pixit("CAP", "TSPX_Connection_Interval", "80")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("CAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("CAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("CAP", "TSPX_BST_CODEC_CONFIG", "8_1_1")

    if len(ptses) < 2:
        return

    pts2 = ptses[1]
    pts2.set_pixit("CAP", "TSPX_CONTEXT_TYPE", "0002")

    if len(ptses) < 3:
        return

    pts3 = ptses[2]
    pts3.set_pixit("CAP", "TSPX_CONTEXT_TYPE", "0002")

sink_contexts = Context.LIVE | Context.CONVERSATIONAL | Context.MEDIA | Context.RINGTONE
source_contexts = Context.LIVE | Context.CONVERSATIONAL


def announcements(adv_data, rsp_data, targeted):
    """Setup Announcements"""

    # CAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] = [struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]

    # BAP General/Targeted Announcement
    adv_data[AdType.uuid16_svc_data] += [struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, sink_contexts, source_contexts, 0) ]

    # Generate the Resolvable Set Identifier (RSI)
    # rsi = btp.cas_get_member_rsi()
    # adv_data[AdType.rsi] = struct.pack('<6B', *rsi)

    stack = get_stack()
    stack.gap.ad = adv_data


def test_cases(ptses):
    """Returns a list of CAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    adv_data, rsp_data = {}, {}

    iut_addr = ResultWithFlag()

    def set_addr(addr):
        iut_addr.set(addr)

    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(stack.gatt_init),
        TestFunc(btp.gap_set_conn),
        TestFunc(btp.gap_set_gendiscov),
        TestFunc(btp.core_reg_svc_aics),
        TestFunc(stack.aics_init),
        TestFunc(btp.core_reg_svc_vcp),
        TestFunc(stack.vcp_init),
        TestFunc(btp.core_reg_svc_micp),
        TestFunc(stack.micp_init),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.ascs_init),
        TestFunc(stack.bap_init),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(btp.gap_set_extended_advertising_on),
        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    general_conditions = [
        TestFunc(announcements, adv_data, rsp_data, False),
        TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data),
        TestFunc(lambda: pts.update_pixit_param("CAP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str()))
    ]

    targeted_conditions = [
        TestFunc(announcements, adv_data, rsp_data, True),
        TestFunc(btp.gap_adv_ind_on, ad=adv_data, sd=rsp_data),
        TestFunc(lambda: pts.update_pixit_param("CAP", "TSPX_bd_addr_iut",
                                                stack.gap.iut_addr_get_str()))
    ]

    set_audio_contexts = [
        TestFunc(btp.pacs_set_supported_contexts,
                 PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                 PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL),
        TestFunc(btp.pacs_set_available_contexts,
                 PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL,
                 PACS_AUDIO_CONTEXT_TYPE_CONVERSATIONAL)
    ]

    custom_test_cases = [
        ZTestCase("CAP", "CAP/INI/ERR/BI-01-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/COM/ERR/BI-01-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),

        ZTestCase("CAP", "CAP/CL/ADV/BV-01-C", cmds=pre_conditions + general_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-01-C", cmds=pre_conditions + set_audio_contexts + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-02-C", cmds=pre_conditions + set_audio_contexts + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-03-C", cmds=pre_conditions + set_audio_contexts + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/ACC/ERR/BI-04-C", cmds=pre_conditions + set_audio_contexts + targeted_conditions,
                  generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-01-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 405),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 400),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-01-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-01-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-01-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-02-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 405),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 400),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-02-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-02-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-02-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-03-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 405),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 400),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-03-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-03-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-03-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-04-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 405),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 400),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-04-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-04-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-04-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-05-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 405),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 400),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-05-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-05-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-05-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-06-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 405),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 400),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-06-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-06-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-06-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-07-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 405),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 400),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-07-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-07-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-07-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-08-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 405),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 400),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-08-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-08-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-08-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-09-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 405),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 400),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-09-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-09-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-09-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-10-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 405),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 400),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-10-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-10-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-10-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-11-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 405),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 400),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-11-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-11-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-11-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-12-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 405),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 400),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-12-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-12-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-12-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-13-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 405),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 400),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-13-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-13-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-13-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-14-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 405),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 400),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-14-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-14-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-14-C_LT2"),

        ZTestCase("CAP", "CAP/INI/UST/BV-15-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-16-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-17-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-18-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-19-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-20-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-21-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-22-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-23-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-24-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-25-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-26-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-27-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/UST/BV-28-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),

        ZTestCase("CAP", "CAP/INI/UST/BV-29-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 405),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 400),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-29-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-29-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-29-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-30-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 405),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 400),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-30-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-30-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-30-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-31-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 405),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 400),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-31-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-31-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-31-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-32-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 405),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 419),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 310),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-32-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-32-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-32-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-33-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 405),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 419),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 310),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-33-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-33-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-33-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-34-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 405),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 419),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-34-C", 310),
                       SynchPoint("CAP/INI/UST/BV-34-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-34-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-34-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-34-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-35-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 405),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 419),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-35-C", 310),
                       SynchPoint("CAP/INI/UST/BV-35-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-35-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-35-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-35-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-36-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 405),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 419),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("CAP/INI/UST/BV-36-C", 310),
                       SynchPoint("CAP/INI/UST/BV-36-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-36-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-36-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-36-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-37-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 405),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 419),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 419)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 310),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 310)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-37-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-37-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-37-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-40-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 405),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 400),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 312),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 309),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 309)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-40-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-40-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-40-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-41-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 405),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 400),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 312),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-41-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-41-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-41-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UST/BV-42-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 20100),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 405),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 400),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 312),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 312)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 309),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 309)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UST/BV-42-C", 20115),
                      SynchPoint("CAP/INI/UST/BV-42-C_LT2", 20115)]),
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UST/BV-42-C_LT2"),
        ZTestCase("CAP", "CAP/COM/BST/BV-01-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-01-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-01-C_LT2", 20100),
                     SynchPoint("CAP/COM/BST/BV-01-C_LT3", 100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-01-C", 405),
                      SynchPoint("CAP/COM/BST/BV-01-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-01-C", 345),
                      SynchPoint("CAP/COM/BST/BV-01-C_LT2", 345),
                      SynchPoint("CAP/COM/BST/BV-01-C_LT3", 384)]),   # 376 (confirm received audio) must run after both 345 (add source)
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-01-C_LT2", lt3="CAP/COM/BST/BV-01-C_LT3"),
        ZTestCase("CAP", "CAP/COM/BST/BV-02-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-02-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-02-C_LT2", 20100),
                     SynchPoint("CAP/COM/BST/BV-02-C_LT3", 100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-02-C", 405),
                      SynchPoint("CAP/COM/BST/BV-02-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-02-C", 345),
                      SynchPoint("CAP/COM/BST/BV-02-C_LT2", 345),
                      SynchPoint("CAP/COM/BST/BV-02-C_LT3", 384)]), # 376 (confirm received audio) must run after both 345 (add source)
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-02-C_LT2", lt3="CAP/COM/BST/BV-02-C_LT3"),
        ZTestCase("CAP", "CAP/COM/BST/BV-03-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-03-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-03-C_LT2", 100)
                 ]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-03-C", 347),
                      SynchPoint("CAP/COM/BST/BV-03-C_LT2", 384)])
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-03-C_LT2",),
        ZTestCase("CAP", "CAP/COM/BST/BV-04-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-04-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-04-C_LT2", 100)
                 ]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-04-C", 347),
                      SynchPoint("CAP/COM/BST/BV-04-C_LT2", 384)])
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-04-C_LT2", ),
        ZTestCase("CAP", "CAP/COM/BST/BV-05-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-05-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-05-C_LT2", 100)
                 ]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-05-C", 345),
                      SynchPoint("CAP/COM/BST/BV-05-C_LT2", 384)])
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-05-C_LT2", ),
        ZTestCase("CAP", "CAP/COM/BST/BV-06-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/BST/BV-06-C", 20100),
                     SynchPoint("CAP/COM/BST/BV-06-C_LT2", 20100),
                     SynchPoint("CAP/COM/BST/BV-06-C_LT3", 100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-06-C", 405),
                      SynchPoint("CAP/COM/BST/BV-06-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/BST/BV-06-C", 345),
                      SynchPoint("CAP/COM/BST/BV-06-C_LT2", 345),
                      SynchPoint("CAP/COM/BST/BV-06-C_LT3", 384)]),   # 376 (confirm received audio) must run after both 345 (add source)
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/BST/BV-06-C_LT2", lt3="CAP/COM/BST/BV-06-C_LT3"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-01-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-01-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-01-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-01-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-01-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-01-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-01-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-01-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-03-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-03-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-03-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-03-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-03-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-03-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-03-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-03-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-04-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-04-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-04-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-04-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-04-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-04-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-04-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-04-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-05-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-05-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-05-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-05-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-05-C_LT2", 405)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-05-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-06-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-06-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-06-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-06-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-06-C_LT2", 405)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-06-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-07-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-07-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-07-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-07-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-07-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-07-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-07-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-07-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-08-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-08-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-08-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-08-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-08-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-08-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-08-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-08-C_LT2"),
        ZTestCase("CAP", "CAP/COM/CRC/BV-09-C", cmds=pre_conditions +
                 [TestFunc(get_stack().synch.add_synch_element, [
                     SynchPoint("CAP/COM/CRC/BV-09-C", 20100),
                     SynchPoint("CAP/COM/CRC/BV-09-C_LT2", 20100)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-09-C", 405),
                      SynchPoint("CAP/COM/CRC/BV-09-C_LT2", 405)]),
                  TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/COM/CRC/BV-09-C", 20110),
                      SynchPoint("CAP/COM/CRC/BV-09-C_LT2", 20110)]),
                  ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/COM/CRC/BV-09-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UTB/BV-01-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-01-C", 20100),
                      SynchPoint("CAP/INI/UTB/BV-01-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-01-C", 405),
                      SynchPoint("CAP/INI/UTB/BV-01-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-01-C", 400),
                      SynchPoint("CAP/INI/UTB/BV-01-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-01-C", 406),
                      SynchPoint("CAP/INI/UTB/BV-01-C_LT2", 406)])
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UTB/BV-01-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UTB/BV-02-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-02-C", 20100),
                      SynchPoint("CAP/INI/UTB/BV-02-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-02-C", 405),
                      SynchPoint("CAP/INI/UTB/BV-02-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-02-C", 400),
                      SynchPoint("CAP/INI/UTB/BV-02-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-02-C", 406),
                      SynchPoint("CAP/INI/UTB/BV-02-C_LT2", 406)])
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UTB/BV-02-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UTB/BV-03-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-03-C", 20100),
                      SynchPoint("CAP/INI/UTB/BV-03-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-03-C", 405),
                      SynchPoint("CAP/INI/UTB/BV-03-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-03-C", 400),
                      SynchPoint("CAP/INI/UTB/BV-03-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-03-C", 406),
                      SynchPoint("CAP/INI/UTB/BV-03-C_LT2", 406)])
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UTB/BV-03-C_LT2"),
        ZTestCase("CAP", "CAP/INI/UTB/BV-04-C", cmds=pre_conditions +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-04-C", 20100),
                      SynchPoint("CAP/INI/UTB/BV-04-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-04-C", 405),
                      SynchPoint("CAP/INI/UTB/BV-04-C_LT2", 405)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-04-C", 400),
                      SynchPoint("CAP/INI/UTB/BV-04-C_LT2", 400)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("CAP/INI/UTB/BV-04-C", 406),
                      SynchPoint("CAP/INI/UTB/BV-04-C_LT2", 406)])
                   ],
                  generic_wid_hdl=cap_wid_hdl, lt2="CAP/INI/UTB/BV-04-C_LT2"),
        ZTestCase("CAP", "CAP/INI/BTU/BV-01-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
        ZTestCase("CAP", "CAP/INI/BTU/BV-02-C", cmds=pre_conditions, generic_wid_hdl=cap_wid_hdl),
    ]
    test_case_name_list = pts.get_test_case_list('CAP')
    tc_list = []

    for tc_name in test_case_name_list:

        instance = ZTestCase("CAP", tc_name,
                             cmds=pre_conditions + targeted_conditions,
                             generic_wid_hdl=cap_wid_hdl)

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
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-06-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-07-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-08-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-09-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-10-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-11-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-12-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-13-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-14-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-29-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-30-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-31-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-32-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-33-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-34-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-35-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-36-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-37-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-40-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-41-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UST/BV-42-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/BST/BV-06-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-06-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-07-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-08-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/COM/CRC/BV-09-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UTB/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UTB/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UTB/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave("CAP", "CAP/INI/UTB/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=cap_wid_hdl),
    ]

    if len(ptses) < 3:
        return tc_list + test_cases_lt2

    pts3 = ptses[2]

    pre_conditions_lt3 = [
        TestFunc(lambda: pts3.update_pixit_param(
            "CAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90))),
        TestFunc(btp.set_lt3_addr, pts3.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt3 = [
        ZTestCaseSlave2("CAP", "CAP/COM/BST/BV-01-C_LT3",
                       cmds=pre_conditions_lt3,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave2("CAP", "CAP/COM/BST/BV-02-C_LT3",
                       cmds=pre_conditions_lt3,
                       generic_wid_hdl=cap_wid_hdl),
        ZTestCaseSlave2("CAP", "CAP/COM/BST/BV-06-C_LT3",
                        cmds=pre_conditions_lt3,
                        generic_wid_hdl=cap_wid_hdl),
    ]

    return tc_list + test_cases_lt2 + test_cases_lt3
