# Development notes

## Initial milestone

This branch establishes the integration packaging, UI configuration flow, CT50 API client, weekly schedule validation, and Home Assistant storage for four independent profiles.

The schedule service implementation, clock monitoring/synchronization, entity model, and Lovelace editor are intentionally not considered complete yet. The clock setter endpoint and Hold side effects must be confirmed against the API guide and a real CT50 before enabling any automatic clock correction.

## CT50 schedule format

- Endpoints: `GET/POST /tstat/program/heat` and `GET/POST /tstat/program/cool`.
- Seven keys `"0"` through `"6"`; day 0 is Monday and day 6 is Sunday.
- Each value is eight integers: four pairs of minute-of-day and Fahrenheit setpoint.
- A schedule upload must be followed by a GET and normalized comparison.
- Heat and cool are separate requests; the operation cannot be assumed atomic.

## Safety rules

- No schedule upload during setup or Home Assistant restart.
- Do not infer the intended Home/Away profile from current thermostat programs.
- Do not overwrite stored profiles from a thermostat read unless the user explicitly asks to adopt them.
- Preserve current thermostat mode when switching profiles.
- Clock correction must not run automatically while Hold is active until the exact behavior is proven.
- Keep API operations serialized with a shared lock.

## Testing checklist

Before any real activation is implemented:
1. Validate both heat and cool payloads before writing either one.
2. Serialize API operations.
3. Capture per-mode write/readback results and report partial success accurately.
4. Verify schedule readback and compare normalized data.
5. Confirm current `tmode`, `hold`, and operating state remain unchanged after activation.
6. Test malformed API responses, timeouts, connection loss, and a thermostat reboot.
7. Confirm that a Home Assistant restart never pushes a profile automatically.
8. Verify that UI and services distinguish saved profiles from currently verified thermostat schedules.
