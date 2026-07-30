# Current Lite3 Pro D435i Official B-rep Export Rev A

This evidence package extracts the real two-solid D435i B-rep that Fusion
cloud-translated from Intel's preserved official `D435i_Solid.SLDPRT`.  The
source F3D is the previously validated, small sensor-only assembly rather than
the crash-prone complete robot scene.

`export_d435i_brep_from_fusion.py` is export-only.  It requires the archived
F3D to be open in Fusion, selects the exact
`D435I_REAL_BREP_OFFICIAL_MANUFACTURER_CAD` component, asserts two solid B-rep
bodies and zero mesh bodies, and writes a standalone STEP plus a source/hash
report.  The independent FreeCAD round-trip check is added after export.

This package does not select the current-Pro camera pose or create printable
support geometry.  Those remain separate review and physical-interface gates.
