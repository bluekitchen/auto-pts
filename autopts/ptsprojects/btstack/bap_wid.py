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
    ("8_1", 8000, 7500, 26),
    ("8_2", 8000, 10000, 30),
    ("16_1", 16000, 7500, 30),
    ("16_2", 16000, 10000, 40),
    ("24_1", 24000, 7500, 45),
    ("24_2", 24000, 10000, 60),
    ("32_1", 32000, 7500, 60),
    ("32_2", 32000, 10000, 80),
    ("441_1", 44100, 7500, 97),
    ("441_2", 44100, 10000, 130),
    ("48_1", 48000, 7500, 75),
    ("48_2", 48000, 10000, 100),
    ("48_3", 48000, 7500, 90),
    ("48_4", 48000, 10000, 120),
    ("48_5", 48000, 7500, 117),
    ("48_6", 48000, 10000, 155),
]

# name, sdu interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms
qos_config_settings = [
    ("8_1_1", 7500, 0, 26, 2, 8),
    ("8_2_1", 10000, 0, 30, 2, 10),
    ("16_1_1", 7500, 0, 30, 2, 8),
    ("16_2_1", 10000, 0, 40, 2, 10),
    ("24_1_1", 7500, 0, 45, 2, 8),
    ("24_2_1", 10000, 0, 60, 2, 10),
    ("32_1_1", 7500, 0, 60, 2, 8),
    ("32_2_1", 10000, 0, 80, 2, 10),
    ("441_1_1", 8163, 1, 97, 5, 24),
    ("441_2_1", 10884, 1, 130, 5, 31),
    ("48_1_1", 7500, 0, 75, 5, 15),
    ("48_2_1", 10000, 0, 100, 5, 20),
    ("48_3_1", 7500, 0, 90, 5, 15),
    ("48_4_1", 10000, 0, 120, 5, 20),
    ("48_5_1", 7500, 0, 117, 5, 15),
    ("48_6_1", 10000, 0, 115, 5, 20),
    ("8_1_2", 7500, 0, 26, 13, 75),
    ("8_2_2", 10000, 0, 30, 13, 95),
    ("16_1_2", 7500, 0, 30, 13, 75),
    ("16_2_2", 10000, 0, 40, 13, 95),
    ("24_1_2", 7500, 0, 45, 13, 75),
    ("24_2_2", 10000, 0, 60, 13, 95),
    ("32_1_2", 7500, 0, 60, 13, 75),
    ("32_2_2", 10000, 0, 80, 13, 95),
    ("441_1_2", 8163, 1, 97, 13, 80),
    ("441_2_2", 10884, 1, 130, 13, 85),
    ("48_1_2", 7500, 0, 75, 13, 75),
    ("48_2_2", 10000, 0, 100, 13, 95),
    ("48_3_2", 7500, 0, 90, 13, 75),
    ("48_4_2", 10000, 0, 120, 13, 100),
    ("48_5_2", 7500, 0, 117, 13, 75),
    ("48_6_2", 10000, 0, 115, 13, 100)
]

# Audio Configuration from BAP TS
# - Each configuration has number of servers and an array of CIS entries
# - Each CIS entry specifies number of audio channels on local and remote sinks (matching the topology field)
audio_configurations = {
    "AC 1":      (1, [(0, 1)]),
    "AC 2":      (1, [(1, 0)]),
    "AC 3":      (1, [(1, 1)]),
    "AC 4":      (1, [(0, 2)]),
    "AC 5":      (1, [(1, 2)]),
    "AC 6(i)":   (1, [(0, 1), (0, 1)]),
    "AC 6(ii)":  (2, [(0, 1), (0, 1)]),
    "AC 7(i)":   (1, [(0, 1), (1, 0)]),
    "AC 7(ii)":  (2, [(0, 1), (1, 0)]),
    "AC 8(i)":   (1, [(0, 1), (1, 1)]),
    "AC 8(ii)":  (2, [(0, 1), (1, 1)]),
    "AC 9(i)":   (1, [(1, 0), (1, 0)]),
    "AC 9(ii)":  (2, [(1, 0), (1, 0)]),
    "AC 9(ii)":  (2, [(1, 0), (1, 0)]),
    "AC 10":     (1, [(2, 0)]),
    "AC 11(i)":  (1, [(1, 1), (1, 1)]),
    "AC 11(ii)": (2, [(1, 1), (1, 1)]),
}


def le_audio_codec_get_info(codec_name):
    for (name, sampling_frequency_hz, frame_duration_us, octets_per_frame) in codec_specific_config_settings:
        if codec_name == name:
            return sampling_frequency_hz, frame_duration_us, octets_per_frame
    return 0, 0, 0


def le_audio_qos_get_info(qos_name):
    for (name, sdu_interval_us, framing, max_sdu_size, retransmission_number,
         max_transport_latency_ms) in qos_config_settings:
        if qos_name == name:
            return sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms
    logging.error("qos not found %s" % qos_name)
    return 0, 0, 0, 0, 0


