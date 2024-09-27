#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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
import struct
from argparse import Namespace

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp, defs
from autopts.pybtp.btp import lt2_addr_get, lt2_addr_type_get, pts_addr_get, pts_addr_type_get
from autopts.pybtp.defs import AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS
from autopts.pybtp.types import WIDParams, AudioDir, ASCSState, CODEC_CONFIG_SETTINGS, create_lc3_ltvs_bytes
from autopts.wid import generic_wid_hdl

log = logging.debug

QOS_CONFIG_SETTINGS_GAMING = {
    # Set_Name: (Codec_Config, SDU_interval, Framing, Maximum_SDU_Size, Retransmission_Number, Max_Transport_Latency_ms, Presentation_Delay)
    '16_1_gs': ("16_1",  7500, 0x00,  30, 1, 15, 60000),
    '16_2_gs': ("16_2", 10000, 0x00,  40, 1, 20, 60000),
    '32_1_gs': ("32_1", 7500,  0x00,  60, 1, 15, 60000),
    '32_2_gs': ("32_2", 10000, 0x00,  80, 1, 20, 60000),
    '48_1_gs': ("48_1",  7500, 0x00,  75, 1, 15, 60000),
    '48_2_gs': ("48_2", 10000, 0x00, 100, 1, 20, 60000),
    '16_1_gr': ("16_1",  7500, 0x00,  30, 1, 15, 10000),
    '16_2_gr': ("16_2", 10000, 0x00,  40, 1, 20, 10000),
    '32_1_gr': ("32_1",  7500, 0x00,  60, 1, 15, 10000),
    '32_2_gr': ("32_2", 10000, 0x00,  80, 1, 20, 10000),
    '48_1_gr': ("48_1",  7500, 0x00,  75, 1, 15, 10000),
    '48_2_gr': ("48_2", 10000, 0x00, 100, 1, 20, 10000),
    '48_3_gr': ("48_3",  7500, 0x00,  90, 1, 15, 10000),
    '48_4_gr': ("48_4", 10000, 0x00, 120, 1, 20, 10000),
}


# Audio Configuration from BAP TS
# - Each configuration has number of servers and an array of server entries
# - Each server entry has an array of CIS entries
# - Each CIS entry specifies number of audio channels on local and remote sinks (matching the topology field)
# == local sink channel <-> remote source channels
audio_configurations = {
    "AC 1":      (1, [[(0, 1)]]),
    "AC 2":      (1, [[(1, 0)]]),
    "AC 3":      (1, [[(1, 1)]]),
    "AC 4":      (1, [[(0, 2)]]),
    "AC 5":      (1, [[(1, 2)]]),
    "AC 6(i)":   (1, [[(0, 1), (0, 1)]]),
    "AC 6(ii)":  (2, [[(0, 1)        ], [(0, 1)]]),
    "AC 7(i)":   (1, [[(0, 1), (1, 0)]]),
    "AC 7(ii)":  (2, [[(0, 1)        ], [(1, 0)]]),
    "AC 8(i)":   (1, [[(0, 1), (1, 1)]]),
    "AC 8(ii)":  (2, [[(0, 1)        ], [(1, 1)]]),
    "AC 9(i)":   (1, [[(1, 0), (1, 0)]]),
    "AC 9(ii)":  (2, [[(1, 0)        ], [(1, 0)]]),
    "AC 10":     (1, [[(2, 0)]]),
    "AC 11(i)":  (1, [[(1, 1), (1, 1)]]),
    "AC 11(ii)": (2, [[(1, 1)        ], [(1, 1)]]),
}


def gmap_wid_hdl(wid, description, test_case_name):
    log(f'{gmap_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')
    return generic_wid_hdl(wid, description, test_case_name, [__name__])


def create_default_config():
    return Namespace(addr=pts_addr_get(),
                     addr_type=pts_addr_type_get(),
                     vid=0x0000,
                     cid=0x0000,
                     coding_format=0x06,
                     frames_per_sdu=0x01,
                     audio_locations=0x01,
                     cig_id=0x00,
                     cis_id=0x00,
                     presentation_delay=40000,
                     qos_config=None,
                     codec_set_name=None,
                     codec_ltvs=None,
                     metadata_ltvs=None,
                     mono=None)


