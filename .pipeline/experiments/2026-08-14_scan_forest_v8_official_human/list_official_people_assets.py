"""List the official Isaac Sim 5.1 character folders available to the runtime."""

import json

from isaacsim import SimulationApp


ROOT = (
    "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/"
    "Isaac/People/Characters"
)

app = SimulationApp({"headless": True})

import omni.client  # noqa: E402


result, entries = omni.client.list(ROOT)
if result != omni.client.Result.OK:
    raise RuntimeError(f"could not list official People assets: {result}")
folders = sorted(
    entry.relative_path
    for entry in entries
    if entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN
)
versioned_folders = {"5.1": folders}
for version in ("5.0", "4.5", "4.2"):
    version_root = (
        "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/"
        f"{version}/Isaac/People/Characters"
    )
    version_result, version_entries = omni.client.list(version_root)
    versioned_folders[version] = (
        sorted(
            entry.relative_path
            for entry in version_entries
            if entry.flags & omni.client.ItemFlags.CAN_HAVE_CHILDREN
        )
        if version_result == omni.client.Result.OK
        else {"error": str(version_result)}
    )
candidate_files = {}
for folder in (
    "M_Medical_01",
    "male_adult_construction_01_new",
    "male_adult_construction_05_new",
    "male_adult_police_04",
    "original_male_adult_construction_01",
    "original_male_adult_construction_02",
    "original_male_adult_construction_03",
    "original_male_adult_construction_05",
    "original_male_adult_medical_01",
    "original_male_adult_police_04",
):
    child_result, child_entries = omni.client.list(f"{ROOT}/{folder}")
    if child_result != omni.client.Result.OK:
        candidate_files[folder] = {"error": str(child_result)}
        continue
    candidate_files[folder] = sorted(entry.relative_path for entry in child_entries)
    thumb_result, thumb_entries = omni.client.list(f"{ROOT}/{folder}/.thumbs")
    if thumb_result == omni.client.Result.OK:
        candidate_files[folder + ":thumbs"] = sorted(
            entry.relative_path for entry in thumb_entries
        )
    preview_result, preview_entries = omni.client.list(
        f"{ROOT}/{folder}/.thumbs/256x256"
    )
    if preview_result == omni.client.Result.OK:
        candidate_files[folder + ":preview"] = sorted(
            entry.relative_path for entry in preview_entries
        )
print(
    "OFFICIAL_PEOPLE_ASSETS="
    + json.dumps(
        {
            "root": ROOT,
            "folders": folders,
            "versioned_folders": versioned_folders,
            "candidate_files": candidate_files,
        },
        sort_keys=True,
    ),
    flush=True,
)
app.close()
