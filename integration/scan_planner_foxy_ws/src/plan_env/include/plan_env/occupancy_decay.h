#pragma once

namespace plan_env
{

inline bool occupancyExpired(int current_update, int last_hit_update,
                             int maximum_age_updates)
{
  return maximum_age_updates > 0 && last_hit_update >= 0 &&
         current_update > last_hit_update &&
         current_update - last_hit_update > maximum_age_updates;
}

}  // namespace plan_env
