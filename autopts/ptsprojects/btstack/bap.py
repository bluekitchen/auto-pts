"""BAP test cases"""

from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap, AdType, AdFlags, Prop, Perm, UUID
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.ztestcase import ZTestCase
from autopts.ptsprojects.btstack.bap_wid import bap_wid_hdl
from autopts.ptsprojects.stack import get_stack
from autopts.client import get_unique_name

ut_device_name = 'Tester'.encode('utf-8')
iut_manufacturer_data = 'ABCD'
iut_appearance = '1111'
iut_svc_data = '1111'
iut_flags = '04'
iut_svcs = '1111'
iut_attr_db_off = 0x000b

def set_pixits(ptses):
    """Setup profile PIXITS for workspace. Those values are used for test
    case if not updated within test case.

    PIXITS always should be updated accordingly to project and newest version of
    PTS.

    ptses -- list of PyPTS instances"""
    pts = ptses[0]

    # Set BAP common PIXIT values

    # Needed to pass BAP/UCL/SCC/BV-033-C, BAP/UCL/SCC/BV-034-C, ..
    pts.set_pixit("BAP", "TSPX_Codec_ID", "FF00000000")

def test_cases(ptses):
    """Returns a list of GAP test cases
    ptses -- list of PyPTS instances"""

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr

    stack = get_stack()

    iut_device_name = get_unique_name(pts)

    pre_conditions = [
        TestFunc(stack.gap_init, iut_device_name,
                 iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags,
                 iut_svcs),
        TestFunc(stack.le_audio_init),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
            "BAP", "TSPX_bd_addr_iut",
            stack.gap.iut_addr_get_str())),
        TestFunc(lambda: pts.update_pixit_param(
            "BAP", "TSPX_delete_link_key", "TRUE")),

        # We do this on test case, because previous one could update
        # this if RPA was used by PTS
        # TODO: Get PTS address type
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public)
    ]

    custom_test_cases = []

    # provide codec configuration for BAP/UCL/SCC/BV-001-C - BAP/UCL/SCC/BV-032-C
    # PTS 8.3 shows frequency and frame duration, but not octets per frame
    test_codec_configurations = [
        ("BAP/UCL/SCC/BV-001-C", "8_1"),
        ("BAP/UCL/SCC/BV-002-C", "8_2"),
        ("BAP/UCL/SCC/BV-003-C", "16_1"),
        ("BAP/UCL/SCC/BV-004-C", "16_2"),
        ("BAP/UCL/SCC/BV-005-C", "24_1"),
        ("BAP/UCL/SCC/BV-006-C", "24_2"),
        ("BAP/UCL/SCC/BV-007-C", "32_1"),
        ("BAP/UCL/SCC/BV-008-C", "32_2"),
        ("BAP/UCL/SCC/BV-009-C", "441_1"),
        ("BAP/UCL/SCC/BV-010-C", "441_2"),
        ("BAP/UCL/SCC/BV-011-C", "48_1"),
        ("BAP/UCL/SCC/BV-012-C", "48_2"),
        ("BAP/UCL/SCC/BV-013-C", "48_3"),
        ("BAP/UCL/SCC/BV-014-C", "48_4"),
        ("BAP/UCL/SCC/BV-015-C", "48_5"),
        ("BAP/UCL/SCC/BV-016-C", "48_6"),
        ("BAP/UCL/SCC/BV-017-C", "8_1"),
        ("BAP/UCL/SCC/BV-018-C", "8_2"),
        ("BAP/UCL/SCC/BV-019-C", "16_1"),
        ("BAP/UCL/SCC/BV-020-C", "16_2"),
        ("BAP/UCL/SCC/BV-021-C", "24_1"),
        ("BAP/UCL/SCC/BV-022-C", "24_2"),
        ("BAP/UCL/SCC/BV-023-C", "32_1"),
        ("BAP/UCL/SCC/BV-024-C", "32_2"),
        ("BAP/UCL/SCC/BV-025-C", "441_1"),
        ("BAP/UCL/SCC/BV-026-C", "441_2"),
        ("BAP/UCL/SCC/BV-027-C", "48_1"),
        ("BAP/UCL/SCC/BV-028-C", "48_2"),
        ("BAP/UCL/SCC/BV-029-C", "48_3"),
        ("BAP/UCL/SCC/BV-030-C", "48_4"),
        ("BAP/UCL/SCC/BV-031-C", "48_5"),
        ("BAP/UCL/SCC/BV-032-C", "48_6"),
    ]
    for (test_case, audio_configuration) in test_codec_configurations:
        custom_test_cases.append(
            ZTestCase("BAP", test_case,
                      cmds=pre_conditions + [TestFunc(stack.le_audio_set_audio_configuration, audio_configuration)],
                      generic_wid_hdl=bap_wid_hdl),
        )

    # set audio configuration from BAP TS
    test_audio_configurations = [
        ("BAP/UCL/STR/BV-142-C", "AC 3"),
        ("BAP/UCL/STR/BV-143-C", "AC 5"),
        ("BAP/UCL/STR/BV-144-C", "AC 7(i)"),
        ("BAP/UCL/STR/BV-523-C", "AC 3"),
        ("BAP/UCL/STR/BV-524-C", "AC 5"),
        ("BAP/UCL/STR/BV-525-C", "AC 7(i)"),
    ]
    for (test_case, audio_configuration) in test_audio_configurations:
        custom_test_cases.append(
            ZTestCase("BAP", test_case,
                      cmds=pre_conditions + [TestFunc(stack.le_audio_set_audio_configuration, audio_configuration)],
                      generic_wid_hdl=bap_wid_hdl),
        )

    test_case_name_list = pts.get_test_case_list('BAP')
    tc_list = []

    for tc_name in test_case_name_list:
        # setup generic test case with pre_condition and bap wid hdl()
        instance = ZTestCase("BAP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=bap_wid_hdl)

        # use custom test case if defined above
        for custom_tc in custom_test_cases:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    return tc_list
