#pragma once

#include <cmath>
#include <vector>

#include <Eigen/Core>

namespace plan_env
{
inline std::vector<Eigen::Vector3d> occlusionShadowPoints(
    const Eigen::Vector3d &sensor_position,
    const Eigen::Vector3d &hit_position,
    double shadow_length,
    double resolution)
{
  const Eigen::Vector3d ray = hit_position - sensor_position;
  const double ray_length = ray.norm();
  if (!std::isfinite(shadow_length) || !std::isfinite(resolution) ||
      !std::isfinite(ray_length) || shadow_length <= 0.0 ||
      resolution <= 0.0 || ray_length <= 1.0e-9)
  {
    return {};
  }

  const Eigen::Vector3d direction = ray / ray_length;
  const auto sample_count = static_cast<std::size_t>(
      std::floor(shadow_length / resolution + 1.0e-9));
  std::vector<Eigen::Vector3d> points;
  points.reserve(sample_count);
  for (std::size_t index = 1; index <= sample_count; ++index)
    points.push_back(hit_position + direction * (resolution * index));
  return points;
}
}  // namespace plan_env
