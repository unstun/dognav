#include <gtest/gtest.h>

#include <Eigen/Core>

#include "plan_env/occlusion_shadow.h"

namespace plan_env
{
TEST(OcclusionShadow, ExtendsBehindARealLidarHitAtVoxelResolution)
{
  const Eigen::Vector3d sensor(0.0, 0.0, 0.4);
  const Eigen::Vector3d hit(1.7, 0.0, 0.4);

  const auto points = occlusionShadowPoints(sensor, hit, 0.70, 0.05);

  ASSERT_EQ(points.size(), 14U);
  EXPECT_NEAR(points.front().x(), 1.75, 1.0e-9);
  EXPECT_NEAR(points.back().x(), 2.40, 1.0e-9);
  EXPECT_NEAR(points.back().y(), 0.0, 1.0e-9);
  EXPECT_NEAR(points.back().z(), 0.4, 1.0e-9);
}

TEST(OcclusionShadow, RejectsDegenerateOrDisabledInputs)
{
  const Eigen::Vector3d point(1.0, 2.0, 3.0);
  EXPECT_TRUE(occlusionShadowPoints(point, point, 0.70, 0.05).empty());
  EXPECT_TRUE(occlusionShadowPoints(Eigen::Vector3d::Zero(), point, 0.0, 0.05).empty());
  EXPECT_TRUE(occlusionShadowPoints(Eigen::Vector3d::Zero(), point, 0.70, 0.0).empty());
}
}  // namespace plan_env
