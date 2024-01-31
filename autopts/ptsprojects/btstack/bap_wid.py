import logging
import sys
import socket
import re
from time import sleep

from autopts.pybtp import btp
from autopts.wid.gap import gap_wid_hdl as gen_wid_hdl, hdl_wid_139_mode1_lvl2, hdl_wid_139_mode1_lvl4
from autopts.ptsprojects.stack import get_stack
from autopts.pybtp.types import WIDParams, IOCap, Addr, AdType

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


def get_ase_id_for_type(ascs_client, ase_type):
    if ase_type == "SOURCE":
        return ascs_client['source_ases'][0]
    else:
        return ascs_client['sink_ases'][0]


def le_audio_configure_lc3(ascs_chan_id, ase_id, codec, audio_locations):
    frequency_hz, frame_duration_us, octets_per_frame = le_audio_codec_get_info(codec)
    log("ASE Codec LC3 %s: frequency %u hz, frame duration %u us, octets per frame %u", codec, frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, audio_locations, octets_per_frame)


def le_audio_configure_qos(ascs_chan_id, codec, qos, audio_conffiguration, ):
    # configure codec
    # create cig
    # configure cis
    pass


# Test Cases with _LT2 suffix are the second PTS
def get_bd_addr_for_test_case_name(test_case_name):
    if test_case_name.endswith('LT2'):
        return btp.lt2_addr_get()
    else:
        return btp.pts_addr_get()


# try to use local handler and fall back to gap handler
def bap_wid_hdl(wid, description, test_case_name):
    log("%s, %r, %r, %s", bap_wid_hdl.__name__, wid, description,
        test_case_name)
    module = sys.modules[__name__]

    try:
        handler = getattr(module, "hdl_wid_%d" % wid)
        return handler(WIDParams(wid, description, test_case_name))
    except AttributeError:
        return gen_wid_hdl(wid, description, test_case_name, False)

def hdl_wid_201(params: WIDParams):
    # Please configure the CODEC parameters on ASE ID x in Audio Stream Endpoint Characteristic.
    # we use codec info from test specification as there is no info from PTS
    pattern = '.*on ASE ID (\d+) in Audio.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    stack = get_stack()
    codec = stack.le_audio.get_codec()
    log("ASE Codec Setting %s, ASE ID %u", codec, ase_id)
    le_audio_configure_lc3(0, ase_id, codec, 1)
    return True

def hdl_wid_202(params: WIDParams):
    # Please start audio streaming, and set to Audio Stream Endpoint to STREAMING state for ASE ID x
    pattern = '.*for ASE ID (\d+)\.'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    return True

def hdl_wid_204(params: WIDParams):
    # Please initiate Server initiated DISABLE operation on ASE ID x in Audio Stream Endpoint Characteristic.
    pattern = '.*on ASE ID (\d+) in Audio.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    btp.ascs_disable(0, ase_id)
    return True

def hdl_wid_206(params: WIDParams):
    # Please initiate RELEASE operation on ASE ID x in Audio Stream Endpoint Characteristic.
    pattern = '.*on ASE ID (\d+) in Audio.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    btp.ascs_release(0, ase_id)
    return True

def hdl_wid_207(params: WIDParams):
    # Please initiate META UPDATE operation on ASE ID 3 in Audio Stream Endpoint Characteristic.
    pattern = '.*on ASE ID (\d+) in Audio.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    btp.ascs_update_metadata(0, ase_id)
    return True

def hdl_wid_208(params: WIDParams):
    # Lower tester is waiting RELEASED operation (IDLE or CODEC Configured state) on ASE ID x in Audio Stream Endpoint Characteristic.
    pattern = '.*on ASE ID (\d+) in Audio.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_id = int(desc_match.group(1))
    # IUT will automatically perform RELEASED operation
    return True

def hdl_wid_302(params: WIDParams):
    # Please configure ASE state to CODEC configured with ? ASE, Freq: ? KHz, Frame Duration: ? ms
    # we use codec info from test specification as octets per frame is not provided by PTS
    pattern = '.*with (SINK|SOURCE) ASE.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    ase_type = desc_match.group(1)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)
    codec = stack.le_audio.get_codec()

    le_audio_configure_lc3(ascs_chan_id, ase_id, codec, 1)
    return True


