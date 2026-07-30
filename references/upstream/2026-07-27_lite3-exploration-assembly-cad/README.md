# Lite3 Exploration Assembly CAD

This directory preserves the user-provided STEP assembly downloaded as
`6074-Lite3探索版总装.STEP`.

## What Was Verified

- The preserved file is byte-for-byte identical to the download.
- The file is an ISO 10303-21 STEP AP214 export written by SolidWorks 2020.
- The source uses millimetres and contains B-rep solids and an assembly tree;
  it is not a tessellated mesh-only model.
- The top-level product is named `Lite3探索版总装`.
- Its robot-base child is named `Lite3体验版总装.STEP`.
- Its second top-level child is an exploration backload module containing the
  BZ20 shell/base and a backload expansion board.

The exact commercial variant identity is therefore unresolved. This source is
useful as a real editable Lite3 assembly and visual/packaging reference, but it
does not by itself prove that the chassis is Lite3 Pro.

## Provenance And Redistribution Boundary

The source came from Dr Sun's local Downloads folder. No public download URL,
license, or redistribution permission accompanied it. It is retained as a
local research source and must not be republished until provenance and
redistribution rights are established.

## Current Use

The active unsaved Fusion preview imports the real B-rep robot base, hides the
separate exploration backload module, and places the reviewed Venture sensor
stack above it without adding an external industrial computer. The
manufacturer's native internal robot parts remain unchanged.

The current geometry scan did not find the previously documented Lite3 Pro
`74 x 94 mm` four-hole rectangle on this source chassis. The preview therefore
proves editable geometry, appearance, pose alignment, and nominal packaging
only. It does not prove a direct bolt-on installation or manufacturing fit.