def config_for_qos_name(qos_name):
    config = create_default_config()
    config.qos_set_name = qos_name

    (config.codec_set_name,
     config.sdu_interval,
     config.framing,
     config.max_sdu_size,
     config.retransmission_number,
     config.max_transport_latency,
     config.presentation_delay) = QOS_CONFIG_SETTINGS_GAMING[config.qos_set_name]

    (config.sampling_freq,
     config.frame_duration,
     config.octets_per_frame) = CODEC_CONFIG_SETTINGS[config.codec_set_name]

    # streaming audio context = game
    config.metadata_ltvs = struct.pack('<BBH', 3, AUDIO_METADATA_STREAMING_AUDIO_CONTEXTS, 0x0008)
    return config


# wid handlers section begin

gmap_ugg_unidirectional_settings = {
    # test_case_name: (audio configuration, qos name, audio channel allocation, LT_count)
    "GMAP/UGG/LLU/BV-63-C": ("AC 1",     "32_1_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-64-C": ("AC 1",     "32_2_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-51-C": ("AC 1",     "48_1_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-52-C": ("AC 1",     "48_2_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-53-C": ("AC 1",     "48_3_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-54-C": ("AC 1",     "48_4_gr", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-87-C": ("AC 2",     "16_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-88-C": ("AC 2",     "16_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-55-C": ("AC 2",     "32_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-56-C": ("AC 2",     "32_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-57-C": ("AC 2",     "48_1_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-58-C": ("AC 2",     "48_2_gs", "Not allocated", 1),
    "GMAP/UGG/LLU/BV-69-C": ("AC 4",     "32_1_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-70-C": ("AC 4",     "32_2_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-59-C": ("AC 4",     "48_1_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-60-C": ("AC 4",     "48_2_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-61-C": ("AC 4",     "48_3_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-62-C": ("AC 4",     "48_4_gr", "0b11",          1),
    "GMAP/UGG/LLU/BV-73-C": ("AC 6(i)",  "32_1_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-74-C": ("AC 6(i)",  "32_2_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-01-C": ("AC 6(i)",  "48_1_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-02-C": ("AC 6(i)",  "48_2_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-03-C": ("AC 6(i)",  "48_3_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-04-C": ("AC 6(i)",  "48_4_gr", "0b01 and 0b10", 1),
    "GMAP/UGG/LLU/BV-75-C": ("AC 6(ii)", "32_1_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-76-C": ("AC 6(ii)", "32_2_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-05-C": ("AC 6(ii)", "48_1_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-06-C": ("AC 6(ii)", "48_2_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-07-C": ("AC 6(ii)", "48_3_gr", "0b01 and 0b10", 2),
    "GMAP/UGG/LLU/BV-08-C": ("AC 6(ii)", "48_4_gr", "0b01 and 0b10", 2),
}

gmap_ugg_bidirectional_settings = {
    # test_case_name: (audio configuration, UGG to UGT QoS Setting, audio channel allocation, UGT to UGG QoS Setting, LT_count)
    "GMAP/UGG/LLU/BV-89-C":  ("AC 3",      "32_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-90-C":  ("AC 3",      "32_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-91-C":  ("AC 3",      "48_1_gr", "Not allocated", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-92-C":  ("AC 3",      "48_2_gr", "Not allocated", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-65-C":  ("AC 3",      "32_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-66-C":  ("AC 3",      "32_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-09-C":  ("AC 3",      "48_1_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-10-C":  ("AC 3",      "48_2_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-11-C":  ("AC 3",      "48_1_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-12-C":  ("AC 3",      "48_2_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-13-C":  ("AC 3",      "48_3_gr", "Not allocated", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-14-C":  ("AC 3",      "48_4_gr", "Not allocated", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-67-C":  ("AC 3",      "48_3_gr", "Not allocated", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-68-C":  ("AC 3",      "48_4_gr", "Not allocated", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-93-C":  ("AC 5",      "32_1_gr", "0b11",          "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-94-C":  ("AC 5",      "32_2_gr", "0b11",          "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-95-C":  ("AC 5",      "48_1_gr", "0b11",          "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-96-C":  ("AC 5",      "48_2_gr", "0b11",          "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-71-C":  ("AC 5",      "32_1_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-72-C":  ("AC 5",      "32_2_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-15-C":  ("AC 5",      "48_1_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-16-C":  ("AC 5",      "48_2_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-17-C":  ("AC 5",      "48_1_gr", "0b11",          "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-18-C":  ("AC 5",      "48_2_gr", "0b11",          "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-19-C":  ("AC 5",      "48_3_gr", "0b11",          "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-20-C":  ("AC 5",      "48_4_gr", "0b11",          "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-97-C":  ("AC 7(ii)",  "32_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-98-C":  ("AC 7(ii)",  "32_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-99-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-100-C": ("AC 7(ii)",  "48_2_gr", "Not allocated", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-41-C":  ("AC 7(ii)",  "32_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-42-C":  ("AC 7(ii)",  "32_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-21-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-22-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-23-C":  ("AC 7(ii)",  "48_1_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-24-C":  ("AC 7(ii)",  "48_2_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-25-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-26-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-77-C":  ("AC 7(ii)",  "48_3_gr", "Not allocated", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-78-C":  ("AC 7(ii)",  "48_4_gr", "Not allocated", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-101-C": ("AC 8(i)",   "32_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-102-C": ("AC 8(i)",   "32_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-103-C": ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-104-C": ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-79-C":  ("AC 8(i)",   "32_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-80-C":  ("AC 8(i)",   "32_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-27-C":  ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-28-C":  ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-29-C":  ("AC 8(i)",   "48_1_gr", "0b01 and 0b10", "48_1_gs", 1),
    "GMAP/UGG/LLU/BV-30-C":  ("AC 8(i)",   "48_2_gr", "0b01 and 0b10", "48_2_gs", 1),
    "GMAP/UGG/LLU/BV-31-C":  ("AC 8(i)",   "48_3_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-32-C":  ("AC 8(i)",   "48_4_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-105-C": ("AC 8(ii)",  "32_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-106-C": ("AC 8(ii)",  "32_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-107-C": ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-108-C": ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-81-C":  ("AC 8(ii)",  "32_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-82-C":  ("AC 8(ii)",  "32_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-33-C":  ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-34-C":  ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-35-C":  ("AC 8(ii)",  "48_1_gr", "0b01 and 0b10", "48_1_gs", 2),
    "GMAP/UGG/LLU/BV-36-C":  ("AC 8(ii)",  "48_2_gr", "0b01 and 0b10", "48_2_gs", 2),
    "GMAP/UGG/LLU/BV-37-C":  ("AC 8(ii)",  "48_3_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-38-C":  ("AC 8(ii)",  "48_4_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-109-C": ("AC 11(i)",  "32_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-110-C": ("AC 11(i)",  "32_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-111-C": ("AC 11(i)",  "48_1_gr", "0b01 and 0b10", "16_1_gs", 1),
    "GMAP/UGG/LLU/BV-112-C": ("AC 11(i)",  "48_2_gr", "0b01 and 0b10", "16_2_gs", 1),
    "GMAP/UGG/LLU/BV-83-C":  ("AC 11(i)",  "32_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-84-C":  ("AC 11(i)",  "32_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-39-C":  ("AC 11(i)",  "48_1_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-40-C":  ("AC 11(i)",  "48_2_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-43-C":  ("AC 11(i)",  "48_3_gr", "0b01 and 0b10", "32_1_gs", 1),
    "GMAP/UGG/LLU/BV-44-C":  ("AC 11(i)",  "48_4_gr", "0b01 and 0b10", "32_2_gs", 1),
    "GMAP/UGG/LLU/BV-113-C": ("AC 11(ii)", "32_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-114-C": ("AC 11(ii)", "32_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-115-C": ("AC 11(ii)", "48_1_gr", "0b01 and 0b10", "16_1_gs", 2),
    "GMAP/UGG/LLU/BV-116-C": ("AC 11(ii)", "48_2_gr", "0b01 and 0b10", "16_2_gs", 2),
    "GMAP/UGG/LLU/BV-85-C":  ("AC 11(ii)", "32_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-86-C":  ("AC 11(ii)", "32_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-45-C":  ("AC 11(ii)", "48_1_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-46-C":  ("AC 11(ii)", "48_2_gr", "0b01 and 0b10", "32_2_gs", 2),
    "GMAP/UGG/LLU/BV-49-C":  ("AC 11(ii)", "48_3_gr", "0b01 and 0b10", "32_1_gs", 2),
    "GMAP/UGG/LLU/BV-50-C":  ("AC 11(ii)", "48_4_gr", "0b01 and 0b10", "32_2_gs", 2)
}

gmap_ugg_audio_location_mapping = {
    "Not allocated" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT],
    "0b11" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT | defs.PACS_AUDIO_LOCATION_FRONT_RIGHT],
    "0b01 and 0b10" : [defs.PACS_AUDIO_LOCATION_FRONT_LEFT, defs.PACS_AUDIO_LOCATION_FRONT_RIGHT]
}


def hdl_wid_ugg_unidirectional(params: WIDParams):
    """
        Please configure 1 SINK ASE with Config Setting: .
    """

    lt1_test_name = params.test_case_name
    stack = get_stack()

    # get config
    audio_configuration, qos_name, audio_channel_allocation, lt_count = gmap_ugg_unidirectional_settings[lt1_test_name]
    log(gmap_ugg_unidirectional_settings[lt1_test_name])

    default_config = config_for_qos_name(qos_name)

    ases= []
    cig_id = 0x00
    cis_id = 0x00

    num_servers, server_entries = audio_configurations[audio_configuration]
    if num_servers != lt_count:
        log("Error: num servers incorrect")
        return False

    audio_location_list = gmap_ugg_audio_location_mapping[audio_channel_allocation].copy()
    log(f"audio location list: {audio_location_list}")

    lt_index = 0
    for cis_entries in server_entries:

        if lt_index == 0:
            addr = pts_addr_get()
            addr_type = pts_addr_type_get()
        else:
            addr = lt2_addr_get()
            addr_type = lt2_addr_type_get()

        for source_channels, sink_channels in cis_entries:
            if sink_channels > 0:

                audio_dir = AudioDir.SINK

                # Find ID of the ASE(s)
                ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
                if ev is None:
                    log(f"Could not find ASE for direction {audio_dir} on LT {lt_index+1}")
                    return False

                _, _, _, ase_id = ev

                audio_location = audio_location_list.pop()
                logging.debug(f"Using ASE_ID: {ase_id} for Location: {audio_location}")

                config = Namespace(**vars(default_config))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          sink_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            if source_channels > 0:

                audio_dir = AudioDir.SOURCE

                # Find ID of the ASE(s)
                ev = stack.bap.wait_ase_found_ev(addr_type, addr, audio_dir, 30, remove=True)
                if ev is None:
                    log(f"Could not find ASE for direction {audio_dir} on LT {lt_index + 1}")
                    return False

                _, _, _, ase_id = ev

                audio_location = audio_location_list.pop()
                logging.debug(f"Using ASE_ID: {ase_id} for Location: {audio_location}")

                config = Namespace(**vars(default_config))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          source_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            cis_id += 1

        lt_index += 1

    btp.cap_unicast_audio_start(cig_id, defs.CAP_UNICAST_AUDIO_START_SET_TYPE_AD_HOC)
    ev = stack.cap.wait_unicast_start_completed_ev(cig_id, 10)
    if ev is None:
        return False

    # We could wait for this, but Zephyr controller has issue with the second CIS,
    # so PTS does not send Streaming notification.
    for config in ases:
        # Wait for the ASE states to be changed to streaming
        ev = stack.ascs.wait_ascs_ase_state_changed_ev(config.addr_type,
                                                       config.addr,
                                                       config.ase_id,
                                                       ASCSState.STREAMING,
                                                       20)
        if ev is None:
            log('hdl_wid_ugg_unidirectional exit, not streaming')
            return False

    return True


def hdl_wid_ugg_bidirectional(params: WIDParams):
    """
    Please configure 1 SINK and 1 SOURCE ASE with Config Setting: .
    After that, configure both ASEes to streaming state.
    """

    lt1_test_name = params.test_case_name
    stack = get_stack()

    # get config
    audio_configuration, ugg_to_ugt_qos_name, audio_channel_allocation, ugt_to_ugg_qos_name, lt_count = gmap_ugg_bidirectional_settings[lt1_test_name]
    log(gmap_ugg_bidirectional_settings[lt1_test_name])

    default_config_ugg_to_ugt = config_for_qos_name(ugg_to_ugt_qos_name)
    default_config_ugt_to_ugg = config_for_qos_name(ugt_to_ugg_qos_name)

    num_servers, server_entries = audio_configurations[audio_configuration]
    if num_servers != lt_count:
        log("Error: num servers incorrect")
        return False

    audio_location_list = gmap_ugg_audio_location_mapping[audio_channel_allocation].copy()

    # get ASEs from BAP events and store in servers array
    servers = []
    for lt_index in range(lt_count):
        if lt_index == 0:
            addr = pts_addr_get()
            addr_type = pts_addr_type_get()
        else:
            addr = lt2_addr_get()
            addr_type = lt2_addr_type_get()

        # get Sink ASEs
        sink_ases = []
        while True:
            ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SINK, 1, remove=True)
            if ev is None:
                break
            _, _, _, ase_id = ev
            sink_ases.append(ase_id)

        # get Source ASEs
        source_ases = []
        while True:
            ev = stack.bap.wait_ase_found_ev(addr_type, addr, AudioDir.SOURCE, 1, remove=True)
            if ev is None:
                break
            _, _, _, ase_id = ev
            source_ases.append(ase_id)

        log(f"LT {lt_index+1} - {addr}({addr_type}): Sink ASEs {sink_ases}, Source ASEs {source_ases}")
        servers.append((lt_index, addr, addr_type, sink_ases, source_ases))
        lt_index += 1

    # calculate number of required sink and source ases per LT and select one
    assigned_servers = []
    total_sink_ases = 0
    for cis_entries in server_entries:
        num_sink_ases_required   = 0
        num_source_ases_required = 0
        for source_channels, sink_channels in cis_entries:
            if sink_channels > 0:
                num_sink_ases_required += 1
                total_sink_ases += 1
            if source_channels > 0:
                num_source_ases_required += 1

        # find suitable server
        found_lt = False
        for  server_info in servers:
            (lt_index, _, _, sink_ases, source_ases) = server_info
            if len(sink_ases) == num_sink_ases_required and len(source_ases) == num_source_ases_required:
                assigned_servers.append(server_info)
                found_lt = True

        if not found_lt:
                log(f"No LT with {num_sink_ases_required} Sink ASEs and {num_source_ases_required} Source ASEs available")
                return False

    # sanity check: no test has more than 2 Sink ASEs total
    if total_sink_ases > 2:
        log(f"Audio configuration {audio_configuration} requires more than 2 Sink ASEs")
        return False

    # setup ASEs
    ases= []
    cig_id = 0x00
    cis_id = 0x00
    for cis_entries in server_entries:

        (lt_index, addr, addr_type, sink_ases, source_ases) = assigned_servers.pop(0)

        for source_channels, sink_channels in cis_entries:

            if sink_channels > 0:

                ase_id = sink_ases.pop(0)
                audio_location = audio_location_list.pop()

                logging.debug(f"Using SINK ASE_ID: {ase_id} on LT {lt_index+1}")

                config = Namespace(**vars(default_config_ugg_to_ugt))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          sink_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            if source_channels > 0:

                ase_id = source_ases.pop(0)
                audio_location = 0

                logging.debug(f"Using Source ASE_ID: {ase_id} on LT {lt_index+1}")

                config = Namespace(**vars(default_config_ugt_to_ugg))

                # Perform Codec Config operation
                config.ase_id = ase_id
                config.cig_id = cig_id
                config.cis_id = cis_id
                config.addr = addr
                config.addr_type = addr_type
                config.codec_ltvs = create_lc3_ltvs_bytes(config.sampling_freq,
                                                          config.frame_duration,
                                                          audio_location,
                                                          config.octets_per_frame,
                                                          source_channels * config.frames_per_sdu)

                btp.cap_unicast_setup_ase(config, config.addr_type, config.addr)
                stack.bap.ase_configs.append(config)

                ases.append(config)

            cis_id += 1

    btp.cap_unicast_audio_start(cig_id, defs.CAP_UNICAST_AUDIO_START_SET_TYPE_AD_HOC)
    ev = stack.cap.wait_unicast_start_completed_ev(cig_id, 10)
    if ev is None:
        return False

    # We could wait for this, but Zephyr controller has issue with the second CIS,
    # so PTS does not send Streaming notification.
    for config in ases:
        # Wait for the ASE states to be changed to streaming
        ev = stack.ascs.wait_ascs_ase_state_changed_ev(config.addr_type,
                                                       config.addr,
                                                       config.ase_id,
                                                       ASCSState.STREAMING,
                                                       20)
        if ev is None:
            log('hdl_wid_ugg_bidirectional exit, not streaming')
            return False

    return True


def hdl_wid_311_and_313(params: WIDParams):
    # LT1 does all config
    if params.test_case_name.endswith('LT2'):
        return True

    tc_name = params.test_case_name
    if tc_name in gmap_ugg_unidirectional_settings:
        return hdl_wid_ugg_unidirectional(params)
    elif tc_name in gmap_ugg_bidirectional_settings:
        return hdl_wid_ugg_bidirectional(params)
    else:
        log("{tc_name} neither in hdl_wid_ugg_unidirectional nor hdl_wid_ugg_bidirectional")
        return False


def hdl_wid_311(params: WIDParams):
    """
        Please configure 1 SINK ASE with Config Setting: .
    """
    return hdl_wid_311_and_313(params)


def hdl_wid_313(params: WIDParams):
    """
    Please configure 1 SINK and 1 SOURCE ASE with Config Setting: .
    After that, configure both ASEes to streaming state.
    """
    return hdl_wid_311_and_313(params)


def hdl_wid_364(_: WIDParams):
    """
    After processed audio stream data, please click OK.
    """

    return True


def hdl_wid_558(_: WIDParams):
    """
    Please click ok if the IUT is in streaming state.
    """

    # ToDo: verify streaming state

    return True



def hdl_wid_20100(params: WIDParams):
    """
        Please initiate a GATT connection to the PTS.
        Description: Verify that the Implementation Under Test (IUT) can initiate a GATT connect request to the PTS.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    btp.gap_conn(addr, addr_type)
    stack.gap.wait_for_connection(timeout=10, addr=addr)
    stack.gap.gap_wait_for_sec_lvl_change(level=2, timeout=30, addr=addr)

    return True


def hdl_wid_20106(params: WIDParams):
    """
        Please write to Client Characteristic Configuration Descriptor of ASE
        Control Point characteristic to enable notification.
    """
    if params.test_case_name.endswith('LT2'):
        addr = lt2_addr_get()
        addr_type = lt2_addr_type_get()
    else:
        addr = pts_addr_get()
        addr_type = pts_addr_type_get()

    stack = get_stack()
    peer = stack.bap.get_peer(addr_type, addr)
    if peer.discovery_completed:
        log('Skip BAP discovery, discovery completed before')

        # Skip if discovery has been done already
        return True

    btp.bap_discover(addr_type, addr)
    stack.bap.wait_discovery_completed_ev(addr_type, addr, 30)

    return True
