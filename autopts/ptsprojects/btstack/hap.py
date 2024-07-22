#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Oticon.
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

"""HAP test cases"""
from enum import IntEnum
import struct

from autopts.pybtp import btp
from autopts.client import get_unique_name
from autopts.ptsprojects.stack import get_stack, SynchPoint
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.hap_wid import hap_wid_hdl
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.pybtp.types import Addr, AdType, Context
from autopts.pybtp.defs import HAS_TSPX_available_presets_indices, \
                               HAS_TSPX_unavailable_presets_indices
from autopts.utils import ResultWithFlag

# Options aligned with the overlay-le-audio.conf options
BTP_HAP_HA_OPTS_DEFAULT = (btp.defs.HAP_HA_OPT_PRESETS_DYNAMIC |
                           btp.defs.HAP_HA_OPT_PRESETS_WRITABLE)
BTP_HAP_HA_OPTS_BINAURAL = (btp.defs.HAP_HA_OPT_PRESETS_INDEPENDENT |
                            btp.defs.HAP_HA_OPT_PRESETS_DYNAMIC |
                            btp.defs.HAP_HA_OPT_PRESETS_WRITABLE)

class Uuid(IntEnum):
    ASCS = 0x184E
    BASS = 0x184F
    PACS = 0x1850
    BAAS = 0x1852
    CAS  = 0x1853


def set_pixits(ptses):
    """Setup HAP profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""

    preset_indices = HAS_TSPX_available_presets_indices + HAS_TSPX_unavailable_presets_indices
    max_index = max([0] + preset_indices)
    num_presets = len(preset_indices)

    pts = ptses[0]

    pts.set_pixit("HAP", "TSPX_bd_addr_iut", "DEADBEEFDEAD")
    pts.set_pixit("HAP", "TSPX_Public_bd_addr_LT2", "000000000000")
    pts.set_pixit("HAP", "TSPX_iut_device_name_in_adv_packet_for_random_address", "")
    pts.set_pixit("HAP", "TSPX_time_guard", "180000")
    pts.set_pixit("HAP", "TSPX_use_implicit_send", "TRUE")
    pts.set_pixit("HAP", "TSPX_tester_database_file",
        r"C:\Program Files (x86)\Bluetooth SIG\Bluetooth PTS\Data\SIGDatabase\PTS_HAS_db.xml")
    pts.set_pixit("HAP", "TSPX_mtu_size", "64")
    pts.set_pixit("HAP", "TSPX_secure_simple_pairing_pass_key_confirmation", "FALSE")
    pts.set_pixit("HAP", "TSPX_delete_link_key", "FALSE")
    pts.set_pixit("HAP", "TSPX_pin_code", "0000")
    pts.set_pixit("HAP", "TSPX_use_dynamic_pin", "FALSE")
    pts.set_pixit("HAP", "TSPX_delete_ltk", "TRUE")
    pts.set_pixit("HAP", "TSPX_security_enabled", "TRUE")
    pts.set_pixit("HAP", "TSPX_iut_ATT_transport", "ATT Bearer on LE Transport")
    pts.set_pixit("HAP", "TSPX_sirk", "838E680553F1415AA265BBAFC6EA03B8")
    pts.set_pixit("HAP", "TSPX_Connection_Interval", "120")
    pts.set_pixit("HAP", "TSPX_Extended_Adv_Interval_min", "1200")
    pts.set_pixit("HAP", "TSPX_Extended_Adv_Interval_max", "1200")
    pts.set_pixit("HAP", "TSPX_Periodic_Adv_Interval_min", "600")
    pts.set_pixit("HAP", "TSPX_Periodic_Adv_Interval_max", "600")
    pts.set_pixit("HAP", "TSPX_TARGET_LATENCY", "TARGET_LOWER_LATENCY")
    pts.set_pixit("HAP", "TSPX_TARGET_PHY", "LE_2M_PHY")
    pts.set_pixit("HAP", "TSPX_largest_preset_index", str(max_index))
    pts.set_pixit("HAP", "TSPX_num_presets", str(num_presets))


def announcements(advData, targeted):
    """
        CAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] = [ struct.pack('<HB', Uuid.CAS, 1 if targeted else 0) ]
    """
        BAP General/Targeted Announcement
    """
    advData[AdType.uuid16_svc_data] += [ struct.pack('<HBHHB', Uuid.ASCS, 1 if targeted else 0, \
        Context.LIVE | Context.MEDIA, Context.LIVE, 0) ]
    """
        RSI
    """
    # rsi = btp.cas_get_member_rsi()
    # advData[AdType.rsi] = struct.pack('<6B', *rsi)


test_cases_binaural = [
    'HAP/HA/DISC/BV-01-C',
    'HAP/HA/DISC/BV-05-C',
]

test_cases_banded = [
    'HAP/HA/DISC/BV-02-C',
    'HAP/HA/DISC/BV-06-C',
]