def hdl_wid_303(params: WIDParams):
    # Please configure ASE state to QoS Configured with 8_1_1 in SINK direction
    pattern = '.* (\d+_\d+)_(\d) .* (SINK|SOURCE) .*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False
    codec = desc_match.group(1)
    channels = int(desc_match.group(2))
    qos = desc_match.group(1) + '_' + desc_match.group(2)
    ase_type = desc_match.group(3)

    log("ASE Codec Setting %s, QoS Setting %s, type %s", codec, qos, ase_type)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)
    cig_id = 1
    cis_id = 1
    framing = 0

    # Codec
    frequency_hz, frame_duration_us, octets_per_frame = le_audio_codec_get_info(codec)
    log("ASE Codec LC3 frequency %u hz, frame duration %u us, octets per frame %u", frequency_hz, frame_duration_us, octets_per_frame)
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, 1, octets_per_frame)

    # CIG / QoS
    if ase_type == "SOURCE":
        cis_params = [(cis_id, 0, octets_per_frame)]
    else:
        cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info(qos)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_304(params: WIDParams):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    pattern = '.*(SINK|SOURCE) ASE.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False

    ase_type = desc_match.group(1)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)

    log("Configure %s ASE - ID %u to ENABLING", ase_type, ase_id)

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, 1, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    cis_params = [(cis_id, 0, octets_per_frame)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info('16_2_1')
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id, ase_id)

    # CIS
    cis_associations = [(cis_id, Addr.le_public, bd_addr)]
    btp.cis_create(cig_id, cis_associations)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(ascs_chan_id, ase_id)
    else:
        btp.cis_start_streaming(cig_id, cis_id)

    # Store reference for later, e.g. wdl 307
    ascs_client['ase_id'] = ase_id
    ascs_client['ase_type'] = ase_type

    return True


def hdl_wid_305(params: WIDParams):
    # Please configure ASE state to Enabling for SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    pattern = '.*(SINK|SOURCE) ASE.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False

    ase_type = desc_match.group(1)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, 1, octets_per_frame)

    # CIG / QoS - SOURCE
    cig_id = 1
    cis_id = 1
    framing = 0
    cis_params = [(cis_id, octets_per_frame, 0)]
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info('16_2_1')
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)
    btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id, ase_id)

    # "Wait" for ASE State ENABLING and Metadata update
    sleep(1)

    # Disable
    btp.ascs_disable(ascs_chan_id, ase_id)

    # BAP/UCL/SCC/BV-113
    btp.ascs_release(ascs_chan_id, ase_id)
    return True


def hdl_wid_306(params: WIDParams):
    # Please configure ASE state to Streaming for SINK/SOURCE ASE, Freq: 16KHz and Frame Duration: 10ms
    pattern = '.*(SINK|SOURCE) ASE.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False

    ase_type = desc_match.group(1)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)

    # Codec
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info('16_2')
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, 1, octets_per_frame)

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
    btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)

    # Enable
    btp.ascs_enable(ascs_chan_id, ase_id)

    # CIS
    cis_associations = [(cis_id, Addr.le_public, bd_addr)]
    btp.cis_create(cig_id, cis_associations)

    # send receiver ready if we are sink
    if ase_type == 'SOURCE':
        btp.ascs_receiver_start_ready(ascs_chan_id, ase_id)
    else:
        btp.cis_start_streaming(cig_id, cis_id)

    # Store reference for later, e.g. wdl 307
    ascs_client['ase_id'] = ase_id
    ascs_client['ase_type'] = ase_type

    return True


def hdl_wid_307(params: WIDParams):
    # Please configure ASE state to Disabling state. If server is Source, please initiate Receiver Stop Ready
    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    # get stored ase id, e.g. from wid 304
    ase_id = ascs_client['ase_id']
    ase_type = ascs_client['ase_type']

    log("Configure ASE %u to DISABLING", ase_id)
    btp.ascs_disable(ascs_chan_id, ase_id)

    if ase_type == 'SOURCE':
        log("Receiver Stop Ready ASE %u", ase_id)
        btp.ascs_receiver_stop_ready(ascs_chan_id, ase_id)

    return True


