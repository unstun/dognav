import math
import unittest

from scene_preview_core import (
    OFFICE_FLOOR_LEVELS,
    OFFICE_TOUR_CAMERA_WAYPOINTS,
    candidate_uris,
    nearest_office_floor,
    office_global_camera_pose,
    office_tour_camera_pose,
    overview_camera,
    scene_views,
    validate_bounds,
)


class ScenePreviewCoreTest(unittest.TestCase):
    def test_warehouse_prefers_forklift_scene_with_official_fallback(self):
        uris = candidate_uris("omniverse://assets/Isaac", "warehouse")
        self.assertTrue(uris[0].endswith("warehouse_with_forklifts.usd"))
        self.assertTrue(uris[1].endswith("warehouse.usd"))

    def test_unknown_scene_fails_closed(self):
        with self.assertRaises(ValueError):
            candidate_uris("omniverse://assets/Isaac", "campus")

    def test_bounds_require_positive_finite_extents(self):
        self.assertEqual(
            validate_bounds((0, 0, 0, 10, 20, 5)),
            (0.0, 0.0, 0.0, 10.0, 20.0, 5.0),
        )
        for invalid in (
            (0, 0, 0, 0, 1, 1),
            (0, 0, 0, 1, 1, math.inf),
            (0, 0, 1, 1, 1, 0),
        ):
            with self.assertRaises(ValueError):
                validate_bounds(invalid)

    def test_overview_camera_looks_inside_bounds(self):
        camera = overview_camera((-10, -5, 0, 30, 15, 8))
        self.assertEqual(len(camera["eye"]), 3)
        self.assertEqual(camera["target"][:2], (10.0, 5.0))
        self.assertGreater(camera["eye"][2], 8.0)

    def test_scene_views_are_distinct_and_share_target(self):
        views = scene_views((-10, -5, 0, 30, 15, 8))
        self.assertEqual(
            set(views),
            {"overview", "reverse", "interior_long", "interior_cross"},
        )
        self.assertNotEqual(views["overview"]["eye"], views["reverse"]["eye"])
        self.assertEqual(views["overview"]["target"], views["reverse"]["target"])
        self.assertAlmostEqual(views["interior_long"]["eye"][2], 1.45)

    def test_office_tour_starts_and_ends_at_declared_waypoints(self):
        self.assertEqual(office_tour_camera_pose(0, 120), OFFICE_TOUR_CAMERA_WAYPOINTS[0])
        self.assertEqual(office_tour_camera_pose(119, 120), OFFICE_TOUR_CAMERA_WAYPOINTS[-1])
        eye, target = office_tour_camera_pose(60, 120)
        self.assertEqual(len(eye), 3)
        self.assertEqual(len(target), 3)
        with self.assertRaises(ValueError):
            office_tour_camera_pose(0, 1)
        with self.assertRaises(ValueError):
            office_tour_camera_pose(120, 120)

    def test_office_floor_assignment_and_global_camera_are_deterministic(self):
        self.assertEqual(nearest_office_floor(-3.2), OFFICE_FLOOR_LEVELS[0])
        self.assertEqual(nearest_office_floor(0.2), OFFICE_FLOOR_LEVELS[1])
        self.assertEqual(nearest_office_floor(3.4), OFFICE_FLOOR_LEVELS[2])
        self.assertEqual(nearest_office_floor(7.0), OFFICE_FLOOR_LEVELS[2])
        first = office_global_camera_pose((-24, 12, 6, 60), 0.0, 0, 72)
        last = office_global_camera_pose((-24, 12, 6, 60), 0.0, 71, 72)
        self.assertEqual(first, last)
        self.assertGreater(first[0][2], 48.0)
        with self.assertRaises(ValueError):
            nearest_office_floor(math.inf)
        with self.assertRaises(ValueError):
            office_global_camera_pose((0, 0, 0, 1), 0.0, 0, 72)


if __name__ == "__main__":
    unittest.main()
