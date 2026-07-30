# Current Lite3 Pro sensor-side interface contract Rev A

This evidence package extracts mounting axes from the preserved manufacturer
MID-360 STEP, the related Lite3 Venture S410 and J20A STEP/drawings, and the
official D435i mechanical drawing.  It is intentionally independent of the
current Lite3 Pro chassis receiver.

The package establishes:

- MID-360 to J20A: four M3 axes on a 48 x 36 mm pattern;
- S410 to J20A: four 5.2 mm guard clearances aligned to the modeled J20A M5
  receiver axes;
- D435i: two M3 rear receivers on 45 mm centres, 3 mm maximum insertion, and
  0.4 N m combined recommended torque.

It does not select screw lengths, infer current-Pro threads, or release any
part for printing or robot installation.

Run `extract_sensor_interfaces.py` with FreeCAD's Python runtime, then run
`build_interface_contract.py` with Python 3.
