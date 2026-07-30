# Superseded Torso-Only Extraction

Status: `superseded`

This extraction is not a complete Lite3 robot and must not be imported as the
baseline model.

The extracted geometry contains the central torso/body branch only. The four
leg assemblies are sibling branches in the source SolidWorks AP214 assembly and
are absent from both files below:

- `lite3-real-brep-lightweight.FCStd`
- `lite3-real-brep-lightweight.step`

The retained geometry is true B-rep rather than a triangle mesh, but that does
not make it a valid full-robot model. These files are preserved only as rejected
evidence of the failed extraction route.

Recorded SHA-256 values:

- `lite3-real-brep-lightweight.FCStd`:
  `df9dad7c970f42a63eb84d5f564498486b0a5df40c9494edac54002320a25d1e`
- `lite3-real-brep-lightweight.step`:
  `066ecebe3e5d4f9863b0b4087f2c20610ac917cf948f9c34dabee78d2de2d0c9`

Replacement route: import the original complete STEP assembly in Fusion and
preserve its native occurrence transforms. Exclude the separate exploration
backload only after the complete four-legged robot has been verified visually.