def hdl_wid_309(params: WIDParams):
    # Please configure ASE state to Releasing state.
    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_any_ase_id(ascs_client)
    btp.ascs_release(ascs_chan_id, ase_id)
    return True


def hdl_wid_310(params: WIDParams):
    # Please send Update Metadata Opcode with valid data.
    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_any_ase_id(ascs_client)
    btp.ascs_update_metadata(ascs_chan_id, ase_id)
    return True


def hdl_wid_311(params: WIDParams):
    # Please configure 1 SOURCE ASE with Config Setting: 8_1_1.\nAfter that, configure to streaming state.
    # Please configure 1 SINK ASE with Config Setting: IXIT.\nAfter that, configure to streaming state.
    # Please configure 2 SINK ASE with Config Setting: 16_2_1.\nAfter that, configure to streaming state.
    pattern = ".*configure (\d) (SINK|SOURCE) ASE.*Config Setting: (\w+)\."
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error in description")
        return False
    ase_count = int(desc_match.group(1))
    ase_type = desc_match.group(2)
    qos_string = desc_match.group(3)

    if qos_string == "IXIT":
        codec = '16_2'
        qos = '16_2_1'
    else:
        pattern = '(\d+_\d+)_(\d)'
        desc_match = re.match(pattern, qos_string)
        if not desc_match:
            logging.error("parsing error in " + qos_string)
            return False
        codec = desc_match.group(1)
        qos = desc_match.group(1) + '_' + desc_match.group(2)
    log("ASE Codec %s, Setting %s, QoS Setting %s", ase_type, codec, qos)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']

    if ase_type == "SOURCE":
        ase_ids = ascs_client['source_ases']
    else:
        ase_ids = ascs_client['sink_ases']

    # Get Audio Configuration from test spec
    audio_configuration = stack.le_audio.get_audio_configuration()
    (num_servers, cis_entries) = audio_configurations[audio_configuration]
    log("Audio Configuration %s -> num servers %u, cis entries %s", audio_configuration, num_servers, cis_entries)

    # map CIS entries onto available servers
    if num_servers == 2:
        if params.test_case_name.endswith('LT2'):
            cis_entries = cis_entries[1:2]
        else:
            cis_entries = cis_entries[0:1]
        log("Use CIS entry: %r", cis_entries[0])

    # Codec
    for (ase_id, cis_entry) in zip(ase_ids, cis_entries):
        (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec)
        if ase_type == "SOURCE":
            channels = cis_entry[0]
        else:
            channels = cis_entry[1]
        if channels > 1:
            audio_locations = 3
        else:
            audio_locations = 0
        log("ASE %u, audio locations 0x%x", ase_id, audio_locations)
        btp.ascs_configure_codec(ascs_chan_id, ase_id, 6, frequency_hz, frame_duration_us, audio_locations, octets_per_frame)

    # Use on CIG per LTs
    if params.test_case_name.endswith('LT2'):
        cig_id = 2
    else:
        cig_id = 1
    log("LT%u2 -> CIG ID %u", cig_id, cig_id)

    # CIG / QoS - SOURCE
    cis_id = 1
    cis_params = []
    for ase_id in ase_ids:
        framing = 0
        if ase_type == "SOURCE":
            cis_params.append((cis_id, 0, octets_per_frame))
        else:
            cis_params.append((cis_id, octets_per_frame, 0))
        cis_id += 1
    sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms = le_audio_qos_get_info(qos)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)

    cis_id = 1
    for ase_id in ase_ids:
        btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
        cis_id += 1

    # CIS
    cis_id = 1
    cis_associations = []
    for ase_id in ase_ids:
        cis_associations.append((cis_id, Addr.le_public, bd_addr))
        cis_id += 1
    btp.cis_create(cig_id, cis_associations)

    # "Wait" for ASE State STREAMING
    sleep(1)

    # Enable
    for ase_id in ase_ids:
        btp.ascs_enable(ascs_chan_id, ase_id)

    # "Wait" for ASE State STREAMING
    sleep(1)

    cis_id = 1
    for ase_id in ase_ids:
        if ase_type == 'SOURCE':
            # send receiver ready if we are sink
            btp.ascs_receiver_start_ready(ascs_chan_id, ase_id)
        else:
            btp.cis_start_streaming(cig_id, cis_id)
            cis_id += 1

    return True


