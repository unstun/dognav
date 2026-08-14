#include <gtest/gtest.h>

#include "plan_env/occupancy_decay.h"

TEST(OccupancyDecay, DisabledOrUnobservedCellsDoNotExpire)
{
  EXPECT_FALSE(plan_env::occupancyExpired(20, 1, 0));
  EXPECT_FALSE(plan_env::occupancyExpired(20, -1, 5));
}

TEST(OccupancyDecay, ExpiresOnlyAfterTheCompleteAgeWindow)
{
  EXPECT_FALSE(plan_env::occupancyExpired(15, 10, 5));
  EXPECT_TRUE(plan_env::occupancyExpired(16, 10, 5));
}