def le_audio_audio_configuration_get_info(audio_configuration_name):
    return audio_configurations[audio_configuration_name]

def get_any_ase_id(ascs_client):
    sink_ases = ascs_client['sink_ases']
    source_ases = ascs_client['source_ases']
    if (len(sink_ases) > 0):
        return sink_ases[0]
    else:
        return source_ases[0]


def get_source_ase_id(ascs_client):
    return ascs_client['source_ases'][0]


def get_sink_ase_id(ascs_client):
    return ascs_client['sink_ases'][0]


def get_ase_id_for_type(ascs_client, ase_type):
    if ase_type == "SOURCE":
        return get_source_ase_id(ascs_client)
    else:
        return get_sink_ase_id(ascs_client)


def le_audio_configure_lc3(ascs_chan_id, ase_id, codec):
    frequency_hz, frame_duration_us, octets_per_frame = le_audio_codec_get_info(codec)
    log("ASE Codec LC3 frequency %u hz, frame duration %u us, octets per frame %u", frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

def le_audio_configure_qos(ascs_chan_id, codec, qos, audio_conffiguration, ):
    # configure codec
    # create cig
    # configure cis
    pass

# try to use local handler and fall back to gap handler
def bap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", bap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(description)
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)


def hdl_wid_302(desc):
    # Please configure ASE state to CODEC configured with ? ASE, Freq: ? KHz, Frame Duration: ? ms
    # we use codec info from test specification as octets per frame is not providd by PTS

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_any_ase_id(ascs_client_0)
    codec = stack.le_audio.get_codec()

    le_audio_configure_lc3(ascs_chan_id_0, ase_id, codec)
    return True


def hdl_wid_303(desc):
    # Please configure ASE state to QoS Configured with 8_1_1 in SINK direction
    pattern = '.* (\d+_\d+)_(\d) .* (SINK|SOURCE) .*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False
    codec = params.group(1)
    channels = int(params.group(2))
    qos = params.group(1) + '_' + params.group(2)
    ase_type = params.group(3)

    log("ASE Codec Setting %s, QoS Setting %s, type %s", codec, qos, ase_type)

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, ase_type)
    cig_id = 1
    cis_id = 1
    framing = 0

    # Codec
    frequency_hz, frame_duration_us, octets_per_frame = le_audio_codec_get_info(codec)
    log("ASE Codec LC3 frequency %u hz, frame duration %u us, octets per frame %u", frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

    # CIG / QoS
    if ase_type == "SOURCE":
        cis_params = [(cis_id, 0, octets_per_frame)]
    else:
        cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info(qos)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_304(desc):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, "SOURCE")

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    cis_params = [(cis_id, 0, octets_per_frame)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info('16_2_1')
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_305(desc):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, "SINK")

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info('16_2_1')
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id_0, ase_id)

    # PTS 8.3 does not continue, let's assume we have to first enter streaming and then disable the stream
    btp.ascs_receiver_start_ready(ascs_chan_id_0, ase_id)
    btp.ascs_disable(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_306(desc):
    # Please configure ASE state to Streaming for SINK/SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    pattern = '.*(SINK|SOURCE) ASE.*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False

    ase_type = params.group(1)

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, ase_type)

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    if ase_type == "SOURCE":
        cis_params = [(cis_id, 0, octets_per_frame)]
    else:
        cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info('16_2_1')
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id_0, ase_id)

    # CIS
    btp.cis_create(cig_id)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_307(desc):
    # Please configure ASE state to Disabling state. If server is Source, please initiate Receiver Stop Ready
    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_any_ase_id(ascs_client_0)
    btp.ascs_disable(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_309(desc):
    # Please configure ASE state to Releasing state.
    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_any_ase_id(ascs_client_0)
    btp.ascs_release(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_310(desc):
    # Please send Update Metadata Opcode with valid data.
    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_any_ase_id(ascs_client_0)
    btp.ascs_update_metadata(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_311(desc):
    # Please configure 1 SOURCE ASE with Config Setting: 8_1_1.\nAfter that, configure to streaming state.
    # Please configure 1 SINK ASE with Config Setting: IXIT.\n
    pattern = ".*(SINK|SOURCE) ASE.*Config Setting: (\w+)\."
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error in desc")
        return False
    ase_type = params.group(1)
    qos_string = params.group(2)

    if qos_string == "IXIT":
        codec = '16_2'
        qos = '16_2_1'
    else:
        pattern = '(\d+_\d+)_(\d)'
        params = re.match(pattern, qos_string)
        if not params:
            logging.error("parsing error in " + qos_string)
            return False
        codec = params.group(1)
        qos = params.group(1) + '_' + params.group(2)
    log("ASE Codec %s, Setting %s, QoS Setting %s", ase_type, codec, qos)

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, ase_type)

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec)
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 6, frequency_hz, frame_duration_us, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    if ase_type == "SOURCE":
        cis_params = [(cis_id, 0, octets_per_frame)]
    else:
        cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info(qos)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id_0, ase_id)

    # CIS
    btp.cis_create(cig_id)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(ascs_chan_id_0, ase_id)
    return True


