#include <gtest/gtest.h>

#include <Eigen/Core>

#include "plan_manage/trajectory_progress.h"

namespace scan_planner
{
TEST(TrajectoryProgress, FreezesTheFormalRunCornerCut)
{
  const Eigen::Vector2d robot_position(2.5130047798, 0.6514075994);
  const Eigen::Vector2d candidate_position(2.8653264647, 0.4866866648);

  const auto decision = decideTrajectoryProgress(
      1.94, 0.01, 4.8, robot_position, candidate_position, 0.10);

  EXPECT_TRUE(decision.frozen);
  EXPECT_DOUBLE_EQ(decision.next_time, 1.94);
  EXPECT_GT(decision.tracking_error, 0.35);
}

TEST(TrajectoryProgress, AdvancesWhileRobotTracksAndClampsAtDuration)
{
  const Eigen::Vector2d robot_position(1.0, 0.5);
  const Eigen::Vector2d candidate_position(1.04, 0.53);

  const auto tracking = decideTrajectoryProgress(
      1.0, 0.01, 4.8, robot_position, candidate_position, 0.10);
  EXPECT_FALSE(tracking.frozen);
  EXPECT_DOUBLE_EQ(tracking.next_time, 1.01);

  const auto ending = decideTrajectoryProgress(
      4.795, 0.01, 4.8, robot_position, candidate_position, 0.10);
  EXPECT_FALSE(ending.frozen);
  EXPECT_DOUBLE_EQ(ending.next_time, 4.8);
}

TEST(TrajectoryProgress, FinishedStateLatchesAfterEnteringGoalTolerance)
{
  EXPECT_FALSE(shouldLatchTrajectoryFinished(false, 6.9, 7.0, 0.05, 0.15));
  EXPECT_FALSE(shouldLatchTrajectoryFinished(false, 7.0, 7.0, 0.16, 0.15));
  EXPECT_TRUE(shouldLatchTrajectoryFinished(false, 7.0, 7.0, 0.14, 0.15));
  EXPECT_TRUE(shouldLatchTrajectoryFinished(true, 7.0, 7.0, 0.30, 0.15));
}
}  // namespace scan_planner
