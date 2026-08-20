#include <gtest/gtest.h>
#include <plan_manage/reference_path_height.h>

TEST(ReferencePathHeight, AddsBodyHeightAndKeepsThreeDimensionalRoute)
{
  const std::vector<scan_planner::ReferencePathGroundSample> samples{
      {0.0, 0.0, 0.0}, {1.0, 0.0, 0.12}, {2.0, 0.0, 0.28}};
  std::vector<Eigen::Vector3d> waypoints;
  std::string error;
  ASSERT_TRUE(scan_planner::buildReferencePathBodyWaypoints(
      samples, 0.40, 0.35, &waypoints, &error));
  ASSERT_EQ(waypoints.size(), 3U);
  EXPECT_DOUBLE_EQ(waypoints[0].z(), 0.40);
  EXPECT_DOUBLE_EQ(waypoints[1].z(), 0.52);
  EXPECT_DOUBLE_EQ(waypoints[2].z(), 0.68);
}

TEST(ReferencePathHeight, RejectsNonFiniteAndDiscontinuousGround)
{
  std::vector<Eigen::Vector3d> waypoints;
  std::string error;
  EXPECT_FALSE(scan_planner::buildReferencePathBodyWaypoints(
      {{0.0, 0.0, std::numeric_limits<double>::quiet_NaN()}},
      0.40, 0.35, &waypoints, &error));
  EXPECT_FALSE(scan_planner::buildReferencePathBodyWaypoints(
      {{0.0, 0.0, 0.0}, {1.0, 0.0, 0.50}},
      0.40, 0.35, &waypoints, &error));
}

TEST(ReferencePathHeight, ComputesNearestGroundSampleForResidualAudit)
{
  const std::vector<scan_planner::ReferencePathGroundSample> samples{
      {0.0, 0.0, 0.0}, {2.0, 0.0, 0.2}};
  EXPECT_EQ(scan_planner::nearestReferencePathSample(
                samples, Eigen::Vector3d(1.8, 0.1, 0.6)),
            1U);
}
