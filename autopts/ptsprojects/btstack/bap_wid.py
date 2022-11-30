import logging
import sys
import socket
import re
from time import sleep

from autopts.pybtp import btp
from autopts.wid.gap import gap_wid_hdl as gen_wid_hdl, hdl_wid_139_mode1_lvl2, hdl_wid_139_mode1_lvl4
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams, IOCap

log = logging.debug

# name, frequency_hz, frame_duration, octets_per_frame
codec_specific_config_settings = [
    ( "8_1",   8000,  7500,  26),
    ( "8_2",   8000, 10000,  30),
    ("16_1",  16000,  7500,  30),
    ("16_2",  16000, 10000,  40),
    ("24_1",  24000,  7500,  45),
    ("24_2",  24000, 10000,  60),
    ("32_1",  32000,  7500,  60),
    ("32_2",  32000, 10000,  80),
    ("441_1", 44100,  7500,  97),
    ("441_2", 44100, 10000, 130),
    ("48_1",  48000,  7500,  75),
    ("48_2",  48000, 10000, 100),
    ("48_3",  48000,  7500,  90),
    ("48_4",  48000, 10000, 120),
    ("48_5",  48000,  7500, 117),
    ("48_6",  48000, 10000, 155),
]

# name, sdu interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms
qos_config_settings = [
    ( "8_1_1",   7500, 0,  26,  2,   8),
    ( "8_2_1",  10000, 0,  30,  2,  10),
    ("16_1_1",   7500, 0,  30,  2,   8),
    ("16_2_1",  10000, 0,  40,  2,  10),
    ("24_1_1",   7500, 0,  45,  2,   8),
    ("24_2_1",  10000, 0,  60,  2,  10),
    ("32_1_1",   7500, 0,  60,  2,   8),
    ("32_2_1",  10000, 0,  80,  2,  10),
    ("441_1_1",  8163, 1,  97,  5,  24),
    ("441_2_1", 10884, 1, 130,  5,  31),
    ("48_1_1",   7500, 0,  75,  5,  15),
    ("48_2_1",  10000, 0, 100,  5,  20),
    ("48_3_1",   7500, 0,  90,  5,  15),
    ("48_4_1",  10000, 0, 120,  5,  20),
    ("48_5_1",   7500, 0, 117,  5,  15),
    ("48_6_1",  10000, 0, 115,  5,  20),
    ( "8_1_2",   7500, 0,  26, 13,  75),
    ( "8_2_2",  10000, 0,  30, 13,  95),
    ("16_1_2",   7500, 0,  30, 13,  75),
    ("16_2_2",  10000, 0,  40, 13,  95),
    ("24_1_2",   7500, 0,  45, 13,  75),
    ("24_2_2",  10000, 0,  60, 13,  95),
    ("32_1_2",   7500, 0,  60, 13,  75),
    ("32_2_2",  10000, 0,  80, 13,  95),
    ("441_1_2",  8163, 1,  97, 13,  80),
    ("441_2_2", 10884, 1, 130, 13,  85),
    ("48_1_2",   7500, 0,  75, 13,  75),
    ("48_2_2",  10000, 0, 100, 13,  95),
    ("48_3_2",   7500, 0,  90, 13,  75),
    ("48_4_2",  10000, 0, 120, 13, 100),
    ("48_5_2",   7500, 0, 117, 13,  75),
    ("48_6_2",  10000, 0, 115, 13, 100)
]

def le_audio_codec_get_info(codec_name):
    for (name, sampling_frequency_hz, frame_duration_us, octets_per_frame) in codec_specific_config_settings:
        if codec_name == name:
            return (sampling_frequency_hz, frame_duration_us, octets_per_frame)
    return (0,0,0)

