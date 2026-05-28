# Pool Lab PL MAX Series - TCP Protocol Reference

This document describes the local TCP socket protocol used by Pool Lab PL MAX series controllers (PL25, PL35, PL45 MAX models). This is an unofficial protocol derived from manufacturer correspondence.

## Connection

| Parameter | Value |
|-----------|-------|
| Transport | Raw TCP socket |
| Port | 8080 |
| Hostname pattern | `POOLLAB_XXXXXX` (last 6 hex digits of MAC, uppercase) |
| mDNS hostname | `POOLLAB_XXXXXX.local` |
| mDNS service | `_http._tcp` on port 8080 |
| Encoding | ASCII text |

### Handshake

Upon successful TCP connection, the device immediately sends:

```
connected\r\n
```

Followed by a full status update (see Status Update section below).

## Command Format

### Structure

```
<cmd>[,<param>];<CR>
```

- Commands are **two lowercase characters**
- Optional (or required) parameter follows a comma
- Terminated with a semicolon
- The full command string is terminated with a carriage return `\r` (0x0D)

### Chaining

Multiple commands can be chained in a single message:

```
fi,1;a1,1;a2,1;\r
```

Note: When multiple AUX outputs are activated together, the device enforces a 1-second delay between each activation to prevent excessive inrush current.

### Case Sensitivity

Some commands accept uppercase, but **lowercase is recommended** for maximum compatibility.

## Commands

### Status Request

| Command | Description |
|---------|-------------|
| `up;` | Request a full status update (no parameter) |

The device also pushes a status update automatically whenever a critical state change occurs.

### Filter & Modes

| Command | Parameter | Description |
|---------|-----------|-------------|
| `fi;` | none | Toggle filter mode |
| `fi,<n>;` | 0=OFF, 1=ON, 2=AUTO | Set filter mode |
| `ps;` | none | Toggle pool/spa mode |
| `ps,<n>;` | 0=POOL, 1=SPA | Set pool/spa mode |

### Heating

| Command | Parameter | Description |
|---------|-----------|-------------|
| `sh;` | none | Toggle solar heat |
| `sh,<n>;` | 0=OFF, 1=ON | Set solar heat mode |
| `ht;` | none | Toggle heater |
| `ht,<n>;` | 0=OFF, 1=ON | Set heater mode |

### AUX Outputs (a1 - a9)

| Command | Parameter | Description |
|---------|-----------|-------------|
| `a1;` | none | Toggle AUX1 |
| `a1,<n>;` | 0=OFF, 1=ON, 2=AUTO | Set AUX1 mode |
| `a2;` ... `a9;` | same | AUX2 through AUX9 |

### Valves

| Command | Parameter | Description |
|---------|-----------|-------------|
| `v3;` | none | Toggle valve 3 position |
| `v3,<n>;` | 0=POS1, 1=POS2, 2=AUTO | Set valve 3 mode |
| `v4;` / `v4,<n>;` | same | Valve 4 |

### Grouped Outputs

These control groups of outputs configured in the system. All support toggle (no param) or explicit mode.

| Command | Parameter | Description |
|---------|-----------|-------------|
| `pl;` / `pl,<n>;` | 0=OFF, 1=ON, 2=AUTO | Pool lights |
| `sl;` / `sl,<n>;` | 0=OFF, 1=ON, 2=AUTO | Spa lights |
| `sb;` / `sb,<n>;` | 0=OFF, 1=ON, 2=AUTO | Spa boost |
| `bl;` / `bl,<n>;` | 0=OFF, 1=ON, 2=AUTO | Blower |
| `if;` / `if,<n>;` | 0=OFF, 1=ON, 2=AUTO | Infloor cleaning |
| `cn;` / `cn,<n>;` | 0=OFF, 1=ON, 2=AUTO | Cleaner |
| `fo;` / `fo,<n>;` | 0=OFF, 1=ON, 2=AUTO | Fountain |

### Set Points (required parameter)

| Command | Parameter | Description |
|---------|-----------|-------------|
| `sp,<xxx>;` | Temperature × 10 | Set pool temp target (e.g. `sp,275;` = 27.5°C) |
| `ss,<xxx>;` | Temperature × 10 | Set spa temp target |
| `ph,<xx>;` | pH × 10 | Set pH target (e.g. `ph,76;` = 7.6) |
| `cl,<xx>;` | Chlorine × 10 | Set free chlorine target (ppm × 10) |
| `so,<x>;` | 1, 2, or 3 | Set pump speed override |
| `co,<xxx>;` | 0-100 | Set chlorinator output % (only without ASP module) |

## Status Update Format

The status update is a semicolon-delimited string of `KEY=VALUE` pairs:

```
FG1=1aea09ff;FG2=0;CHLORSTAT=0300;SYSSTAT=0;FILTER=1;SPAMODE=0;...
```

### Sensor Values

