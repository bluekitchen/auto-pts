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

    # provide octets_per_frame for BAP/UCL/SCC/BV-001-C - BAP/UCL/SCC/BV-032-C
    custom_test_cases = []
    octets_001_032 = 2 * [26, 30,  30,40,  45,60, 60,80,  97,130,  75, 100,  90, 120,  117, 155]
    for (i, octets) in zip(range(1,33), octets_001_032):
        custom_test_cases.append(
            ZTestCase("BAP", "BAP/UCL/SCC/BV-%03u-C" % i,
                      cmds=pre_conditions + [TestFunc(stack.le_audio_set_octets_per_frame, octets)],
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