def hdl_wid_313(desc):
    # Please configure 1 SINK and 1 SOURCE ASE with Config Setting: 16_2_1.\nAfter that, configure both ASEes to streaming state
    # Please configure 1 SINK and 1 SOURCE ASE with Config Setting: IXIT.\nAfter that, configure both ASEes to streaming state.
    pattern = ".*Config Setting: (\w+)\."
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error in desc")
        return False

    if params.group(1) == "IXIT":
        codec_name = '16_2'
        qos_name = '16_2_1'
    else:
        qos_string = params.group(1)
        pattern = '(\d+_\d+)_(\d)'
        params = re.match(pattern, qos_string)
        if not params:
            logging.error("parsing error in " + qos_string)
            return False
        codec_name = params.group(1)
        qos_name = params.group(1) + '_' + params.group(2)

    codec_format = 6
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec_name)
    log("ASE Codec %u, Setting %s, QoS Setting %s", codec_format, codec_name, qos_name)

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    source_ase_id = get_source_ase_id(ascs_client_0)
    sink_ase_id = get_sink_ase_id(ascs_client_0)

    # Codec
    log("ASE codec %u, Frequency %u, frame duration %u, octets %u", codec_format, frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id_0, source_ase_id, codec_format, frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id_0, sink_ase_id, codec_format, frequency_hz, frame_duration_us, octets_per_frame)

    # Get Audio Configuration from test spec
    audio_configuration = stack.le_audio.get_audio_configuration()
    (num_servers, cis_entries) = audio_configurations[audio_configuration]
    log("Audio Configuration %s -> num servers %u, cis entries %s", audio_configuration, num_servers, cis_entries)

    # Determine CIS Params based on Audio Configuration and map ase to cis
    cis_params = []
    cig_id = 1
    cis_id = 1
    sink_cis = 0
    source_cis = 0
    for cis_entry in cis_entries:
        cis_params.append((cis_id, octets_per_frame * cis_entry[1], octets_per_frame * cis_entry[0]))
        if sink_cis == 0 and cis_entry[1] > 0:
            sink_cis = cis_id
        if source_cis == 0 and cis_entry[0] > 0:
            source_cis = cis_id
        cis_id += 1

    # CIG
    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info(qos_name)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)

    # QoS
    btp.ascs_configure_qos(ascs_chan_id_0, sink_ase_id, cig_id, sink_cis, sdu_interval_us, framing, max_sdu_size, retransmission_number,
                           max_transport_latency_ms)
    btp.ascs_configure_qos(ascs_chan_id_0, source_ase_id, cig_id,source_cis, sdu_interval_us, framing, max_sdu_size, retransmission_number,
                           max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id_0, source_ase_id)
    btp.ascs_enable(ascs_chan_id_0, sink_ase_id)

    # Create CIS
    btp.cis_create(cig_id)

    # Receiver Ready
    btp.ascs_receiver_start_ready(sink_ase_id, source_ase_id)
    return True


def hdl_wid_314(desc):
    # Please configure ASE state to CODEC configured with Vendor specific parameter in SOURCE/SINK ASE
    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_any_ase_id(ascs_client_0)
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 0xff, 48000, 10000, 26)
    return True


def hdl_wid_315(desc):
    # Please configure ASE state to QoS Configured with Vendor specific parameter in SOURCE/SINK ASE.
    pattern = '.*(SINK|SOURCE) ASE.*'
    params = re.match(pattern, desc)
    if not params:
        logging.error("parsing error")
        return False

    ase_type = params.group(1)

    stack = get_stack()
    ascs_client_0 = stack.le_audio.ascs_clients[0]
    ascs_chan_id_0 = ascs_client_0['chan_id']
    ase_id = get_ase_id_for_type(ascs_client_0, ase_type)

    # Codec
    btp.ascs_configure_codec(ascs_chan_id_0, ase_id, 0xff, 48000, 10000, 26)

    # PTS TSPX_VS_QoS_*
    sdu_interval_us = 10000
    framing = 0
    # 2M_PHY
    max_sdu_size = 40
    retransmission_number = 2
    max_transport_latency_ms = 10
    # presentation delay 40000 us
    octets_per_frame = 26

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    if ase_type == "SOURCE":
        cis_params = [(cis_id, 0, octets_per_frame)]
    else:
        cis_params = [(cis_id, octets_per_frame, 0)]
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id_0, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_364(desc):
    # After processed audio stream data, please click OK.
    return True


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
