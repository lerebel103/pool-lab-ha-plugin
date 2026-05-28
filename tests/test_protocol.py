"""Tests for the Pool Lab protocol layer."""

from __future__ import annotations

import pytest

from custom_components.pool_lab.const import (
    ChlorinatorStatus,
    OutputMode,
    PoolSpaMode,
    PumpSpeed,
    SystemFlag,
)
from custom_components.pool_lab.protocol import (
    cmd_aux,
    cmd_chlorinator_output,
    cmd_chlorine_target,
    cmd_filter,
    cmd_heater,
    cmd_ph_target,
    cmd_pool_spa,
    cmd_pool_temp_target,
    cmd_pump_speed,
    cmd_solar_heat,
    cmd_spa_temp_target,
    cmd_status_request,
    cmd_valve,
    parse_status_update,
)


class TestCommandBuilders:
    """Tests for command construction."""

    def test_status_request(self) -> None:
        assert cmd_status_request() == "up;\r"

    def test_filter_toggle(self) -> None:
        assert cmd_filter() == "fi;\r"

    def test_filter_set_on(self) -> None:
        assert cmd_filter(OutputMode.ON) == "fi,1;\r"

    def test_filter_set_off(self) -> None:
        assert cmd_filter(OutputMode.OFF) == "fi,0;\r"

    def test_pool_spa_toggle(self) -> None:
        assert cmd_pool_spa() == "ps;\r"

    def test_pool_spa_set_spa(self) -> None:
        assert cmd_pool_spa(PoolSpaMode.SPA) == "ps,1;\r"

    def test_solar_heat_on(self) -> None:
        assert cmd_solar_heat(OutputMode.ON) == "sh,1;\r"

    def test_solar_heat_off(self) -> None:
        assert cmd_solar_heat(OutputMode.OFF) == "sh,0;\r"

    def test_heater_on(self) -> None:
        assert cmd_heater(OutputMode.ON) == "ht,1;\r"

    def test_aux_toggle(self) -> None:
        assert cmd_aux(1) == "a1;\r"

    def test_aux_set_auto(self) -> None:
        assert cmd_aux(5, OutputMode.AUTO) == "a5,2;\r"

    def test_aux_invalid_number(self) -> None:
        with pytest.raises(ValueError):
            cmd_aux(10)

    def test_valve_set(self) -> None:
        assert cmd_valve(3, OutputMode.ON) == "v3,1;\r"

    def test_valve_invalid_number(self) -> None:
        with pytest.raises(ValueError):
            cmd_valve(1)

    def test_pool_temp_target(self) -> None:
        assert cmd_pool_temp_target(27.5) == "sp,275;\r"

    def test_spa_temp_target(self) -> None:
        assert cmd_spa_temp_target(38.0) == "ss,380;\r"

    def test_ph_target(self) -> None:
        assert cmd_ph_target(7.6) == "ph,76;\r"

    def test_chlorine_target(self) -> None:
        assert cmd_chlorine_target(2.5) == "cl,25;\r"

    def test_pump_speed(self) -> None:
        assert cmd_pump_speed(PumpSpeed.HIGH) == "so,3;\r"

    def test_chlorinator_output(self) -> None:
        assert cmd_chlorinator_output(75) == "co,75;\r"

    def test_chlorinator_output_invalid(self) -> None:
        with pytest.raises(ValueError):
            cmd_chlorinator_output(101)


class TestStatusParsing:
    """Tests for parsing status update strings."""

    SAMPLE_STATUS = (
        "FG1=1aea09ff;FG2=0;CHLORSTAT=0300;SYSSTAT=0;PUMPSTAT=01;"
        "FILTER=1;SPAMODE=0;CHLORTARG=50;CHLORACT=45;PUMPSPEED=2;"
        "WATERTEMP=270;SOLARMODE=0;HEATMODE=0;POOLSET=28.00;SPASET=38.00;"
        "AUX[1]=0;AUX[2]=1;AUX[5]=2;VALVE3=2;VALVE4=0;"
        "POOLLIGHT=2;SPALIGHT=1;"
        "CLLEVEL=1.60;PHLEVEL=7.20;CLTARG=2.50;PHTARG=7.60;"
        "CHROMSTAT=21;"
        "REAGENT #1=1;REAGENT #2=1;REAGENT #3=0;"
        "PHTH=7.6,7.6,-1.0;CLTH=1.6,-1.0,2.0;"
        "STRT1_HR=9;STRT1_MIN=30;STOP1_HR=17;STOP1_MIN=0"
    )

    def test_parse_system_flags(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.system_flags & SystemFlag.AUX1
        assert state.system_flags & SystemFlag.POOL
        assert state.system_flags & SystemFlag.SPA

    def test_parse_chlorinator_status(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.chlorinator_status & ChlorinatorStatus.CELLFLOW

    def test_parse_filter_mode(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.filter_mode == OutputMode.ON

    def test_parse_spa_mode(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.spa_mode == PoolSpaMode.POOL

    def test_parse_pump_speed(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.pump_speed == PumpSpeed.MEDIUM

    def test_parse_chlorinator_values(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.chlorinator_target == 50
        assert state.chlorinator_actual == 45

    def test_parse_water_temp(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.water_temp == 27.0

    def test_parse_set_temps(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.pool_set_temp == 28.0
        assert state.spa_set_temp == 38.0

    def test_parse_water_chemistry(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.chlorine_level == 1.60
        assert state.ph_level == 7.20
        assert state.chlorine_target == 2.50
        assert state.ph_target == 7.60

    def test_parse_aux_modes(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.aux_modes[1] == OutputMode.OFF
        assert state.aux_modes[2] == OutputMode.ON
        assert state.aux_modes[5] == OutputMode.AUTO

    def test_parse_valves(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.valve3_mode == OutputMode.AUTO
        assert state.valve4_mode == OutputMode.OFF

    def test_parse_grouped_outputs(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.pool_light == OutputMode.AUTO
        assert state.spa_light == OutputMode.ON

    def test_parse_reagents(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.reagent_ph is True
        assert state.reagent_cl1 is True
        assert state.reagent_cl2 is False

    def test_parse_history(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.ph_history == [7.6, 7.6, None]
        assert state.cl_history == [1.6, None, 2.0]

    def test_parse_timers(self) -> None:
        state = parse_status_update(self.SAMPLE_STATUS)
        assert state.timer1_start_hr == 9
        assert state.timer1_start_min == 30
        assert state.timer1_stop_hr == 17
        assert state.timer1_stop_min == 0

    def test_parse_empty_string(self) -> None:
        """Parsing an empty string should return default state."""
        state = parse_status_update("")
        assert state.water_temp is None
        assert state.filter_mode == OutputMode.OFF

    def test_parse_unknown_fields_ignored(self) -> None:
        """Unknown fields should not raise errors."""
        state = parse_status_update("UNKNOWN_FIELD=42;FILTER=2")
        assert state.filter_mode == OutputMode.AUTO
