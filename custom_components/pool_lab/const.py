"""Constants for the Pool Lab integration."""

from __future__ import annotations

from enum import IntEnum, IntFlag

DOMAIN = "pool_lab"
DEFAULT_PORT = 8080

# mDNS discovery
MDNS_SERVICE_TYPE = "_http._tcp.local."
MDNS_HOSTNAME_PREFIX = "POOLLAB_"


class OutputMode(IntEnum):
    """Mode for controllable outputs (filter, AUX, groups)."""

    OFF = 0
    ON = 1
    AUTO = 2


class PoolSpaMode(IntEnum):
    """Pool or Spa mode selection."""

    POOL = 0
    SPA = 1


class PumpSpeed(IntEnum):
    """Pump speed levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class SystemFlag(IntFlag):
    """FG1 system configuration flags (bits 0-31)."""

    CHLORI = 1 << 1
    CHROMA = 1 << 2
    EXPAN = 1 << 3
    MS_PUMP = 1 << 4
    VALVE3 = 1 << 5
    VALVE4 = 1 << 6
    AUX1 = 1 << 7
    AUX2 = 1 << 8
    AUX3 = 1 << 9
    AUX4 = 1 << 10
    AUX5 = 1 << 11
    AUX6 = 1 << 12
    AUX7 = 1 << 13
    AUX8 = 1 << 14
    AUX9 = 1 << 15
    AUX10 = 1 << 16
    SOLARPOOL = 1 << 17
    SOLARSPA = 1 << 18
    HEATPOOL = 1 << 19
    HEATSPA = 1 << 20
    POOL = 1 << 21
    SPA = 1 << 22
    AUX1_5 = 1 << 23
    AUX6_10 = 1 << 24
    VALVE1_4 = 1 << 25
    CL_TOTAL = 1 << 26
    POOL_LIGHT_GROUP = 1 << 27
    SPA_LIGHT_GROUP = 1 << 28
    SPA_BOOST_GROUP = 1 << 29
    SPA_BLOWER_GROUP = 1 << 30
    INFLOOR_GROUP = 1 << 31


class SystemFlag2(IntFlag):
    """FG2 system configuration flags (bits 32-33)."""

    CLEANER_GROUP = 1 << 0
    FOUNTAIN_GROUP = 1 << 1


class ChlorinatorStatus(IntFlag):
    """CHLORSTAT chlorinator status flags."""

    LOW_FLOW = 1 << 0
    LO_SALT = 1 << 1
    LO_SALT_OFF = 1 << 2
    HI_SALT = 1 << 3
    HI_SALT_OFF = 1 << 4
    PUMP_PROTECT = 1 << 5
    CHLR_CMD = 1 << 6
    CHLR_DUTY = 1 << 7
    CELLFLOW = 1 << 8
    OUTPUT_FAULT = 1 << 9


class SystemStatus(IntFlag):
    """SYSSTAT system status flags."""

    DEFAULTS_USED = 1 << 0
    WATER_SENSOR_FAULT = 1 << 1
    HOT_SENSOR_FAULT = 1 << 2
    COLD_SENSOR_FAULT = 1 << 3


class WaterAnalyzerStatus(IntFlag):
    """CHROMSTAT water analyzer status flags."""

    CL_AT_TARG = 1 << 0
    CHLOR_ON = 1 << 1
    ACID_ON = 1 << 2
    SUST_CL_DEV = 1 << 3
    SUST_PH_DEV = 1 << 4
    CL_KNOWN = 1 << 5
    PH_KNOWN = 1 << 6
    CT_KNOWN = 1 << 7
