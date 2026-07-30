# Lite3 Current-Pro Revision Audit

This source snapshot prevents the purchased current Lite3 Pro from being
silently modelled as the older Pro documented by User Manual V1.0.7-0.

The official 2025 brochure reports Pro at `610 x 370 x 450 mm`, `12.9 kg`, and
`4 kg` walking load.  The legacy 2024 manual reports `610 x 370 x 445 mm` and
`12.7 kg`, and is the only official file found with the `4 x M3`, `74 x 94 mm`
mounting drawing.  That pattern is therefore retained as legacy,
version-specific evidence rather than transferred to the current robot.

The official current Pro and LiDAR product images share the long
rear/centre compute enclosure visible in Dr Sun's physical photograph.  The
LiDAR module sits ahead of that enclosure.  The images establish layout and
revision identity only; they do not reveal the hidden carrier or usable hole
axes.

The official FAST-LIVO2 repository at pinned commit
`624b45c90bb76484a1612eaf243b962461c84819` explicitly scopes its printable
hardware to Lite3 Venture.  It does not supply current-Pro robot-side bracket
CAD.  Its README snapshot is accompanied by the pinned GPL-2.0 license text.

See `source_record.yaml` for hashes, URLs, claim boundaries, and the physical
measurements required before a current-Pro lower adapter can be released.
