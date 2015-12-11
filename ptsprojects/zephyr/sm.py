"""SM test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

except ImportError: # running this module as script
    import sys
    sys.path.append("../..") # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.qtestcase import QTestCase

from ptsprojects.zephyr.iutctl import get_zephyr
import btp

def test_cases(pts_bdaddr):
    """Returns a list of SM test cases
    pts -- Instance of PyPTS"""

    zephyrctl = get_zephyr()

    test_cases = [
        QTestCase("SM", "TC_PROT_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                    TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                    TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100)]),
        QTestCase("SM", "TC_PROT_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 109)]),
        QTestCase("SM", "TC_JW_BV_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("SM", "TC_JW_BV_05_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                   TestFunc(btp.gap_disconn, pts_bdaddr, 0, start_wid = 102),
                   TestFunc(btp.gap_disconnected_ev, pts_bdaddr, 1, start_wid = 102)]),
        QTestCase("SM", "TC_JW_BI_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100)]),
        QTestCase("SM", "TC_JW_BI_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("SM", "TC_JW_BI_03_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("SM", "TC_JW_BI_04_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_PKE_BV_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 108),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 108)]),
        QTestCase("SM", "TC_PKE_BV_02_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_PKE_BV_04_C",
                   [TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_set_io_cap, 0),
                    TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                    TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                    TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                    TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, start_wid = 100)]),
        QTestCase("SM", "TC_PKE_BV_05_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_adv_ind_on)]),
        QTestCase("SM", "TC_PKE_BI_01_C",
                  edit1_wids = {106 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        QTestCase("SM", "TC_PKE_BI_02_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        QTestCase("SM", "TC_PKE_BI_03_C",
                  edit1_wids = {106 : btp.var_get_wrong_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_OOB_BV_05_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        QTestCase("SM", "TC_OOB_BV_06_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_OOB_BV_07_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100)]),
        QTestCase("SM", "TC_OOB_BV_08_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_adv_ind_on)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_EKS_BV_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        QTestCase("SM", "TC_EKS_BV_02_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_EKS_BI_01_C",
                  edit1_wids = {104 : "000000"},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100)]),
        QTestCase("SM", "TC_EKS_BI_02_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_adv_ind_on, start_wid = 15)]),
        QTestCase("SM", "TC_SIGN_BV_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_SIGN_BV_03_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_SIGN_BI_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_KDU_BV_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        #QTestCase("SM", "TC_KDU_BV_02_C",
        #          edit1_wids = {104 : btp.var_get_passkey},
        #          cmds = [TestFunc(btp.core_reg_svc_gap),
        #              TestFunc(btp.gap_set_io_cap, 0),
        #              TestFunc(btp.gap_adv_ind_on, start_wid = 15),
        #              TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
        #              TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_KDU_BV_03_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        #QTestCase("SM", "TC_KDU_BV_09_C",
        #          edit1_wids = {104 : btp.var_get_passkey},
        #          cmds = [TestFunc(btp.core_reg_svc_gap),
        #              TestFunc(btp.gap_set_io_cap, 0),
        #              TestFunc(btp.gap_adv_ind_on, start_wid = 15),
        #              TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
        #              TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_KDU_BV_04_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        #QTestCase("SM", "TC_KDU_BV_05_C",
        #          edit1_wids = {104 : btp.var_get_passkey},
        #          cmds = [TestFunc(btp.core_reg_svc_gap),
        #              TestFunc(btp.gap_set_io_cap, 0),
        #              TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
        #              TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
        #              TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
        #              TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_KDU_BV_06_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        #QTestCase("SM", "TC_KDU_BV_08_C",
        #          edit1_wids = {104 : btp.var_get_passkey},
        #          cmds = [TestFunc(btp.core_reg_svc_gap),
        #              TestFunc(btp.gap_set_io_cap, 0),
        #              TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 100),
        #              TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 100),
        #              TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 100),
        #              TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 100)]),
        QTestCase("SM", "TC_KDU_BV_07_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 15),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 15)]),
        QTestCase("SM", "TC_SIP_BV_01_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_adv_ind_on, start_wid = 15),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 109),
                      TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 109),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 109)]),
        # TODO 14310 - PTS Issue
        QTestCase("SM", "TC_SIP_BV_02_C",
                  edit1_wids = {104 : btp.var_get_passkey},
                  cmds = [TestFunc(btp.core_reg_svc_gap),
                      TestFunc(btp.gap_set_io_cap, 0),
                      TestFunc(btp.gap_conn, pts_bdaddr, 0, start_wid = 101),
                      TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 101),
                      TestFunc(btp.gap_passkey_disp_ev, pts_bdaddr, 1, True, start_wid = 101)]),
        QTestCase("SM", "TC_SIE_BV_01_C",
                  [TestFunc(btp.core_reg_svc_gap),
                   TestFunc(btp.gap_set_io_cap, 0),
                   TestFunc(btp.gap_adv_ind_on),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 109),
                   TestFunc(btp.gap_disconnected_ev, pts_bdaddr, 1, start_wid = 109),
                   TestFunc(btp.gap_connected_ev, pts_bdaddr, 1, start_wid = 109),
                   TestFunc(btp.gap_pair, pts_bdaddr, 0, start_wid = 109)]),
        ]

    return test_cases

def main():
    """Main."""
    import sys
    import ptsprojects.zephyr.iutctl as iutctl

    iutctl.init_stub()

    # to be able to successfully create ZephyrCtl in QTestCase
    iutctl.ZEPHYR_KERNEL_IMAGE = sys.argv[0]

    test_cases_ = test_cases()

    for test_case in test_cases_:
        print
        print test_case

        if test_case.edit1_wids:
            print "edit1_wids: %r" % test_case.edit1_wids

        if test_case.verify_wids:
            print "verify_wids: %r" % test_case.verify_wids

        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)

if __name__ == "__main__":
    main()
