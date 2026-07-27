# J17A Front Pair 65 mm Adapted Rev B

Status: `accepted_model_baseline`

Dr Sun rejected Rev A and confirmed that the two front shallow chassis holes
are the intended screw interface. Rev B therefore aligns the two front J17A
screw axes to those two chassis axes. It does not add a new base or invent a
four-receiver chassis pattern.

The robot target pair is a `diameter 2.5 mm` central opening inside a shallow
`diameter 8.0 mm` cylindrical recess. Its measured centre pitch is
`64.999999659 mm`. The original J17A front pair is `diameter 4.5 mm` through
with `diameter 8.0 mm` counterbores at `67.882250994 mm` pitch. Rev B preserves
the source J17A unchanged and creates a separately named derived B-rep in
which only the two front stepped holes are filled and relocated to the exact
robot axes. Hole diameters and the rear J17A pair remain unchanged.

The complete J17A/J20A/S410/Mid-360 stack was translated rigidly by
`[-0.151878610, -3.128370000, +40.923512315] mm` in world `[X, Y, Z]`.
All occurrence rotation determinants remain `+1`. The adapted front-hole axes
have maximum line residual `3.0838e-13 mm`; the adapted body is one valid
solid B-rep with zero mesh bodies. Exact checks found no positive solid
intersection among the robot and four sensor bodies. Adapted-J17A-to-shell
minimum distance is numerical zero/contact.

This is a user-authorized model correction, not official factory CAD or a
fabrication release. The diameter difference is intentional: the J17A
`diameter 8 mm` recess seats the screw head, its `diameter 4.5 mm` bore clears
the shaft, and the chassis `diameter 2.5 mm` opening is the receiving/pilot
feature. Exact thread designation, screw length, engagement depth, torque,
material, anti-rotation, service access, and load path remain unresolved. Only
the front pair is aligned; the unchanged rear J17A pair is not claimed as
installed.

The Fusion document is named `Untitled`, is modified, and remains unsaved
in the active application tab. After Dr Sun said `继续，执行` on 2026-07-27,
the accepted state was frozen locally as:

- `lite3-j17a-front-pair-65mm-rev-b.f3d`: complete editable Fusion archive;
- `j17a-front-pair-65mm-adapted-rev-b.step`: lightweight adapted J17A only.

The local archive is the durable project copy. Acceptance applies to this
model baseline and front-pair relationship only; it is not a fabrication,
load, torque, or real-robot safety approval.
