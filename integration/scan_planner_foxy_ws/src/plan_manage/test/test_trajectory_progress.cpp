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

TEST(TrajectoryProgress, BoundsReplanCatchupBeforeStrictTracking)
{
  EXPECT_EQ(classifyTrajectoryCatchup(0.08, 0.10, 0.40),
            TrajectoryCatchupState::TRACKING);
  EXPECT_EQ(classifyTrajectoryCatchup(0.353, 0.10, 0.40),
            TrajectoryCatchupState::CATCHUP);
  EXPECT_EQ(classifyTrajectoryCatchup(0.401, 0.10, 0.40),
            TrajectoryCatchupState::REJECTED);
}

TEST(TrajectoryProgress, DefersCollisionReplanOnlyWhileCatchupIsActive)
{
  EXPECT_FALSE(isTrajectoryCatchupActive(TrajectoryCatchupState::TRACKING));
  EXPECT_TRUE(isTrajectoryCatchupActive(TrajectoryCatchupState::CATCHUP));
  EXPECT_FALSE(isTrajectoryCatchupActive(TrajectoryCatchupState::REJECTED));
  EXPECT_TRUE(shouldDeferCollisionReplan(true));
  EXPECT_FALSE(shouldDeferCollisionReplan(false));
}

TEST(TrajectoryProgress, CatchupVelocityClearsThePolicyDeadbandButStaysBounded)
{
  const Eigen::Vector2d slow = boundedCatchupVelocity(
      Eigen::Vector2d(0.15, 0.0), 0.8, 0.20, 1.0);
  EXPECT_NEAR(slow.x(), 0.20, 1.0e-9);
  EXPECT_NEAR(slow.y(), 0.0, 1.0e-9);

  const Eigen::Vector2d saturated = boundedCatchupVelocity(
      Eigen::Vector2d(2.0, 0.0), 0.8, 0.20, 1.0);
  EXPECT_NEAR(saturated.norm(), 1.0, 1.0e-9);
  EXPECT_NEAR(
      boundedCatchupVelocity(
          Eigen::Vector2d::Zero(), 0.8, 0.20, 1.0).norm(),
      0.0, 1.0e-9);
}
}  // namespace scan_planner
