# Office R2.0.1 Live Cloud and Transfer Reliability — Design

## 1. Boundary and invariants

This patch changes presentation retention, observation-only auditing, evidence
validation, and delivery packaging. The simulator, sensor generator, bridge
publication, SCAN planner, locomotion policy, Office scenario, and acceptance
thresholds remain frozen.

The canonical checkout is the source of truth. The 5070 Ti Foxy workspace and
run root are execution copies. A result is usable only after its complete
artifact tree returns to the canonical local path and recursive hashes match.

## 2. Revision control model

Upgrade the Office ledger to an append-only revision-history schema while
retaining an explicit current-working-revision pointer for consumers. Seed the
history with the existing r2.0.0 record, append the planned r2.0.1 record, and
make the validator enforce:

- unique, ordered revision identifiers and immutable parent linkage;
- exactly one change group after the normalization baseline;
- current pointer equality with the final history entry;
- immutable historical run IDs and evidence hashes;
- null accepted/formal identities and pending AC55 for this preflight;
- declared allowed components, frozen invariants, gates, artifacts, rollback,
  and unauthorized actions before execution.

This ledger edit is the first Phase 2 edit outside the task directory.

## 3. Live point-cloud data flow

```text
Isaac MID-360 generator (10 Hz simulator time)
  -> Foxy bridge publishes genuine /quad_0/cloud
     -> native RViz PointCloud2 display retains latest received message
     -> review node observation-only subscription records arrival evidence
        -> post-run finalizer joins generator metrics + ROS observations
           + right-panel video visibility analysis
           -> live_pointcloud_continuity_audit.json
```

The RViz PointCloud2 display stays on `/quad_0/cloud`. Its persistence setting
is changed only after verifying that decay `0` means retain-until-replaced in
the deployed RViz plugin. No relay topic and no publisher are added.

## 4. Audit ownership and contracts

Add a pure Python continuity-audit core beside `rviz_replay_core.py`. It owns
stamp ordering, gap statistics, coverage, point counts, persistence-contract
validation, video visibility sequences, threshold evaluation, serialization,
and claim text. Keeping this logic ROS-independent enables behavior tests.

`RvizReplayNode` adds one sensor-QoS subscription to `/quad_0/cloud` in live
mode. The callback observes message header stamp, `width * height`, and
monotonic wall-clock arrival only; it never publishes or mutates the cloud. A
dedicated audit path is passed from the launch file. Shutdown writes the ROS
observation layer even when the gate fails.

The remote driver finalizes that layer after capture by joining:

- generated scan records from the same run's MID-360 metrics;
- ROS-received observations from the review node;
- cloud visibility measured on the synchronized native-RViz right panel;
- the semantically parsed RViz display contract.

The finalizer uses percentile interpolation documented in the JSON, reports
simulator and wall gaps separately, and fails closed on missing or malformed
inputs. Coverage accounts only for the overlapping generated/received time
window so startup/end differences remain visible and explainable.

## 5. Video cloud-visibility gate

The native display already renders the live cloud with the fixed cyan flat
color `(80, 225, 255)`. The validator inspects the right-panel RViz entity,
uses a declared region/color tolerance and minimum cloud-pixel/connected-area
threshold, and emits per-frame classifications or a compact trace. Warm-up is
derived from the first observed live-cloud frame rather than an arbitrary wall
delay. It reports total visible frames, post-warm-up ratio, and longest blank
run. Synthetic rendered-frame tests prove visible, blank, intermittent, and
false-color cases; the remote preflight supplies the runtime proof.

This image gate confirms visibility in the delivered capture, while the ROS
audit confirms data provenance and continuity. Neither substitutes for the
other.

## 6. Transfer-video pipeline

The full-resolution master is written once by the existing compositor and is
never used as an output target again. For CRF 22, 24, and 26, encode exclusive
temporary candidates with libx264 slow/high/yuv420p/BT.709, then validate each:

- strict ffprobe media contract and master frame/duration parity;
- error-sensitive full decode and decoded-frame parity;
- size reduction;
- SSIM, and VMAF only when the installed ffmpeg exposes `libvmaf`;
- sampled panel/detail quality plus manual contact-sheet inspection.

Select the smallest passing candidate, atomically promote it to the transfer
filename, preserve the master, and record all candidates and the rejection or
selection reason in `video_compression_manifest.json`. Temporary comparison
encodes may be removed only after their measurements are preserved; failed run
directories themselves are immutable.

## 7. Compatibility and failure behavior

- Replay mode keeps its existing snapshot behavior and tests.
- Live mode becomes fail-closed: audit disabled, no messages, empty messages,
  regressed stamps, excessive simulator gaps, inadequate coverage, or capture
  blanks make the preflight fail.
- Slow wall time alone never fails the 10 Hz sensor-frequency check.
- The dual-panel dimensions, positions, synchronization path, and master encode
  remain unchanged except for persistent live-cloud display.
- Any remote failure is preserved under its unique run ID. A source/config
  change after a failure requires the ledger to reflect the change before a
  new run.

## 8. Rollback

The final single fix commit is reverted with `git revert`. Reversion restores
the RViz live-cloud decay to `0.4000000059604645`, restores the old live-audit
parameters and driver packaging behavior, and restores the previous validator
schema. It does not delete r2.0.1 success/failure evidence or rewrite r2.0.0,
candidate38, or candidate39. The archived r2.0.1 documents explain how to run
the r2.0.0 ledger validator against the preserved parent record.
