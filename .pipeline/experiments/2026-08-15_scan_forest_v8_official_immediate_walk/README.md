# Official Human Immediate Constant-Velocity Preview

This auxiliary trial addresses the visual observation that the pedestrian in
the continuous-walk preview still waited for the Lite3 command trigger.

The run changes only these recorded preview inputs:

- `dynamic_obstacle_schedule_trigger=run_start`;
- `dynamic_obstacle_wait_seconds=0.0`;
- `dynamic_obstacle_hold_seconds=0.0`;
- `dynamic_obstacle_speed=0.8` m/s;
- `official_human_animation_mode=continuous_walk`.

The pedestrian follows the existing straight line from the declared start to
the declared endpoint independently of robot commands. The Lite3 URDF, V12
checkpoint, hidden capsule, sensors, forest, SCAN algorithms, and command limits
remain unchanged. This trial intentionally does not satisfy the frozen
command-relative schedule requirement and must not run acceptance or replace
the V8 R2 review candidate.

Remote invocation uses the existing continuous-walk preview wrapper with
explicit environment overrides:

```bash
SCAN_DYNAMIC_OBSTACLE_SCHEDULE_TRIGGER=run_start \
SCAN_DYNAMIC_OBSTACLE_WAIT_SECONDS=0.0 \
SCAN_DYNAMIC_OBSTACLE_HOLD_SECONDS=0.0 \
./run_remote_continuous_walk_preview.sh \
  RUN_ID DURATION_SECONDS TELEMETRY_PORT COMMAND_PORT
```

## Results

### Preview 01 — preserved collision negative

The original endpoint at `y=4.8 m` let the pedestrian finish its 2.8 m route
after 3.5 s and park on the Lite3 route. Motion was exactly 0.8 m/s, but the
parked actor produced 17.375 N maximum non-foot contact and -0.169 m minimum
surface clearance. The run is preserved and not submitted for visual approval.

### Preview 02 — short visual trial superseded by duration review

The endpoint was extended to `y=8.0 m` so the actor remained in the crossing
phase throughout the rendered interval. Local replay of the copied metrics
confirmed:

- pedestrian first motion at simulator time 0.05 s while the robot command was
  still `[0, 0, 0]`;
- first nonzero robot command at simulator time 0.27 s;
- 361 crossing rows at exactly 0.8 m/s, zero hold rows, and zero parked rows;
- constant `x=-2.7 m` and monotonic increasing y;
- all 362 animation records selected the official walk clip;
- zero non-foot contact and 0.594 m minimum synchronized surface clearance;
- no acceptance report, by design.

Raw video SHA-256:
`5b6043e3c8eb56f46568c6975e7b5ab8989534b27ab901db32c6b13c5dc55955`.

Overlay video SHA-256:
`f61f7a13db5a7c4dddf852505f4a2cd1213274d832ca596ef952b8a9a0124334`.

Dr Sun requested a longer video after reviewing this 7.12 s preview.

### Preview 03 — long but parked at the end

This 21.18 s run used `y=0.0 -> 15.5 m`. It had zero contact, but the
pedestrian reached the endpoint and parked for the final 111 runtime rows. It
is preserved as intermediate evidence and is not the selected long preview.

### Preview 04 — continuous but collision negative

Moving the start back to `y=-2.0 m` kept the pedestrian crossing for the full
20.94 s video, but changed the encounter timing and caused 288.43 N maximum
non-foot contact with -0.216 m minimum clearance. It is preserved as a negative
and is not submitted for review.

### Preview 05 — rejected long visual trial

This long preview used `y=0.0 -> 16.0 m` and a 26 s wall-clock run. Its copied
runtime evidence confirmed:

- encoded video duration 19.59 s, 333 frames, 1280 x 720 at 17 fps;
- pedestrian first motion at simulator time 0.05 s while the robot command was
  still `[0, 0, 0]`;
- first nonzero robot command at simulator time 0.27 s;
- 997 crossing rows at exactly 0.8 m/s, zero hold rows, and zero parked rows;
- constant `x=-2.7 m`, monotonic increasing y, and continuous official walk;
- zero non-foot contact and 0.138 m minimum synchronized surface clearance;
- no acceptance report, by design.

Raw video SHA-256:
`35b8742754b12764a116fb175ff033ed46602b897029a1e6776f16726e2d4726`.

Overlay video SHA-256:
`e6b1afe584e43ed8d404143b5a8b2e8104112a1dab477b404943a1885499e23e`.

Dr Sun rejected this preview after visual inspection. Exact route-versus-proxy
replay found a `-0.300 m` swept clearance against `forest_proxy_008` (Rock_1),
and trajectory provenance showed that no SCAN plan was published after the
human later entered the active local path. The preview is retained only as a
negative example.

