"""Protocol layer for Pool Lab device communication.

Handles command construction and response parsing. This module is
purely functional — no I/O, no state. It translates between Python
types and the wire format described in docs/protocol.md.
"""

from __future__ import annotations

import logging
import re

from .const import (
    ChlorinatorStatus,
    OutputMode,
    PoolSpaMode,
    PumpSpeed,
    SystemFlag,
    SystemFlag2,
    SystemStatus,
    WaterAnalyzerStatus,
)
from .models import PoolLabState

_LOGGER = logging.getLogger(__name__)

# Pattern to split status update into key=value pairs
_STATUS_PAIR_RE = re.compile(r"([A-Za-z0-9_# \[\]]+)=([^;]*)")


# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------


def cmd_status_request() -> str:
    """Build a status request command."""
    return "up;\r"


def cmd_filter(mode: OutputMode | None = None) -> str:
    """Build a filter command. None = toggle."""
    if mode is None:
        return "fi;\r"
    return f"fi,{mode.value};\r"


def cmd_pool_spa(mode: PoolSpaMode | None = None) -> str:
    """Build a pool/spa mode command. None = toggle."""
    if mode is None:
        return "ps;\r"
    return f"ps,{mode.value};\r"


def cmd_solar_heat(mode: OutputMode | None = None) -> str:
    """Build a solar heat command. None = toggle."""
    if mode is None:
        return "sh;\r"
    return f"sh,{int(mode != OutputMode.OFF)};\r"


def cmd_heater(mode: OutputMode | None = None) -> str:
    """Build a heater command. None = toggle."""
    if mode is None:
        return "ht;\r"
    return f"ht,{int(mode != OutputMode.OFF)};\r"


def cmd_aux(number: int, mode: OutputMode | None = None) -> str:
    """Build an AUX output command. None = toggle."""
    if not 1 <= number <= 9:
        raise ValueError(f"AUX number must be 1-9, got {number}")
    if mode is None:
        return f"a{number};\r"
    return f"a{number},{mode.value};\r"


def cmd_valve(number: int, mode: OutputMode | None = None) -> str:
    """Build a valve command. None = toggle."""
    if number not in (3, 4):
        raise ValueError(f"Valve number must be 3 or 4, got {number}")
    if mode is None:
        return f"v{number};\r"
    return f"v{number},{mode.value};\r"


def cmd_pool_light(mode: OutputMode | None = None) -> str:
    """Build a pool lights group command."""
    if mode is None:
        return "pl;\r"
    return f"pl,{mode.value};\r"


def cmd_spa_light(mode: OutputMode | None = None) -> str:
    """Build a spa lights group command."""
    if mode is None:
        return "sl;\r"
    return f"sl,{mode.value};\r"


def cmd_spa_boost(mode: OutputMode | None = None) -> str:
    """Build a spa boost group command."""
    if mode is None:
        return "sb;\r"
    return f"sb,{mode.value};\r"


def cmd_blower(mode: OutputMode | None = None) -> str:
    """Build a blower group command."""
    if mode is None:
        return "bl;\r"
    return f"bl,{mode.value};\r"


def cmd_infloor(mode: OutputMode | None = None) -> str:
    """Build an infloor cleaning group command."""
    if mode is None:
        return "if;\r"
    return f"if,{mode.value};\r"


def cmd_cleaner(mode: OutputMode | None = None) -> str:
    """Build a cleaner group command."""
    if mode is None:
        return "cn;\r"
    return f"cn,{mode.value};\r"


def cmd_fountain(mode: OutputMode | None = None) -> str:
    """Build a fountain group command."""
    if mode is None:
        return "fo;\r"
    return f"fo,{mode.value};\r"


def cmd_pool_temp_target(temp_celsius: float) -> str:
    """Build a pool temperature target command."""
    return f"sp,{int(temp_celsius * 10)};\r"


def cmd_spa_temp_target(temp_celsius: float) -> str:
    """Build a spa temperature target command."""
    return f"ss,{int(temp_celsius * 10)};\r"


def cmd_ph_target(ph: float) -> str:
    """Build a pH target command."""
    return f"ph,{int(ph * 10)};\r"


def cmd_chlorine_target(cl_ppm: float) -> str:
    """Build a free chlorine target command."""
    return f"cl,{int(cl_ppm * 10)};\r"


def cmd_pump_speed(speed: PumpSpeed) -> str:
    """Build a pump speed override command."""
    return f"so,{speed.value};\r"


def cmd_chlorinator_output(percent: int) -> str:
    """Build a chlorinator output % command (only without ASP module)."""
    if not 0 <= percent <= 100:
        raise ValueError(f"Chlorinator output must be 0-100, got {percent}")
    return f"co,{percent};\r"


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_status_update(raw: str) -> PoolLabState:
    """Parse a status update string into a PoolLabState.

    The raw string is semicolon-delimited KEY=VALUE pairs.
    Unknown keys are logged at debug level and skipped.
    """
    state = PoolLabState()
    pairs = _STATUS_PAIR_RE.findall(raw)

    for key, value in pairs:
        key = key.strip()
        value = value.strip()
        try:
            _apply_field(state, key, value)
        except (ValueError, KeyError) as err:
            _LOGGER.debug("Failed to parse field %s=%s: %s", key, value, err)

    return state