def le_audio_qos_get_info(qos_name):
    for (name, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) in qos_config_settings:
        if qos_name == name:
            return (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    logging.error("qos not found %s" % qos_name)
    return (0,0,0,0,0)


def bap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", bap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


def hdl_wid_20100(desc):
    # 'Please initiate a GATT connection to the PTS.'
    btp.gap_conn()
    return True


def hdl_wid_20106(desc):
    # 'Please write to Client Characteristic Configuration Descriptor..'
    stack = get_stack()
    if not stack.le_audio.ascs_is_connected():
        btp.ascs_connect()
        stack.le_audio.ascs_connected()
    return True


def hdl_wid_302(desc):
    # Please configure ASE state to CODEC configured with ? ASE, Freq: ? KHz, Frame Duration: ? ms
    stack = get_stack()
    pattern = '.*Freq: ([\d\.]+) KHz, Frame Duration: ([\d\.]+) ms.*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False
    frequency_hz = int(float(params.group(1)) * 1000)
    frame_duration_us = int(float(params.group(2)) * 1000)
    # provided by custom test setup in bap.py
    octets_per_frame = stack.le_audio.get_octets_per_frame()
    log("ASE Config %s %s %s", frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)
    return True


def hdl_wid_303(desc):
    # Please configure ASE state to QoS Configured with 8_1_1 in SINK direction
    stack = get_stack()
    pattern = '.* (\d+_\d+)_(\d) .*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False
    codec_name = params.group(1)
    channels = int(params.group(2))
    qos_name = params.group(1) + '_' + params.group(2)
    log("ASE Codec Setting %s, QoS Setting %s", codec_name, qos_name)

    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec_name)
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)

    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info(qos_name)
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_304(desc):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)

    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info('16_2_1')
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    btp.ascs_enable(0)
    return True

def hdl_wid_305(desc):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)

    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info('16_2_1')
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    btp.ascs_enable(0)

    # PTS 8.3 does not continue, let's assume we have to first enter streaming and then disable the stream
    btp.ascs_receiver_start_ready(0)
    btp.ascs_disable(0)
    return True

def hdl_wid_306(desc):
    # Please configure ASE state to Streaming for SINK/SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms

    pattern = '.*(SINK|SOURCE) ASE.*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False

    ase_type = params.group(1)

    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)

    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info('16_2_1')
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    btp.ascs_enable(0)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(0)
    return True


def hdl_wid_307(desc):
    # Please configure ASE state to Disabling state. If server is Source, please initiate Receiver Stop Ready
    btp.ascs_disable(0)
    return True


def hdl_wid_309(desc):
    # Please configure ASE state to Releasing state.
    btp.ascs_release(0)
    return True


def hdl_wid_311(desc):
    # Please configure 1 SOURCE ASE with Config Setting: 8_1_1.\nAfter that, configure to streaming state.
    pattern = '.*(SINK|SOURCE) ASE.* Setting: (\d+_\d+)_(\d).*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False

    ase_type = params.group(1)
    codec_name = params.group(2)
    channels = int(params.group(3))
    qos_name = params.group(2) + '_' + params.group(3)
    log("ASE Codec %s, Setting %s, QoS Setting %s", ase_type, codec_name, qos_name)

    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec_name)
    btp.ascs_configure_codec(0, 6, frequency_hz, frame_duration_us, octets_per_frame)

    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info(qos_name)
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    btp.ascs_enable(0)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(0)
    return True


def hdl_wid_314(desc):
    # Please configure ASE state to CODEC configured with Vendor specific parameter in SOURCE/SINK ASE
    btp.ascs_configure_codec(0, 0xff, 48000, 10000, 26)
    return True


def hdl_wid_315(desc):
    # Please configure ASE state to QoS Configured with Vendor specific parameter in SOURCE/SINK ASE
    btp.ascs_configure_codec(0, 0xff, 48000, 10000, 26)
    # PTS TSPX_VS_QoS_*
    sdu_interval_us = 10000
    framing = 0
    # 2M_PHY
    max_sdu_size = 40
    retransmission_number = 2
    max_transport_latency_ms = 10
    # presentation delay 40000 us
    btp.ascs_configure_qos(0, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_364(desc):
    # After processed audio stream data, please click OK.
    return True