| Field | Type | Range | Unit | Description |
|-------|------|-------|------|-------------|
| `WATERTEMP` | int | 0-400 | °C × 10 | Water temperature (e.g. 270 = 27.0°C) |
| `CLLEVEL` | float | 0.00-9.90 | ppm | Free chlorine level |
| `PHLEVEL` | float | 6.50-8.50 | — | pH level |
| `CLTARG` | float | 0.00-9.90 | ppm | Free chlorine target |
| `PHTARG` | float | 6.50-8.50 | — | pH target |
| `CHLORTARG` | int | 0-100 | % | Chlorinator output target |
| `CHLORACT` | int | 0-100 | % | Chlorinator actual output |
| `PUMPSPEED` | int | 1-3 | — | Pump speed (1=low, 2=med, 3=high) |
| `POOLSET` | float | 0-40 | °C | Pool temperature target |
| `SPASET` | float | 0-40 | °C | Spa temperature target |

### Mode/State Values

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `FILTER` | int | 0=OFF, 1=ON, 2=AUTO | Filter mode |
| `SPAMODE` | int | 0=POOL, 1=SPA | Pool/Spa mode |
| `SOLARMODE` | int | 0=OFF, 1=ON | Solar heating mode |
| `HEATMODE` | int | 0=OFF, 1=ON | Heater mode |
| `AUX[1]`...`AUX[10]` | int | 0=OFF, 1=ON, 2=AUTO | AUX output modes |
| `VALVE3` | int | 0=POS1, 1=POS2, 2=AUTO | Valve 3 mode |
| `VALVE4` | int | 0=POS1, 1=POS2, 2=AUTO | Valve 4 mode |
| `POOLLIGHT` | int | 0=OFF, 1=ON, 2=AUTO | Pool lights group |
| `SPALIGHT` | int | 0=OFF, 1=ON, 2=AUTO | Spa lights group |
| `SPABOOST` | int | 0=OFF, 1=ON, 2=AUTO | Spa boost group |
| `SPABLOWER` | int | 0=OFF, 1=ON, 2=AUTO | Spa blower group |
| `INFLOOR` | int | 0=OFF, 1=ON, 2=AUTO | Infloor cleaning group |
| `CLEANER` | int | 0=OFF, 1=ON, 2=AUTO | Cleaner group |
| `FOUNTAIN` | int | 0=OFF, 1=ON, 2=AUTO | Fountain group |

### Reagent Status

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `REAGENT #1` | int | 0=empty, 1=ok | pH reagent |
| `REAGENT #2` | int | 0=empty, 1=ok | Free chlorine reagent #1 |
| `REAGENT #3` | int | 0=empty, 1=ok | Free chlorine reagent #2 |
| `REAGENT #4` | int | 0=empty, 1=ok | Total chlorine reagent (not currently used) |

### History Data

| Field | Description |
|-------|-------------|
| `PHTH` | Comma-separated list of 21 pH history values (-1.0 = no data) |
| `CLTH` | Comma-separated list of 21 chlorine history values (-1.0 = no data) |
| `TMST` | Comma-separated list of 21 hex-encoded timestamps for history entries |

### Timer Configuration

| Field | Description |
|-------|-------------|
| `STRT1_HR`, `STRT1_MIN` | Filter timer 1 start (hour, minute) |
| `STOP1_HR`, `STOP1_MIN` | Filter timer 1 stop |
| `STRT2_HR`, `STRT2_MIN` | Filter timer 2 start |
| `STOP2_HR`, `STOP2_MIN` | Filter timer 2 stop |

## Bitfield: FG1 (System Flags, bits 0-31)

Hex value `0x00000000` to `0xFFFFFFFF`. Determines which controls/features are available.

| Bit | Name | Description |
|-----|------|-------------|
| 0 | — | Not used (should be 0) |
| 1 | CHLORI | Chlorinator available (deprecated, always 1) |
| 2 | CHROMA | Water Analyzer module connected |
| 3 | EXPAN | Expansion module connected |
| 4 | MS_PUMP | Multi-speed pump available |
| 5 | VALVE3 | Valve 3 enabled |
| 6 | VALVE4 | Valve 4 enabled |
| 7 | AUX1 | AUX1 enabled |
| 8 | AUX2 | AUX2 enabled |
| 9 | AUX3 | AUX3 enabled |
| 10 | AUX4 | AUX4 enabled |
| 11 | AUX5 | AUX5 enabled |
| 12 | AUX6 | AUX6 enabled |
| 13 | AUX7 | AUX7 enabled |
| 14 | AUX8 | AUX8 enabled |
| 15 | AUX9 | AUX9 enabled |
| 16 | AUX10 | AUX10 enabled |
| 17 | SOLARPOOL | Solar heating available in pool mode |
| 18 | SOLARSPA | Solar heating available in spa mode |
| 19 | HEATPOOL | Gas heating available in pool mode |
| 20 | HEATSPA | Gas heating available in spa mode |
| 21 | POOL | Pool mode available (if unset, locked to SPA) |
| 22 | SPA | Spa mode available (if unset, locked to POOL) |
| 23 | AUX1-5 | Any expansion module connected (AUX 1-5 available) |
| 24 | AUX6-10 | 10-output expansion module connected (AUX 6-10 available) |
| 25 | VALVE1-4 | Any expansion module connected (valves available) |
| 26 | CL_TOTAL | Total chlorine testing available (future use) |
| 27 | POOL_LIGHT_GROUP | Pool light group configured |
| 28 | SPA_LIGHT_GROUP | Spa light group configured |
| 29 | SPA_BOOST_GROUP | Spa boost group configured |
| 30 | SPA_BLOWER_GROUP | Spa blower group configured |
| 31 | INFLOOR_GROUP | Infloor cleaning group configured |

