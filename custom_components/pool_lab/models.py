"""Data models for Pool Lab device state."""

from __future__ import annotations

from dataclasses import dataclass, field

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


@dataclass
class PoolLabState:
    """Complete state snapshot from a Pool Lab device.

    Populated by parsing a status update string from the device.
    All values use native Python types with appropriate units.
    """

    # System configuration flags
    system_flags: SystemFlag = field(default_factory=lambda: SystemFlag(0))
    system_flags_2: SystemFlag2 = field(default_factory=lambda: SystemFlag2(0))

    # Status bitfields
    chlorinator_status: ChlorinatorStatus = field(default_factory=lambda: ChlorinatorStatus(0))
    system_status: SystemStatus = field(default_factory=lambda: SystemStatus(0))
    water_analyzer_status: WaterAnalyzerStatus = field(
        default_factory=lambda: WaterAnalyzerStatus(0)
    )

    # Core modes
    filter_mode: OutputMode = OutputMode.OFF
    spa_mode: PoolSpaMode = PoolSpaMode.POOL
    solar_mode: OutputMode = OutputMode.OFF
    heat_mode: OutputMode = OutputMode.OFF

    # Pump
    pump_speed: PumpSpeed = PumpSpeed.LOW

    # Chlorinator
    chlorinator_target: int = 0  # 0-100 %
    chlorinator_actual: int = 0  # 0-100 %

    # Temperature (degrees Celsius)
    water_temp: float | None = None
    pool_set_temp: float | None = None
    spa_set_temp: float | None = None

    # Water chemistry
    chlorine_level: float | None = None  # ppm
    ph_level: float | None = None
    chlorine_target: float | None = None  # ppm
    ph_target: float | None = None

    # AUX outputs (keyed by number 1-10)
    aux_modes: dict[int, OutputMode] = field(default_factory=dict)

    # Valves
    valve3_mode: OutputMode = OutputMode.OFF
    valve4_mode: OutputMode = OutputMode.OFF

    # Grouped outputs
    pool_light: OutputMode = OutputMode.OFF
    spa_light: OutputMode = OutputMode.OFF
    spa_boost: OutputMode = OutputMode.OFF
    spa_blower: OutputMode = OutputMode.OFF
    infloor: OutputMode = OutputMode.OFF
    cleaner: OutputMode = OutputMode.OFF
    fountain: OutputMode = OutputMode.OFF

    # Reagent status (True = ok, False = empty)
    reagent_ph: bool = True
    reagent_cl1: bool = True
    reagent_cl2: bool = True
    reagent_total_cl: bool = True

    # History data
    ph_history: list[float | None] = field(default_factory=list)
    cl_history: list[float | None] = field(default_factory=list)

    # Timer configuration
    timer1_start_hr: int = 0
    timer1_start_min: int = 0
    timer1_stop_hr: int = 0
    timer1_stop_min: int = 0
    timer2_start_hr: int = 0
    timer2_start_min: int = 0
    timer2_stop_hr: int = 0
    timer2_stop_min: int = 0
