# Pool Lab - Home Assistant Integration

Home Assistant integration for the Pool Lab PL Max Series of controllers.

## Compatible Devices

This integration supports the following Pool Lab models:

| Series | Models |
|--------|--------|
| PL25 | Classic, Plus, MAX |
| PL35 | Classic, Plus, MAX |
| PL45 | Classic, Plus, MAX |

Any device in the PL25, PL35, or PL45 range with network connectivity is supported.

## Installation via HACS

1. Open HACS in your Home Assistant instance.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add this repository URL and select **Integration** as the category.
4. Click **Add**, then find "Pool Lab" in the HACS store and install it.
5. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for "Pool Lab".
3. Enter the IP address (or hostname) and port of your Pool Lab device.
4. The integration will verify connectivity before completing setup.

## Requirements

- A Pool Lab Max series device accessible on your local network.
- The device's IP/hostname and port.
