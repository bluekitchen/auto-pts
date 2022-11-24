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

"""Wrapper around btp messages. The functions are added as needed."""

import logging

from struct import pack

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get, lt2_addr_get, lt2_addr_type_get, btp_hdr_check, \
    CONTROLLER_INDEX, set_pts_addr, set_lt2_addr, LeAdv, get_iut_method as get_iut
from autopts.pybtp.types import BTPError, gap_settings_btp2txt, addr2btp_ba, Addr, OwnAddrType, AdDuration

LE_AUDIO = {
    "ascs_connect":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONNECT,         CONTROLLER_INDEX),
    "ascs_configure_codec":       (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONFIGURE_CODEC, CONTROLLER_INDEX),
    "ascs_configure_qos":         (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONFIGURE_QOS,   CONTROLLER_INDEX),
    "ascs_enable":                (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_ENABLE,          CONTROLLER_INDEX),
    "ascs_receiver_start_ready":  (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_ENABLE,          CONTROLLER_INDEX),
    "ascs_receiver_stop_ready":   (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_ENABLE,          CONTROLLER_INDEX),
    "ascs_disable":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_DISABLE,         CONTROLLER_INDEX),
    "ascs_release":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_RELEASE,         CONTROLLER_INDEX),
}


def ascs_connect(bd_addr=None, bd_addr_type=None, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", ascs_connect.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    own_addr_type_ba = chr(own_addr_type).encode('utf-8')

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(own_addr_type_ba)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_connect'], data=data_ba)

def ascs_configure_codec(ase_index, coding_format, sampling_frequency_hz, frame_duration_us, octets_per_frame):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BBBIHH', channel_id, ase_index, coding_format, sampling_frequency_hz, frame_duration_us, octets_per_frame)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_configure_codec'], data=data_ba)

def ascs_configure_qos(ase_index, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BBHBHBB', channel_id, ase_index, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_configure_qos'], data=data_ba)

def ascs_enable(ase_index):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BB', channel_id, ase_index)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_enable'], data=data_ba)

def ascs_receiver_start_ready(ase_index):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BB', channel_id, ase_index)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_receiver_start_ready'], data=data_ba)

def ascs_receiver_stop_ready(ase_index):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BB', channel_id, ase_index)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_receiver_stop_ready'], data=data_ba)

def ascs_disable(ase_index):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BB', channel_id, ase_index)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_disable'], data=data_ba)

def ascs_release(ase_index):
    iutctl = get_iut()

    # TODO use channel id returned from ascs_connect
    channel_id = 0
    data_ba = pack('<BB', channel_id, ase_index)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_release'], data=data_ba)
