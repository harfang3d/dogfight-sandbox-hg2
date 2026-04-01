# Carrier Landing RL Research

This repository is suitable for carrier landing research as a **research sandbox**, not as a high-fidelity naval aviation simulator. The current codebase already contains:

* An aircraft carrier asset with named start and landing nodes
* Carrier spawn and training missions
* A built-in landing target and approach profile
* Fixed-timestep and renderless execution support
* An RL client scaffold in `Agent/`

That makes it practical for RL method development, reward shaping, curriculum design, and ablation studies. It does **not** model arresting wires, catapults, sea-state deck motion, wind-over-deck procedures, or validated real-carrier geometry.

## Where the carrier parameters come from

The exporter reads the current simulator asset directly:

* Scene anchors: `source/assets/machines/aircraft_carrier_blend/aircraft_carrier_blend.scn`
* Collision geometry: `source/assets/machines/aircraft_carrier_blend/carrier_col_shape*.geo`

The collision extents intentionally mirror the runtime setup in `source/Machines.py`:

* The exporter uses the raw cube geometry sizes from the collision `.geo` files.
* It applies the collision node position and rotation from the scene.
* It does **not** apply the source node `0.1` scale, because the engine replaces those source nodes with unscaled physics cubes during collision setup.

The generated metadata is written to `source/scripts/aircraft_carrier_deck_parameters.json`.

## Exporting the metadata

Generate or refresh the metadata artifact:

```bash
python source/scripts/export_carrier_deck_parameters.py
```

Check that the committed JSON matches the current carrier asset:

```bash
python source/scripts/export_carrier_deck_parameters.py --check
```

The same carrier-local deck metadata is also available at runtime through the network API:

* `get_carriers_list()`
* `get_carrier_deck_parameters(carrier_id)`

The network response includes the exported local metadata plus world-space deck anchors for the selected carrier instance.

## Current baseline values

The current carrier asset exports these baseline values:

* Collision bounds local size: about `80.734 m x 4.300 m x 273.820 m`
* Landing point local: about `(5.659, 17.400, -119.565)`, yaw `-10.0 deg`
* Start point 1 local: `(10.000, 17.500, 40.000)`, yaw `0.0 deg`
* Start point 2 local: `(-23.519, 17.361, -19.881)`, yaw `6.06 deg`
* Approach entry local from the built-in `LandingTarget`: about `(1047.548, 517.400, -6028.411)`

## Static-deck RL landing task

### Scope

Phase 1 keeps the carrier static and uses the existing aircraft physics model. The default validation vehicle is the current **Rafale** training setup. `Miuss` can be used as a follow-up cross-check once the task is stable.

### Observation source

Use:

* The existing plane state from the network API
* Offline deck metadata from `source/scripts/aircraft_carrier_deck_parameters.json`

### Action space

Continuous controls:

* `pitch`
* `roll`
* `yaw`
* `thrust`

### Configuration policy

Recommended defaults:

* Auto-deploy gear when along-track distance to touchdown is below `1200 m`
* Auto-set flaps to landing configuration when along-track distance is below `1500 m`
* Auto-apply brakes after valid wheel contact

### Reset distribution

Recommended initial state sampling:

* Along-track distance behind touchdown: uniform `1500-3000 m`
* Cross-track error: uniform `-60 to 60 m`
* Heading error: uniform `-8 to 8 deg`
* Altitude error relative to the glide profile: uniform `-25 to 25 m`
* Forward speed: uniform `72-82 m/s`

### Success criteria

* Touchdown inside the exported valid landing corridor
* Touchdown sink rate `<= 4 m/s`
* Absolute roll `<= 10 deg`
* Absolute pitch `<= 15 deg`
* Full stop inside the corridor within `20 s` of touchdown

### Failure criteria

* Water collision, crash, or deck miss
* First wheel contact outside the corridor
* Passing `50 m` beyond touchdown without wheel contact
* Episode timeout at `90 s`

### Reward defaults

Per-step reward:

```text
-0.002*abs(cross_track_m)
-0.002*abs(alt_error_m)
-0.25*(abs(heading_error_deg)/45)
-0.01*max(0, abs(sink_rate_mps)-4)
-0.002*abs(speed_mps-78)
```

Shaping and terminal rewards:

* `+25` once when inside the near-approach gate:
  * `along_track < 500 m`
  * `|cross_track| < 10 m`
  * `|alt_error| < 10 m`
  * `|heading_error| < 5 deg`
* `+100` for valid touchdown
* `+150` more for a valid full stop
* `-100` for any failure case

## Manual validation

Recommended manual checks:

* Run the exporter and confirm `--check` passes
* Spawn a carrier training mission and enable landing trajectory display
* Verify that the documented landing point and landing heading align with the visible deck approach
* Verify that the exported collision bounds contain both aircraft start points and the landing point

## Research limits

This setup is appropriate for RL research on the **current simulator asset**. It is not sufficient for claims that depend on:

* Arresting-wire or tailhook dynamics
* Catapult launch dynamics
* Sea-state heave, roll, or pitch
* Wind-over-deck procedures
* Calibration to a real Nimitz- or Ford-class carrier
