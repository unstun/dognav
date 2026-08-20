#ifndef SCAN_PLANNER_REFERENCE_PATH_HEIGHT_H
#define SCAN_PLANNER_REFERENCE_PATH_HEIGHT_H

#include <Eigen/Core>
#include <cmath>
#include <limits>
#include <string>
#include <vector>

namespace scan_planner
{
struct ReferencePathGroundSample
{
  double x;
  double y;
  double ground_z;
};

inline bool buildReferencePathBodyWaypoints(
    const std::vector<ReferencePathGroundSample> &samples, double body_height,
    double maximum_ground_step, std::vector<Eigen::Vector3d> *waypoints,
    std::string *error)
{
  if (waypoints == nullptr || error == nullptr)
    return false;
  waypoints->clear();
  error->clear();
  if (samples.empty())
  {
    *error = "reference path is empty";
    return false;
  }
  if (!std::isfinite(body_height) || body_height <= 0.0 ||
      !std::isfinite(maximum_ground_step) || maximum_ground_step < 0.0)
  {
    *error = "reference path height limits are invalid";
    return false;
  }
  waypoints->reserve(samples.size());
  double previous_ground_z = 0.0;
  bool have_previous = false;
  for (const auto &sample : samples)
  {
    if (!std::isfinite(sample.x) || !std::isfinite(sample.y) ||
        !std::isfinite(sample.ground_z))
    {
      *error = "reference path contains a non-finite coordinate";
      waypoints->clear();
      return false;
    }
    if (have_previous &&
        std::abs(sample.ground_z - previous_ground_z) > maximum_ground_step)
    {
      *error = "reference path ground height is locally discontinuous";
      waypoints->clear();
      return false;
    }
    waypoints->emplace_back(sample.x, sample.y, sample.ground_z + body_height);
    previous_ground_z = sample.ground_z;
    have_previous = true;
  }
  return true;
}

inline std::size_t nearestReferencePathSample(
    const std::vector<ReferencePathGroundSample> &samples,
    const Eigen::Vector3d &body_position)
{
  std::size_t nearest = 0;
  double nearest_distance_squared = std::numeric_limits<double>::infinity();
  for (std::size_t index = 0; index < samples.size(); ++index)
  {
    const double dx = samples[index].x - body_position.x();
    const double dy = samples[index].y - body_position.y();
    const double distance_squared = dx * dx + dy * dy;
    if (distance_squared < nearest_distance_squared)
    {
      nearest = index;
      nearest_distance_squared = distance_squared;
    }
  }
  return nearest;
}
} // namespace scan_planner

#endif
