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

from struct import pack, unpack

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import pts_addr_get, pts_addr_type_get, lt2_addr_get, lt2_addr_type_get, btp_hdr_check, \
    CONTROLLER_INDEX, set_pts_addr, set_lt2_addr, LeAdv, get_iut_method as get_iut
from autopts.pybtp.types import BTPError, gap_settings_btp2txt, addr2btp_ba, Addr, OwnAddrType, AdDuration
from autopts.ptsprojects.stack import get_stack


def le_audio_rsp_succ(op=None):
    logging.debug("%s", le_audio_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read()
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_LE_AUDIO, op)

    return tuple_data


def get_24_bit_unsigned_int(b1, b2, b3):
    return (b1 << 16) | (b2 << 8) | b3


LE_AUDIO = {
    "ascs_connect":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONNECT,              CONTROLLER_INDEX),
    "ascs_configure_codec":       (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONFIGURE_CODEC,      CONTROLLER_INDEX),
    "ascs_configure_qos":         (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_CONFIGURE_QOS,        CONTROLLER_INDEX),
    "ascs_enable":                (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_ENABLE,               CONTROLLER_INDEX),
    "ascs_receiver_start_ready":  (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_RECEIVER_START_READY, CONTROLLER_INDEX),
    "ascs_receiver_stop_ready":   (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_RECEIVER_STOP_READY,  CONTROLLER_INDEX),
    "ascs_disable":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_DISABLE,              CONTROLLER_INDEX),
    "ascs_release":               (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_RELEASE,              CONTROLLER_INDEX),
    "ascs_update_metadata":       (defs.BTP_SERVICE_ID_LE_AUDIO, defs.ASCS_UPDATE_METADATA,      CONTROLLER_INDEX),
    "cig_create":                 (defs.BTP_SERVICE_ID_LE_AUDIO, defs.CIG_CREATE,                CONTROLLER_INDEX),
    "cis_create":                 (defs.BTP_SERVICE_ID_LE_AUDIO, defs.CIS_CREATE,                CONTROLLER_INDEX),
}


def ascs_connect(bd_addr=None, bd_addr_type=None, own_addr_type=OwnAddrType.le_identity_address):
    logging.debug("%s %r %r", ascs_connect.__name__, bd_addr, bd_addr_type)
    iutctl = get_iut()
    statck = get_stack()

    data_ba = bytearray()
    bd_addr_ba = addr2btp_ba(pts_addr_get(bd_addr))
    bd_addr_type_ba = chr(pts_addr_type_get(bd_addr_type)).encode('utf-8')
    own_addr_type_ba = chr(own_addr_type).encode('utf-8')

    data_ba.extend(bd_addr_type_ba)
    data_ba.extend(bd_addr_ba)
    data_ba.extend(own_addr_type_ba)

    iutctl.btp_socket.send(*LE_AUDIO['ascs_connect'], data=data_ba)
    tuple_data = le_audio_rsp_succ()
    data = tuple_data[0]

    header = data[0:2]
    chan_id, ase_count = unpack('<BB', header)

    # get sink and source ases
    ases = data[2:]
    sink_ases = []
    source_ases = []
    for i in range(ase_count):
        ase = ases[2*i : 2*i+2]
        ase_id, ase_type = unpack('<BB', ase)
        if ase_type == 0:
            sink_ases.append(ase_id)
        else:
            source_ases.append(ase_id)
    ascs_client = {'bd_addr': bd_addr, 'sink_ases': sink_ases, 'source_ases': source_ases, 'chan_id': chan_id}
    logging.debug("ASCS: SINK ASEs %r, SOURCE ASEs %r", sink_ases, source_ases)
    get_stack().le_audio.ascs_clients.append(ascs_client)


def ascs_configure_codec(chan_id, ase_id, coding_format, sampling_frequency_hz, frame_duration_us, octets_per_frame):
    iutctl = get_iut()

    data_ba = pack('<BBBIHH', chan_id, ase_id, coding_format, sampling_frequency_hz, frame_duration_us, octets_per_frame)

    iutctl.btp_socket.send(*LE_AUDIO['ascs_configure_codec'], data=data_ba)
    tuple_data = le_audio_rsp_succ()
    data = tuple_data[0]
    # convert 24-bit values manually
    fields = unpack("<BBBBBB", data)
    presentation_latency_min_us = get_24_bit_unsigned_int(fields[0], fields[1], fields[2])
    presentation_latency_max_us = get_24_bit_unsigned_int(fields[3], fields[4], fields[5])
    return (presentation_latency_min_us, presentation_latency_max_us)


def ascs_configure_qos(chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number,
                       max_transport_latency_ms):
    iutctl = get_iut()

    data_ba = pack('<BBBBHBHBB', chan_id, ase_id,  cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_configure_qos'], data=data_ba)


def ascs_enable(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_enable'], data=data_ba)


def ascs_receiver_start_ready(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_receiver_start_ready'], data=data_ba)


def ascs_receiver_stop_ready(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_receiver_stop_ready'], data=data_ba)


def ascs_disable(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_disable'], data=data_ba)


def ascs_release(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_release'], data=data_ba)


def ascs_update_metadata(chan_id, ase_id):
    iutctl = get_iut()

    data_ba = pack('<BB', chan_id, ase_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['ascs_update_metadata'], data=data_ba)


def cig_create(cig_id, sdu_interval_c_to_p_us, sdu_interval_p_to_c_us, framing, cis_params):
    iutctl = get_iut()

    cis_count = len(cis_params)
    logging.debug("CIG: %u cis, sdu interval %u us, framing %u, cis_params %r", cis_count, sdu_interval_c_to_p_us, framing, cis_params)
    data_ba = pack('<BBHHB', cig_id, cis_count, sdu_interval_c_to_p_us, sdu_interval_p_to_c_us, framing)
    for (cis_id, max_sdu_c_to_p, max_sdu_p_to_c) in cis_params:
        data_ba = data_ba + pack('<BHH', cis_id, max_sdu_c_to_p, max_sdu_p_to_c)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['cig_create'], data=data_ba)

def cis_create(cig_id):
    iutctl = get_iut()

    data_ba = pack('<B', cig_id)

    iutctl.btp_socket.send_wait_rsp(*LE_AUDIO['cis_create'], data=data_ba)
