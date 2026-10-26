# Radio Thermostat Schedule Manager

A Home Assistant custom integration for managing thermostat-native weekly schedules and monitoring the CT50's internal clock. The CT50 is the initial target; other Radio Thermostat models are not considered supported until tested.

> **Development status:** early development. Do not use this project to control a thermostat you depend on for freeze protection or other critical heating/cooling without supervised testing. The first milestone is an inspectable, conservative integration foundation; full schedule editing and the Lovelace editor will follow after API behavior is verified.

## Design goals

- Keep the thermostat responsible for executing its own schedules; Home Assistant does not run the schedule.
- Store four independent profiles in Home Assistant: Home Heat, Away Heat, Home Cool, and Away Cool.
- Require an explicit activation action before writing a profile to the thermostat.
- Verify schedule writes by reading the schedules back. Heat and cool writes are separate and are not atomic.
- Preserve the thermostat's current operating mode when changing schedules.
- Never silently overwrite saved Home Assistant profiles when the thermostat schedule differs.
- Monitor the thermostat's internal clock, but avoid automatic clock writes while Hold is active because the time-setting API may clear Hold.
- Share an API lock between schedule and clock operations.

## Planned installation

The intended distribution is a HACS custom integration plus a companion Lovelace schedule editor. Installation instructions will be added when the integration and frontend are ready for a release.

## Development

This repository is under active development. See [CHANGELOG.md](CHANGELOG.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the current scope and test expectations.

## Support boundary

Initial target: Radio Thermostat CT50. API endpoints and payloads are based on the CT50 API guide and user-verified local tests. This software is not affiliated with Radio Thermostat.
