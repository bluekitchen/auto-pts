#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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

import logging
import sys
import btp
import time
import re
from ptsprojects.stack import get_stack

log = logging.debug

def mesh_wid_hdl(wid, description):
    log("%s, %r, %r", mesh_wid_hdl.__name__, wid, description)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        log("wid nb: %d, not implemented!", wid)


# wid handlers section begin
def hdl_wid_8(desc):
    stack = get_stack()

    ret = stack.mesh.oob_data.data

    # cleanup
    stack.mesh.oob_data.data = None
    stack.mesh.oob_data.action = None

    return str(ret)

def hdl_wid_12(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_13(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_24(desc):
    stack = get_stack()

    if stack.mesh.last_seen_prov_link_state.data is None:
        logging.error("The link state is None")
        return 'No'

    (state, bearer) = stack.mesh.last_seen_prov_link_state.data

    if state == 'closed':
        return 'Yes'
    return 'No'

def hdl_wid_81(desc):
    stack = get_stack()
    btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
    btp.mesh_init()

    return 'OK'

def hdl_wid_90(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_201(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_203(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == True:
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_204(desc):
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_210(desc):
    stack = get_stack()

    if stack.mesh.is_provisioned.data == False:
        btp.mesh_config_prov(stack.mesh.dev_uuid, 16 * '1', 0, 0, 0, 0)
        btp.mesh_init()
        return 'OK'
    else:
        return 'Cancel'

def hdl_wid_218(desc):
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_221(desc):
    stack = get_stack()

    time.sleep(stack.mesh.iv_update_timeout.data)

    return 'OK'

def hdl_wid_262(desc):
    return 'Yes'

def hdl_wid_268(desc):
    stack = get_stack()

    return 'OK'

def hdl_wid_274(desc):
    stack = get_stack()

    return 'OK'

def hdl_wid_285(desc):
    stack = get_stack()

    return 'Yes'

def hdl_wid_519(desc):
    stack = get_stack()

    btp.mesh_reset()
    return 'OK'

def hdl_wid_600(desc):
    stack = get_stack()

    return 'OK'

def hdl_wid_604(desc):
    stack = get_stack()

    pattern = re.compile(r"(?:array\s*|ID\s*)(\w+)", re.IGNORECASE)
    found = pattern.findall(desc)
    if not found \
            or int(stack.mesh.health_test_id) != int(found[0]) \
            or str(stack.mesh.health_fault_array) != found[1].upper():
        return 'Cancel'

    return 'OK'