### Causal preflights 01–03 — preserved negatives

The first three geometry-gated routes established the following boundaries:

- preflight 01 passed static clearance and causal replanning but collided with
  the robot (`-0.145 m` synchronized surface clearance and `162.855 N`
  non-foot contact);
- preflight 02 delayed the pedestrian but lost the causal later plan and still
  collided (`-0.277 m`, `51.647 N`);
- preflight 03 passed static clearance, causal replanning, and zero contact, but
  its robot-human safety envelopes still overlapped by `0.123 m`.

None is a review candidate.

### Causal preflight 04 — bounded passing preflight

The candidate fixes the straight route at `x=-3.6 m`, `y=1.6 -> 9.2 m` and
keeps the official human walking continuously at exactly `0.8 m/s`. The route
ends before the later birch rather than letting the actor cross it. The copied
audit records:

- 11 static proxy bounds checked before rendering;
- `0.364 m` minimum swept-route clearance, nearest Rock_1;
- LiDAR detection at 82 sensor samples;
- first active-path intrusion at simulator time `0.690 s`;
- a later SCAN replacement from trajectory 2 to trajectory 3 at `1.130 s`;
- `0.440 s` response latency and `0.284 m` directional plan deviation;
- `0.141 m` minimum synchronized robot-human surface clearance;
- zero non-foot contact and 15 distinct SCAN trajectory IDs;
- 8.00 s, 1280 x 720, 17 fps overlay video.

Overlay video SHA-256:
`19c558ac44a7464ea5ae1753f3c02693eca3c5f268d99e6c2af5db7b210e2e3c`.

This bounded 8 s run established the first full automated pass but was not
selected because Dr Sun had already requested a longer video.

### Long causal review 01 — passing but superseded on safety margin

The first 16.18 s long straight-line candidate passed every declared automated
gate, but its minimum synchronized robot-human surface clearance was only
`0.034 m`. It is preserved as a passing intermediate and is not submitted for
human approval.

### Long causal review 02 — first same-input passing run

The selected straight line runs from `(-3.60, 1.60) m` to `(-4.09, 15.59) m`.
It is almost parallel to world y, remains a single constant direction, and lets
the official human keep walking for the whole 16.29 s video. Local copied
evidence confirms:

- 277 frames at 1280 x 720 and 17 fps;
- `0.345 m` minimum swept-route clearance, nearest `forest_proxy_007`;
- 828 crossing records at exactly `0.8 m/s`, with no hold or parked rows;
- 106 LiDAR samples that contain official-human proxy returns;
- active-path intrusion at `0.750 s`, followed by SCAN trajectory 3 -> 4 at
  `1.130 s` (`0.380 s` response, `0.162 m` directional plan change);
- 17 distinct SCAN trajectory IDs over the run;
- `0.066 m` minimum synchronized robot-human surface clearance and zero
  non-foot contact.

Overlay video SHA-256:
`f55cc30d0b48662351a67530063ae6f3fa0a5b95506c0d9b3fe3fc4c01706568`.

The operational input was correct and is also recorded in run identity, but the
then-current effective-input writer omitted the newly added endpoint-x field.
The run is retained as the first same-input passing result rather than the final
review artifact.

### Long causal review 03 — current human-review candidate

Review 03 repeats the same route, speed, duration, model, forest, sensors, and
planner inputs after adding `dynamic_obstacle_end_x=-4.09` to
`effective_input.txt`. It also passed every auxiliary gate:

- 277 frames and 16.29 s at 1280 x 720 and 17 fps;
- `0.345 m` minimum swept-route clearance;
- 830 crossing records at exactly `0.8 m/s`, with no hold or parked rows;
- 140 LiDAR samples containing human proxy returns;
- active-path intrusion at `0.690 s`, followed by SCAN trajectory 2 -> 3 at
  `1.130 s` (`0.440 s` response, `0.323 m` directional plan change);
- 16 distinct SCAN trajectory IDs;
- `0.031 m` minimum synchronized robot-human surface clearance and zero
  non-foot contact.

The two same-input runs both produced complete SCAN avoidance, but their exact
trajectory sequence and minimum clearance differ slightly; they are therefore
repeat passes, not bitwise-deterministic duplicates.

Overlay video SHA-256:
`fbac7e09f8618d56828722e93675c6bc845ce0f0361ad8954d5fbd604fd673b0`.

This remains auxiliary evidence only. The frozen V8 R2 acceptance record is
unchanged, and final visual acceptance belongs to Dr Sun.
