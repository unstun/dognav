#pragma once

#include <algorithm>

#include <Eigen/Core>

namespace scan_planner
{
struct TrajectoryProgressDecision
{
  double next_time;
  double tracking_error;
  bool frozen;
};

enum class TrajectoryCatchupState
{
  TRACKING,
  CATCHUP,
  REJECTED,
};

inline TrajectoryCatchupState classifyTrajectoryCatchup(
    double start_error, double strict_tracking_error,
    double maximum_catchup_error)
{
  if (start_error <= strict_tracking_error)
    return TrajectoryCatchupState::TRACKING;
  if (start_error <= maximum_catchup_error)
    return TrajectoryCatchupState::CATCHUP;
  return TrajectoryCatchupState::REJECTED;
}

inline bool shouldDeferCollisionReplan(bool catchup_active)
{
  return catchup_active;
}

inline bool isTrajectoryCatchupActive(TrajectoryCatchupState state)
{
  return state == TrajectoryCatchupState::CATCHUP;
}

inline Eigen::Vector2d boundedCatchupVelocity(
    const Eigen::Vector2d &position_error, double gain,
    double minimum_speed, double maximum_speed)
{
  const Eigen::Vector2d requested = gain * position_error;
  const double norm = requested.norm();
  if (norm < 1.0e-9 || maximum_speed <= 0.0)
    return Eigen::Vector2d::Zero();
  const double bounded_norm = std::min(
      maximum_speed, std::max(0.0, std::max(minimum_speed, norm)));
  return requested / norm * bounded_norm;
}

inline TrajectoryProgressDecision decideTrajectoryProgress(
    double current_time, double dt, double duration,
    const Eigen::Vector2d &current_position,
    const Eigen::Vector2d &candidate_position,
    double max_tracking_error)
{
  const double candidate_time = std::min(duration, current_time + std::max(0.0, dt));
  const double tracking_error = (candidate_position - current_position).norm();
  const bool frozen = tracking_error > max_tracking_error;
  return {frozen ? current_time : candidate_time, tracking_error, frozen};
}

inline bool shouldLatchTrajectoryFinished(
    bool already_finished, double execution_time, double duration,
    double position_error, double finish_distance)
{
  return already_finished ||
         (execution_time >= duration && position_error < finish_distance);
}
}  // namespace scan_planner