def _apply_field(state: PoolLabState, key: str, value: str) -> None:
    """Apply a single parsed field to the state object."""
    # System flags
    if key == "FG1":
        state.system_flags = SystemFlag(int(value, 16))
    elif key == "FG2":
        state.system_flags_2 = SystemFlag2(int(value, 16))
    elif key == "CHLORSTAT":
        state.chlorinator_status = ChlorinatorStatus(int(value, 16))
    elif key == "SYSSTAT":
        state.system_status = SystemStatus(int(value, 16))
    elif key == "CHROMSTAT":
        state.water_analyzer_status = WaterAnalyzerStatus(int(value, 16))

    # Core modes
    elif key == "FILTER":
        state.filter_mode = OutputMode(int(value))
    elif key == "SPAMODE":
        state.spa_mode = PoolSpaMode(int(value))
    elif key == "SOLARMODE":
        state.solar_mode = OutputMode(int(value))
    elif key == "HEATMODE":
        state.heat_mode = OutputMode(int(value))

    # Pump
    elif key == "PUMPSPEED":
        state.pump_speed = PumpSpeed(int(value))

    # Chlorinator
    elif key == "CHLORTARG":
        state.chlorinator_target = int(value)
    elif key == "CHLORACT":
        state.chlorinator_actual = int(value)

    # Temperature
    elif key == "WATERTEMP":
        state.water_temp = int(value) / 10.0
    elif key == "POOLSET":
        state.pool_set_temp = float(value)
    elif key == "SPASET":
        state.spa_set_temp = float(value)

    # Water chemistry
    elif key == "CLLEVEL":
        state.chlorine_level = float(value)
    elif key == "PHLEVEL":
        state.ph_level = float(value)
    elif key == "CLTARG":
        state.chlorine_target = float(value)
    elif key == "PHTARG":
        state.ph_target = float(value)

    # AUX outputs
    elif _is_aux_key(key):
        num = _parse_aux_number(key)
        state.aux_modes[num] = OutputMode(int(value))

    # Valves
    elif key == "VALVE3":
        state.valve3_mode = OutputMode(int(value))
    elif key == "VALVE4":
        state.valve4_mode = OutputMode(int(value))

    # Grouped outputs
    elif key == "POOLLIGHT":
        state.pool_light = OutputMode(int(value))
    elif key == "SPALIGHT":
        state.spa_light = OutputMode(int(value))
    elif key == "SPABOOST":
        state.spa_boost = OutputMode(int(value))
    elif key == "SPABLOWER":
        state.spa_blower = OutputMode(int(value))
    elif key == "INFLOOR":
        state.infloor = OutputMode(int(value))
    elif key == "CLEANER":
        state.cleaner = OutputMode(int(value))
    elif key == "FOUNTAIN":
        state.fountain = OutputMode(int(value))

    # Reagents
    elif key == "REAGENT #1":
        state.reagent_ph = value == "1"
    elif key == "REAGENT #2":
        state.reagent_cl1 = value == "1"
    elif key == "REAGENT #3":
        state.reagent_cl2 = value == "1"
    elif key == "REAGENT #4":
        state.reagent_total_cl = value == "1"

    # History
    elif key == "PHTH":
        state.ph_history = _parse_history(value)
    elif key == "CLTH":
        state.cl_history = _parse_history(value)

    # Timers
    elif key == "STRT1_HR":
        state.timer1_start_hr = int(value)
    elif key == "STRT1_MIN":
        state.timer1_start_min = int(value)
    elif key == "STOP1_HR":
        state.timer1_stop_hr = int(value)
    elif key == "STOP1_MIN":
        state.timer1_stop_min = int(value)
    elif key == "STRT2_HR":
        state.timer2_start_hr = int(value)
    elif key == "STRT2_MIN":
        state.timer2_start_min = int(value)
    elif key == "STOP2_HR":
        state.timer2_stop_hr = int(value)
    elif key == "STOP2_MIN":
        state.timer2_stop_min = int(value)

    # Known but unhandled fields
    elif key in ("PUMPSTAT", "TMST"):
        pass  # Intentionally ignored

    else:
        _LOGGER.debug("Unknown status field: %s=%s", key, value)


def _is_aux_key(key: str) -> bool:
    """Check if a key matches the AUX[n] pattern."""
    return key.startswith("AUX[") and key.endswith("]")


def _parse_aux_number(key: str) -> int:
    """Extract the AUX number from a key like 'AUX[1]'."""
    return int(key[4:-1])


def _parse_history(value: str) -> list[float | None]:
    """Parse a comma-separated history string.

    Values of -1.0 are treated as 'no data' and returned as None.
    """
    result: list[float | None] = []
    for item in value.split(","):
        item = item.strip()
        val = float(item)
        result.append(None if val < 0 else val)
    return result