def test_cases(ptses):
    """Returns a list of HAP Server test cases"""

    pts = ptses[0]

    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    advData = {}

    # declare iut_addr as a kind of future
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
        TestFunc(btp.core_reg_svc_mics),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(stack.pacs_init),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(stack.ascs_init),
        TestFunc(btp.core_reg_svc_vcs),
        TestFunc(btp.core_reg_svc_cas),
        TestFunc(btp.core_reg_svc_ias),
        TestFunc(stack.ias_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_hap),
        # TODO: This list is getting quite long. Consider some refactor.
        TestFunc(stack.hap_init),
        TestFunc(lambda: pts.update_pixit_param("HAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),

        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    adv_conditions = [
        TestFunc(announcements, advData, True),
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(btp.gap_adv_ind_on, ad=advData),
    ]

    pre_conditions_ha_binaural = pre_conditions + adv_conditions + [
        TestFunc(btp.hap_ha_init,
                 btp.defs.HAP_HA_TYPE_BINAURAL,
                 BTP_HAP_HA_OPTS_BINAURAL),
    ]

    pre_conditions_ha_banded = pre_conditions + [
        TestFunc(btp.hap_ha_init,
                 btp.defs.HAP_HA_TYPE_BANDED,
                 BTP_HAP_HA_OPTS_DEFAULT),
    ]

    pre_conditions_harc = pre_conditions + [
        TestFunc(btp.hap_harc_init),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_gatt),
    ]

    pre_conditions_hauc = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_pacs),
        TestFunc(stack.pacs_init),
        TestFunc(btp.core_reg_svc_ascs),
        TestFunc(stack.ascs_init),
        TestFunc(btp.core_reg_svc_bap),
        TestFunc(stack.bap_init),
        TestFunc(btp.core_reg_svc_cap),
        TestFunc(stack.cap_init),
        TestFunc(btp.core_reg_svc_hap),
        TestFunc(stack.hap_init),
        TestFunc(lambda: pts.update_pixit_param("HAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
        TestFunc(btp.hap_hauc_init),
        TestFunc(btp.core_reg_svc_csip),
        TestFunc(stack.csip_init),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_cl_init),

        # Gives a signal to the LT2 to continue its preconditions
        TestFunc(lambda: set_addr(stack.gap.iut_addr_get_str())),
    ]

    pre_conditions_iac = pre_conditions + [
        TestFunc(btp.hap_iac_init),
    ]

    test_case_name_list = pts.get_test_case_list('HAP')
    tc_list = []

    custom_test_cases = [
        ZTestCase("HAP", "HAP/HAUC/DISC/BV-01-C", cmds=pre_conditions_hauc +
                     [TestFunc(get_stack().synch.add_synch_element, [
                         SynchPoint("HAP/HAUC/DISC/BV-01-C", 20100),
                         SynchPoint("HAP/HAUC/DISC/BV-01-C_LT2", 20100)]),
                      TestFunc(get_stack().synch.add_synch_element, [
                          SynchPoint("HAP/HAUC/DISC/BV-01-C", 20106),
                          SynchPoint("HAP/HAUC/DISC/BV-01-C_LT2", 20106)]),
                      TestFunc(get_stack().synch.add_synch_element, [
                          SynchPoint("HAP/HAUC/DISC/BV-01-C", 20105),
                          SynchPoint("HAP/HAUC/DISC/BV-01-C_LT2", 20105)]),
                      TestFunc(get_stack().synch.add_synch_element, [
                          SynchPoint("HAP/HAUC/DISC/BV-01-C", 481),
                          SynchPoint("HAP/HAUC/DISC/BV-01-C_LT2", 481)]),
                      # After WID 481, ID 474 on LT1 asks to confirm the previous operations
                      ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HAUC/DISC/BV-01-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/DISC/BV-01-C", cmds=pre_conditions_harc +
                   [TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/DISC/BV-01-C", 20100),
                       SynchPoint("HAP/HARC/DISC/BV-01-C_LT2", 20100)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/DISC/BV-01-C", 20106),
                        SynchPoint("HAP/HARC/DISC/BV-01-C_LT2", 20106)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/DISC/BV-01-C", 20105),
                        SynchPoint("HAP/HARC/DISC/BV-01-C_LT2", 20105)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/DISC/BV-01-C", 481),
                        SynchPoint("HAP/HARC/DISC/BV-01-C_LT2", 481)]),
                    # After WID 481, ID 474 on LT1 asks to confirm the previous operations
                    ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/DISC/BV-01-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-02-C", cmds=pre_conditions_harc +
                   [TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-02-C", 20100),
                       SynchPoint("HAP/HARC/PRE/BV-02-C_LT2", 20100)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/PRE/BV-02-C", 20106),
                        SynchPoint("HAP/HARC/PRE/BV-02-C_LT2", 20106)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/PRE/BV-02-C", 20105),
                        SynchPoint("HAP/HARC/PRE/BV-02-C_LT2", 20105)]),
                    TestFunc(get_stack().synch.add_synch_element, [
                        SynchPoint("HAP/HARC/PRE/BV-02-C", 462),
                        SynchPoint("HAP/HARC/PRE/BV-02-C_LT2", 462)]),
                    # After WID 462, ID 474 on LT1 asks to confirm the previous operations
                    ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-02-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-03-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-03-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-03-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-03-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-03-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-03-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-03-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-03-C", 469),
                       SynchPoint("HAP/HARC/PRE/BV-03-C_LT2", 490)]),
                   # After WID 469, ID 474 on LT1 asks to confirm the previous operations
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-03-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-04-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-04-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-04-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-04-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-04-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-04-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-04-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-04-C", 463),
                       SynchPoint("HAP/HARC/PRE/BV-04-C_LT2", 463)]),
                   # After WID 463, ID 474 on LT1 asks to confirm the previous operations
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-04-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-05-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-05-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-05-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-05-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-05-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-05-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-05-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-05-C", 470),
                       SynchPoint("HAP/HARC/PRE/BV-05-C_LT2", 490)]),
                   # After WID 470, ID 474 on LT1 asks to confirm the previous operations
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-05-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-06-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-06-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-06-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-06-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-06-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-06-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-06-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-06-C", 464),
                       SynchPoint("HAP/HARC/PRE/BV-06-C_LT2", 464)]),
                   # After WID 464, ID 474 on LT1 asks to confirm the previous operations
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-06-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-07-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-07-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-07-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-07-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-07-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-07-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-07-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-07-C", 471),
                       SynchPoint("HAP/HARC/PRE/BV-07-C_LT2", 471)]),
                   # After WID 471, ID 474 on LT1 asks to confirm the previous operations
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-07-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-13-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-13-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-13-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-13-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-13-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-13-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-13-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-13-C", 465),
                       SynchPoint("HAP/HARC/PRE/BV-13-C_LT2", 465)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-13-C", 468),
                       SynchPoint("HAP/HARC/PRE/BV-13-C_LT2", 468)]),
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-13-C_LT2"
                  ),
        ZTestCase("HAP", "HAP/HARC/PRE/BV-18-C", cmds=pre_conditions_harc +
                  [TestFunc(get_stack().synch.add_synch_element, [
                      SynchPoint("HAP/HARC/PRE/BV-18-C", 20100),
                      SynchPoint("HAP/HARC/PRE/BV-18-C_LT2", 20100)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-18-C", 20106),
                       SynchPoint("HAP/HARC/PRE/BV-18-C_LT2", 20106)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-18-C", 20105),
                       SynchPoint("HAP/HARC/PRE/BV-18-C_LT2", 20105)]),
                   TestFunc(get_stack().synch.add_synch_element, [
                       SynchPoint("HAP/HARC/PRE/BV-18-C", 473),
                       SynchPoint("HAP/HARC/PRE/BV-18-C_LT2", 473)]),
                   ], generic_wid_hdl=hap_wid_hdl, lt2="HAP/HARC/PRE/BV-18-C_LT2"
                  ),
    ]

    for tc_name in test_case_name_list:
        if tc_name.startswith('HAP/HA/'):
            if tc_name == 'HAP/HA/STR/BV-02-C':
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions + [
                                         TestFunc(btp.hap_ha_init,
                                                  btp.defs.HAP_HA_TYPE_BINAURAL,
                                                  BTP_HAP_HA_OPTS_BINAURAL),
                                     ],
                                     generic_wid_hdl=hap_wid_hdl)
            elif tc_name in test_cases_banded:
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions_ha_banded,
                                     generic_wid_hdl=hap_wid_hdl)
            else:
                # fallback to binaural
                instance = ZTestCase("HAP", tc_name,
                                     cmds=pre_conditions_ha_binaural,
                                     generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/HARC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_harc,
                                 generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/HAUC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_hauc,
                                 generic_wid_hdl=hap_wid_hdl)
        elif tc_name.startswith('HAP/IAC/'):
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions_iac,
                                 generic_wid_hdl=hap_wid_hdl)
        else:
            instance = ZTestCase("HAP", tc_name,
                                 cmds=pre_conditions,
                                 generic_wid_hdl=hap_wid_hdl)

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
            "HAP", "TSPX_bd_addr_iut", iut_addr.get(timeout=90))),
        TestFunc(btp.set_lt2_addr, pts2.q_bd_addr, Addr.le_public),
    ]

    test_cases_lt2 = [
        ZTestCaseSlave("HAP", "HAP/HAUC/DISC/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/DISC/BV-01-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-02-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-03-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-04-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-05-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-06-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-07-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-08-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-09-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-10-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-13-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
        ZTestCaseSlave("HAP", "HAP/HARC/PRE/BV-18-C_LT2",
                       cmds=pre_conditions_lt2,
                       generic_wid_hdl=hap_wid_hdl),
    ]

    return tc_list + test_cases_lt2
