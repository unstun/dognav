# Livox MID-360 Source-to-Isaac Comparison

| Property | Legacy Office input | New opt-in input | Evidence |
|---|---:|---:|---|
| ray pattern | uniform 16-channel grid | ordered non-repetitive MID-360 CSV | pinned Livox MIT repository |
| horizontal sampling | fixed 2 deg increments | source sequence spanning 360 deg | `mid360.csv` |
| elevation | fixed -7 to 52 deg lines | source sequence about -7.212 to 52.164 deg | `mid360.csv` |
| rays per 0.1 s scan | 2,880 | 20,000 | official 200,000 points/s at 10 Hz |
| blind-zone filter | 0.1 m | 0.1 m | official product specification |
| ray-cast maximum | 12 m | 40 m | official 10% reflectivity range |
| pattern cycle | repeats every scan | 800,000 rows / 40 scans / 4 s | pinned CSV and point rate |
| pose/stamp behavior | periodic cache could lag one physics interval | forced same-step pose refresh and one frame stamp | local integration contract |

The new mode is a geometric snapshot model. It does not simulate intensity,
reflectivity-dependent 70 m returns, multiple returns, rain/fog/dust,
electronic range noise, or motion distortion within a 0.1-second scan. Those
limits are recorded in each new run identity rather than hidden behind the
word "true".

SCAN's local occupancy window remains planner-owned. A 40 m ray-cast limit does
not turn its sliding collision map into a 40 m global SLAM map.
