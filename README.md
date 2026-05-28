# Pool Lab

[![hacs][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]
[![License][license-badge]][license-url]

Home Assistant integration for the Pool Lab PL Max Series of controllers.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][hacs-install-badge]][hacs-install-url]

## Compatible Devices

This integration supports the following Pool Lab models:

- PL25 MAX
- PL35 MAX
- PL45 MAX

Only the MAX variant of each series is supported, as these include the network connectivity required for this integration.

## Features

- **Sensors**: Water temperature, pH level, chlorine level, chlorinator output, pump speed
- **Binary Sensors**: Flow detection, salt warnings, sensor faults, reagent levels, water analyzer status
- **Switches**: Filter, heater, solar heat, pool/spa mode, AUX outputs (1-9), valves, pool lights, spa lights, blower, fountain, cleaner, infloor cleaning, spa boost
- **Number Controls**: Pool/spa temperature targets, pH target, chlorine target, chlorinator output %

## Installation

### HACS (Recommended)

1. Click the button above, or manually add this repository to HACS:
   - Open HACS → three-dot menu → **Custom repositories**
   - Add `https://github.com/lerebel103/pool-lab-ha-plugin` with category **Integration**
2. Search for "Pool Lab" in HACS and install it.
3. Restart Home Assistant.

### Manual

1. Download the latest release from the [releases page][release-url].
2. Extract the `pool_lab` folder into your `custom_components/` directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Pool Lab**.
3. Enter the IP address (or hostname) and port of your Pool Lab device.
4. The integration will verify connectivity before completing setup.

The device communicates over a local TCP connection on port 8080. For reliable connectivity, assign a static IP to your Pool Lab device via your router.

## Device Discovery

Pool Lab devices advertise themselves via mDNS/Bonjour:

- **Hostname**: `POOLLAB_XXXXXX.local` (where XXXXXX is the last 6 hex digits of the MAC address)
- **Service**: `_http._tcp` on port 8080

## Contributing

See [AGENTS.md](AGENTS.md) for development guidelines.

```bash
# Install dev dependencies
make install

# Run linting
make lint

# Run tests
make test

# Run full CI check
make ci
```

## License

This project is licensed under the MIT License.

---

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://hacs.xyz
[release-badge]: https://img.shields.io/github/v/release/lerebel103/pool-lab-ha-plugin
[release-url]: https://github.com/lerebel103/pool-lab-ha-plugin/releases
[license-badge]: https://img.shields.io/github/license/lerebel103/pool-lab-ha-plugin
[license-url]: https://github.com/lerebel103/pool-lab-ha-plugin/blob/main/LICENSE
[hacs-install-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-install-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=lerebel103&repository=pool-lab-ha-plugin&category=integration