## Bitfield: FG2 (System Flags, bits 32-33)

Hex value `0x0` to `0x3`.

| Bit | Name | Description |
|-----|------|-------------|
| 0 | CLEANER_GROUP | Cleaner group configured |
| 1 | FOUNTAIN_GROUP | Fountain group configured |

## Bitfield: CHLORSTAT (Chlorinator Status)

Hex value `0x000` to `0xFFF`.

| Bit | Name | Description |
|-----|------|-------------|
| 0 | LOW_FLOW | Sustained loss of cell flow detected |
| 1 | LO_SALT | Low salt level detected |
| 2 | LO_SALT_OFF | Critically low salt — cell forced off |
| 3 | HI_SALT | High salt level detected |
| 4 | HI_SALT_OFF | Critically high salt — cell forced off |
| 5 | PUMP_PROTECT | Low flow persisted beyond limit — pump forced off |
| 6 | CHLR_CMD | Chlorinator attempting to produce chlorine |
| 7 | CHLR_DUTY | Cell in active duty cycle |
| 8 | CELLFLOW | Flow detected |
| 9 | OUTPUT_FAULT | Cell voltage out of range — major fault, cell forced off |
| 10 | — | Not used |
| 11 | — | Not used |

## Bitfield: SYSSTAT (System Status)

Hex value `0x0` to `0xF`.

| Bit | Name | Description |
|-----|------|-------------|
| 0 | DEFAULTS_USED | Factory reset performed |
| 1 | WATER_SENSOR_FAULT | Filter circuit temp sensor out of range |
| 2 | HOT_SENSOR_FAULT | Solar hot sensor out of range |
| 3 | COLD_SENSOR_FAULT | Solar cold sensor out of range |

## Bitfield: CHROMSTAT (Water Analyzer Status)

Hex value `0x00` to `0xFF`.

| Bit | Name | Description |
|-----|------|-------------|
| 0 | CL_AT_TARG | Free chlorine at or above target |
| 1 | CHLOR_ON | Timed chlorine delivery (deprecated but functional) |
| 2 | ACID_ON | Acid pump active (acid delivery in progress) |
| 3 | SUST_CL_DEV | Chlorine below target for extended period |
| 4 | SUST_PH_DEV | pH above target for extended period |
| 5 | CL_KNOWN | Free chlorine level is known (show `-.-` if unset) |
| 6 | PH_KNOWN | pH level is known (show `-.-` if unset) |
| 7 | CT_KNOWN | Total chlorine level is known (not currently used) |

## Example Session

```
[connect to POOLLAB_93314C:8080]

<< connected
<< FG1=1aea09ff;FG2=0;CHLORSTAT=0300;SYSSTAT=0;PUMPSTAT=01;FILTER=1;SPAMODE=0;
   CHLORTARG=0;CHLORACT=0;PUMPSPEED=2;WATERTEMP=270;SOLARMODE=0;HEATMODE=0;
   POOLSET=40.00;SPASET=99.99;AUX[1]=0;AUX[2]=0;AUX[5]=0;VALVE3=2;VALVE4=2;
   POOLLIGHT=2;SPALIGHT=2;CLLEVEL=1.60;PHLEVEL=6.70;CLTARG=2.50;PHTARG=7.60;
   CHROMSTAT=0000;REAGENT #1=1;REAGENT #2=1;REAGENT #3=1;
   PHTH=7.6,7.6,...;CLTH=1.6,-1.0,...;TMST=...;
   STRT1_HR=9;STRT1_MIN=0;STOP1_HR=9;STOP1_MIN=10;...

>> up;\r
<< [full status update]

>> fi,1;\r
<< [status update reflecting filter ON]

>> sp,275;\r
<< [status update reflecting pool temp target 27.5°C]
```

## Notes

- Status updates are pushed automatically on state changes; polling via `up;` is also supported.
- Values of `99.99` for temperature set points likely indicate "not configured" or "disabled".
- History values of `-1.0` indicate no data for that slot.
- The device uses DHCP by default. For reliable connectivity, assign a static IP via your router or use mDNS discovery.
