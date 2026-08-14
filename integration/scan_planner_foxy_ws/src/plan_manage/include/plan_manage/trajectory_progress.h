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
}  // namespace scan_planner