def hdl_wid_313(params: WIDParams):
    # Please configure 1 SINK and 1 SOURCE ASE with Config Setting: 16_2_1.\nAfter that, configure both ASEes to streaming state
    # Please configure 1 SINK and 1 SOURCE ASE with Config Setting: IXIT.\nAfter that, configure both ASEes to streaming state.
    # Please configure 2 SINK and 1 SOURCE ASE with Config Setting: 16_2_1.\nAfter that, configure both ASEes to streaming state.
    pattern = ".*Config Setting: (\w+)\."
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error in description")
        return False

    if desc_match.group(1) == "IXIT":
        codec_name = '16_2'
        qos_name = '16_2_1'
    else:
        qos_string = desc_match.group(1)
        pattern = '(\d+_\d+)_(\d)'
        desc_match = re.match(pattern, qos_string)
        if not desc_match:
            logging.error("parsing error in " + qos_string)
            return False
        codec_name = desc_match.group(1)
        qos_name = desc_match.group(1) + '_' + desc_match.group(2)

    codec_format = 6
    (frequency_hz, frame_duration_us, octets_per_frame) = le_audio_codec_get_info(codec_name)
    log("ASE Codec %u, Setting %s, QoS Setting %s", codec_format, codec_name, qos_name)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    source_ase_ids = ascs_client['source_ases']
    sink_ase_ids = ascs_client['sink_ases']

    # Get Audio Configuration from test spec
    audio_configuration = stack.le_audio.get_audio_configuration()
    (num_servers, cis_entries) = audio_configurations[audio_configuration]
    log("Audio Configuration %s -> num servers %u, cis entries %s", audio_configuration, num_servers, cis_entries)

    # map CIS entries onto available servers
    if num_servers == 2:
        if params.test_case_name.endswith('LT2'):
            cis_entries = cis_entries[1:2]
        else:
            cis_entries = cis_entries[0:1]
        log("Use CIS entry: %r", cis_entries[0])

    # Assume: single CIS entry, max one source and sink ase

    # Codec
    for source_ase_id in source_ase_ids:
        channels = cis_entries[0][0]
        if channels > 1:
            audio_locations = 3
        else:
            audio_locations = 1
        log("ASE SOURCE %u: codec %u, Frequency %u, frame duration %u, octets %u, channels %u", source_ase_id, codec_format, frequency_hz,
            frame_duration_us, octets_per_frame, channels)
        btp.ascs_configure_codec(ascs_chan_id, source_ase_id, codec_format, frequency_hz, frame_duration_us, audio_locations, octets_per_frame)
    for sink_ase_id in sink_ase_ids:
        channels = cis_entries[0][1]
        if channels > 1:
            audio_locations = 3
        else:
            audio_locations = 1
        log("ASE SINK %u: codec %u, Frequency %u, frame duration %u, octets %u, channels %u", sink_ase_id, codec_format, frequency_hz,
            frame_duration_us, octets_per_frame, channels)
        btp.ascs_configure_codec(ascs_chan_id, sink_ase_id, codec_format, frequency_hz, frame_duration_us, audio_locations, octets_per_frame)

    # Use on CIG per LTs
    if params.test_case_name.endswith('LT2'):
        cig_id = 2
    else:
        cig_id = 1
    log("LT%u -> CIG ID %u", cig_id, cig_id)

    # Determine CIS Params based on Audio Configuration and map ase to cis
    cis_params = []
    cis_id = 1
    sink_cis_ids = []
    source_cis_ids = []
    for cis_entry in cis_entries:
        cis_params.append((cis_id, octets_per_frame * cis_entry[1], octets_per_frame * cis_entry[0]))
        if cis_entry[1] > 0:
            sink_cis_ids.append(cis_id)
        if cis_entry[0] > 0:
            source_cis_ids.append(cis_id)
        cis_id += 1

    # CIG
    (sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms) = le_audio_qos_get_info(qos_name)
    btp.cig_create(cig_id, sdu_interval_us, sdu_interval_us, framing, cis_params)

    # QoS
    for (source_ase_id, source_cis) in zip(source_ase_ids, source_cis_ids):
        log("ASE SOURCE %u uses CIS %u", source_ase_id, source_cis)
        btp.ascs_configure_qos(ascs_chan_id, source_ase_id, cig_id, source_cis, sdu_interval_us, framing, max_sdu_size,
                               retransmission_number, max_transport_latency_ms)
    for (sink_ase_id, sink_cis) in zip(sink_ase_ids, sink_cis_ids):
        log("ASE SINK %u uses CIS %u", sink_ase_id, sink_cis)
        btp.ascs_configure_qos(ascs_chan_id, sink_ase_id, cig_id, sink_cis, sdu_interval_us, framing, max_sdu_size,
                               retransmission_number, max_transport_latency_ms)

    # Enable
    for source_ase_id in source_ase_ids:
        btp.ascs_enable(ascs_chan_id, source_ase_id)
    for sink_ase_id in sink_ase_ids:
        btp.ascs_enable(ascs_chan_id, sink_ase_id)

    # CIS
    cis_id = 1
    cis_associations = []
    for cis_entry in cis_entries:
        cis_associations.append((cis_id, Addr.le_public, bd_addr))
        cis_id += 1
    btp.cis_create(cig_id, cis_associations)

    for source_ase_id in source_ase_ids:
        # send receiver ready if we are sink
        btp.ascs_receiver_start_ready(ascs_chan_id, source_ase_id)
    for sink_cis_id in sink_cis_ids:
        # start streaming if we are source
        btp.cis_start_streaming(cig_id, sink_cis_id)

    return True


