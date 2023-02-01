"""BAP test cases"""
from time import sleep

from autopts.pybtp import btp
from autopts.pybtp.types import Addr, IOCap, AdType, AdFlags, Prop, Perm, UUID
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.btstack.ztestcase import ZTestCase, ZTestCaseSlave
from autopts.ptsprojects.btstack.bap_wid import bap_wid_hdl
from autopts.ptsprojects.stack import get_stack, SynchPoint
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

    for pts in ptses:
        # Set BAP common PIXIT values
        pts.set_pixit("BAP", "TSPX_delete_ltk", "TRUE")

        # Needed to pass BAP/UCL/SCC/BV-033-C, BAP/UCL/SCC/BV-034-C, ..
        pts.set_pixit("BAP", "TSPX_Codec_ID", "FF00000000")


# When called by LT2, BD ADDR might not be set, let's wait until it becomes ready
def iut_addr_get_str_spin_lock():
    stack = get_stack()
    while True:
        addr = stack.gap.iut_addr_get_str()
        if addr != "000000000000":
            return addr
        sleep(0.1)


def test_cases(ptses):
    """Returns a list of GAP test cases
    ptses -- list of PyPTS instances"""

    pts_lt1 = ptses[0]
    pts_lt1_bd_addr = pts_lt1.q_bd_addr

    stack = get_stack()
    iut_device_name = get_unique_name(pts_lt1)
    stack.gap_init(iut_device_name, iut_manufacturer_data, iut_appearance, iut_svc_data, iut_flags, iut_svcs)

    btp.set_pts_addr(pts_lt1_bd_addr, Addr.le_public)

    # Preconditions for Lower Tester 1
    pre_conditions = [
        TestFunc(stack.le_audio_init),
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(btp.gap_set_powered_on),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts_lt1.update_pixit_param(
            "BAP", "TSPX_bd_addr_iut", stack.gap.iut_addr_get_str())),
    ]

    # Preconditions for Lower Tester 2
    pre_conditions_lt2 = [
        TestFunc(lambda: pts_lt2.update_pixit_param(
            "BAP", "TSPX_bd_addr_iut", iut_addr_get_str_spin_lock())),
    ]

    # Preconditions for Unicast Server
    # get ad to be less than 31 as btstack iut doesn't support larger adv data for extended advertisements yet
    ad = stack.gap.ad
    if AdType.name_short in ad:
        del ad[AdType.name_short]
    if AdType.name_full in ad:
        del ad[AdType.name_full]
    ad[AdType.name_short] = 'tester'.encode('utf-8')
    ad[AdType.uuid16_some] = bytes([0x4E, 0x18])
    ad[AdType.uuid16_svc_data] = bytes([0x4E, 0x18,  0x01,  0x07, 0x00,  0x00, 0x00,  0x00])

    pre_conditions_unicast_server = [
        TestFunc(btp.gap_set_extended_advertising_on),
        TestFunc(btp.gap_adv_ind_on, ad=ad)
    ]

    custom_test_cases = []
    test_cases_lt2 = []
    test_cases_slaves = []

    # List of configurations
    test_codec_configurations_new = [
          "8_1",   "8_2", "16_1", "16_2", "24_1", "24_2", "32_1", "32_2",
        "441_1", "441_2", "48_1", "48_2", "48_3", "48_4", "48_5", "48_6",
    ]

    # Codec configuration for tests where PTS does not fully indicate codec
    for (codec_id, codec_name) in zip(range(0, 33), test_codec_configurations_new + test_codec_configurations_new):
        # Unicast Client BAP/UCL/SCC/BV-001-C - Client BAP/UCL/SCC/BV-032-C
        custom_test_cases.append(
            ZTestCase("BAP", "BAP/UCL/SCC/BV-%03u-C" % (codec_id+1),
                      cmds=pre_conditions + [TestFunc(stack.le_audio_set_codec, codec_name)],
                      generic_wid_hdl=bap_wid_hdl),
        )
        # Unicast Server BAP/USR/SCC/BV-001-C - Client BAP/USR/SCC/BV-032-C
        custom_test_cases.append(
            ZTestCase("BAP", "BAP/USR/SCC/BV-%03u-C" % (codec_id+1),
                      cmds=pre_conditions + pre_conditions_unicast_server + [TestFunc(stack.le_audio_set_codec, codec_name)],
                      generic_wid_hdl=bap_wid_hdl),
        )
        # Unicast Server BAP/USR/SCC/BV-035-C - BAP/USR/SCC/BV-066-C
        custom_test_cases.append(
            ZTestCase("BAP", "BAP/USR/SCC/BV-%03u-C" % (codec_id+35),
                      cmds=pre_conditions + pre_conditions_unicast_server + [TestFunc(stack.le_audio_set_codec, codec_name)],
                      generic_wid_hdl=bap_wid_hdl),
        )

    # set audio configuration from BAP TS
    test_audio_configurations = [
        ("BAP/UCL/STR/BV-129-C", "AC 1"),
        ("BAP/UCL/STR/BV-130-C", "AC 4"),
        ("BAP/UCL/STR/BV-131-C", "AC 2"),
        ("BAP/UCL/STR/BV-132-C", "AC 10"),
        ("BAP/UCL/STR/BV-142-C", "AC 3"),
        ("BAP/UCL/STR/BV-143-C", "AC 5"),
        ("BAP/UCL/STR/BV-144-C", "AC 7(i)"),
        ("BAP/UCL/STR/BV-235-C", "AC 6(i)"),
        ("BAP/UCL/STR/BV-267-C", "AC 6(i)"),
        ("BAP/UCL/STR/BV-300-C", "AC 6(ii)"),
        ("BAP/UCL/STR/BV-333-C", "AC 9(i)"),
        ("BAP/UCL/STR/BV-365-C", "AC 9(ii)"),
        ("BAP/UCL/STR/BV-397-C", "AC 8(i)"),
        ("BAP/UCL/STR/BV-429-C", "AC 8(ii)"),
        ("BAP/UCL/STR/BV-461-C", "AC 11(i)"),
        ("BAP/UCL/STR/BV-493-C", "AC 11(ii)"),
        ("BAP/UCL/STR/BV-522-C", "AC 11(ii)"),
        ("BAP/UCL/STR/BV-523-C", "AC 3"),
        ("BAP/UCL/STR/BV-524-C", "AC 5"),
        ("BAP/UCL/STR/BV-525-C", "AC 7(i)"),
        ("BAP/UCL/STR/BV-526-C", "AC 7(ii)"),
        ("BAP/UCL/STR/BV-527-C", "AC 6(i)"),
        ("BAP/UCL/STR/BV-528-C", "AC 6(ii)"),
        ("BAP/UCL/STR/BV-529-C", "AC 9(i)"),
        ("BAP/UCL/STR/BV-530-C", "AC 9(ii)"),
        ("BAP/UCL/STR/BV-531-C", "AC 8(i)"),
        ("BAP/UCL/STR/BV-532-C", "AC 8(ii)"),
        ("BAP/UCL/STR/BV-533-C", "AC 11(i)"),
        ("BAP/UCL/STR/BV-534-C", "AC 11(ii)"),
        ("BAP/UCL/PD/BV-01-C", "AC 6(ii)"),
        ("BAP/UCL/PD/BV-02-C", "AC 9(ii)"),
    ]

    # UCL/STR/BV-001 - 128
    for i in range(1,32, 2):
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % i,        "AC 2"))
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % (i + 64), "AC 2"))
    for i in range(2,33, 2):
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % i,        "AC 10"))
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % (i + 64), "AC 10"))
    for i in range(33,64, 2):
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % i,        "AC 1"))
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % (i + 64), "AC 1"))
    for i in range(34,65, 2):
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % i,        "AC 4"))
        test_audio_configurations.append(('BAP/UCL/STR/BV-%03u-C' % (i + 64), "AC 4"))

    for (test_case, audio_configuration) in test_audio_configurations:
        if test_case.endswith('(ii)'):
            lt2_name = test_case + '_LT2'
            test_cases_lt2.append(
                ZTestCase("BAP", test_case,
                    cmds=pre_conditions + [TestFunc(stack.le_audio_set_audio_configuration, audio_configuration)],
                    generic_wid_hdl=bap_wid_hdl,
                    lt2=lt2_name))
            test_cases_slaves.append(
                ZTestCaseSlave("BAP", lt2_name,
                    cmds=pre_conditions_lt2 + [TestFunc(stack.le_audio_set_audio_configuration, audio_configuration)],
                    generic_wid_hdl=bap_wid_hdl)
                )
        else:
            custom_test_cases.append(
                ZTestCase("BAP", test_case,
                      cmds=pre_conditions + [TestFunc(stack.le_audio_set_audio_configuration, audio_configuration)],
                      generic_wid_hdl=bap_wid_hdl))


    test_case_name_list = pts_lt1.get_test_case_list('BAP')
    tc_list = []

    for tc_name in test_case_name_list:
        # setup generic test case with pre_condition and bap wid hdl()
        instance = ZTestCase("BAP", tc_name,
                             cmds=pre_conditions,
                             generic_wid_hdl=bap_wid_hdl)

        # use custom test case if defined above
        for custom_tc in custom_test_cases + test_cases_lt2:
            if tc_name == custom_tc.name:
                instance = custom_tc
                break

        tc_list.append(instance)

    if len(ptses) == 2:
        tc_list += test_cases_slaves
        pts_lt2 = ptses[1]
        pts_lt2_bd_addr = pts_lt2.q_bd_addr
        btp.set_lt2_addr(pts_lt2_bd_addr, Addr.le_public)

    return tc_list
