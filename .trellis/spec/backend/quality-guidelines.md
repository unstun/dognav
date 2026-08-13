# Quality Guidelines

> Code quality standards for navigation integration and evidence-producing runtimes.

---

## Overview

Navigation integration crosses binary transport, ROS messages, simulator state,
and evaluation artifacts. A passing unit test at one layer is not enough: the
serialized value must be checked at the next consumer and its physical effect
must be checked at runtime.

## Forbidden Patterns

- Passing network-order numeric payload bytes directly to a host-native ROS or
  PCL message. Convert byte order explicitly and test known float values.
- Classifying a simulated sensor hit only by a loose bounding box when another
  surface can occupy the same projection. Require a discriminating condition
  and retain raw hit counts.
- Treating sensor configuration as proof that every named mesh is in the actual
  ray-cast acceleration structure. Inspect runtime mesh-load evidence and prove
  non-ground returns.
- Relaxing planner collision thresholds to hide malformed clouds or frame
  errors.
- Promoting a transport, sensor, planner, or policy preflight into a closed-loop
  validation claim.

## Required Patterns

- Include frame, unit, numeric encoding, byte order, timestamp, and ownership in
  every cross-process sensor contract.
- Hash perception preprocessing settings into the run identity. Keep raw and
  filtered counts so filtering remains auditable.
- Fail closed on command drift, malformed payloads, non-finite values, stale
  commands, disconnects, collisions, and resets.
- Freeze acceptance thresholds after dry runs and before the acceptance run.
- Preserve failed runs unchanged and distinguish instrumentation failures from
  algorithm failures.

## Testing Requirements

- Protocol tests cover framing, partial reads, CRC, limits, timestamps,
  sequences, invalid numeric data, reconnects, saturation, and watchdog stop.
- Numeric boundary tests verify the exact bytes consumed downstream, not only
  encode/decode symmetry inside one module.
- Sensor gates distinguish traversable-floor returns from obstacle-surface
  returns and prove pose-dependent geometry.
- Full integration records planner output, commands, policy observation,
  physical motion and contacts, rendered sensing, and feedback in one run.

## Code Review Checklist

- Does each claim identify `surveyed`, `reproduced`, `integrated`, or
  `validated` evidence?
- Is every binary or frame conversion explicit and covered downstream?
- Can ground, robot self-returns, or stale frames masquerade as obstacles?
- Does a physical obstacle appear to both sensing and collision systems?
- Are source, checkpoint, config, logs, metrics, ROS recording, and video
  synchronized locally and hash-verified?