def hdl_wid_314(params: WIDParams):
    # Please configure ASE state to CODEC configured with Vendor specific parameter in SOURCE/SINK ASE
    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_any_ase_id(ascs_client)
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 0xff, 48000, 10000, 1, 26)
    return True


def hdl_wid_315(params: WIDParams):
    # Please configure ASE state to QoS Configured with Vendor specific parameter in SOURCE/SINK ASE.
    pattern = '.*(SINK|SOURCE) ASE.*'
    desc_match = re.match(pattern, params.description)
    if not desc_match:
        logging.error("parsing error")
        return False

    ase_type = desc_match.group(1)

    stack = get_stack()
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    ascs_client = stack.le_audio.ascs_get_info(bd_addr)
    ascs_chan_id = ascs_client['chan_id']
    ase_id = get_ase_id_for_type(ascs_client, ase_type)

    # Codec
    btp.ascs_configure_codec(ascs_chan_id, ase_id, 0xff, 48000, 10000, 1, 26)

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
    btp.ascs_configure_qos(ascs_chan_id, ase_id, cig_id, cis_id, sdu_interval_us, framing, max_sdu_size, retransmission_number, max_transport_latency_ms)
    return True


def hdl_wid_364(params: WIDParams):
    # After processed audio stream data, please click OK.
    return True

def hdl_wid_376(params: WIDParams):
    # Please confirm received streaming data...'
    return True

def hdl_wid_377(params: WIDParams):
    # Please confirm sent streaming data...
    return True

def hdl_wid_382(params: WIDParams):
    # CIS connection is disconnected. Expect to receive Disabling state.
    return True

def hdl_wid_20100(params: WIDParams):
    # 'Please initiate a GATT connection to the PTS.'
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    log("%s -> %s", params.test_case_name, bd_addr)
    btp.gap_conn(bd_addr)
    return True

def hdl_wid_20001(params: WIDParams):
    # 'Verify that the Implementation Under Test (IUT) can accept GATT connect request from PTS.'
    # we already enabled advertisements
    return True

def hdl_wid_20106(params: WIDParams):
    # 'Please write to Client Characteristic Configuration Descriptor..'
    bd_addr = get_bd_addr_for_test_case_name(params.test_case_name)
    stack = get_stack()
    if stack.le_audio.ascs_get_info(bd_addr) is None:
        btp.ascs_connect(bd_addr, Addr.le_public)
    return True
