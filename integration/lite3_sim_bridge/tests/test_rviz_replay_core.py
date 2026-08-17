import unittest

from lite3_sim_bridge.rviz_replay_core import ReplayAuditState


class ReplayAuditStateTests(unittest.TestCase):
    def test_passing_summary_preserves_replay_only_claim(self):
        state = ReplayAuditState(sample_count=160)
        self.assertTrue(state.accept_body_stamp(10))
        self.assertTrue(state.accept_body_stamp(20))
        state.accept_bspline(7, 160, 15)
        state.accept_bbox_snapshot("frame_000001.npz")
        state.accept_voxel_snapshot("frame_000001.npz", 100, 500)
        state.record_preloaded_snapshot("frame_000001.npz")

        summary = state.summary()

        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["trajectory_ids"], [7])
        self.assertEqual(summary["trajectory_point_counts"], {"7": 160})
        self.assertIn("replay-only", summary["claim_boundary"])
        self.assertIn("no planning", summary["claim_boundary"])
        self.assertEqual(summary["bbox_publish_count"], 1)
        self.assertEqual(summary["bbox_snapshot_files"], ["frame_000001.npz"])
        self.assertEqual(summary["voxel_publish_count"], 1)
        self.assertEqual(summary["preloaded_snapshot_file"], "frame_000001.npz")
        self.assertEqual(
            summary["voxel_point_counts"]["frame_000001.npz"],
            {"raw": 100, "inflated": 500},
        )

    def test_non_increasing_body_stamp_is_rejected_and_audited(self):
        state = ReplayAuditState(sample_count=10)
        self.assertTrue(state.accept_body_stamp(20))
        self.assertFalse(state.accept_body_stamp(20))

        summary = state.summary()

        self.assertEqual(summary["body_pose_count"], 1)
        self.assertEqual(summary["rejected_body_pose_count"], 1)
        self.assertFalse(summary["checks"]["body_stamps_strictly_increase"])
        self.assertEqual(summary["status"], "FAIL")

    def test_wrong_sample_count_is_rejected(self):
        state = ReplayAuditState(sample_count=160)

        with self.assertRaisesRegex(ValueError, "expected 160"):
            state.accept_bspline(3, 159, 100)

    def test_empty_voxel_snapshot_is_rejected(self):
        state = ReplayAuditState(sample_count=160)

        with self.assertRaisesRegex(ValueError, "must be non-empty"):
            state.accept_voxel_snapshot("frame.npz", 0, 5)


if __name__ == "__main__":
    unittest.main()
