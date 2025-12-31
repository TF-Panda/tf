#ifndef CLIENT_CONFIG_H
#define CLIENT_CONFIG_H

#include "pandabase.h"
#include "configVariableBool.h"
#include "configVariableInt.h"
#include "configVariableDouble.h"

extern ConfigVariableInt cl_cmd_rate;
extern ConfigVariableInt cl_update_rate;
extern ConfigVariableDouble cl_interp;
extern ConfigVariableDouble cl_interp_ratio;
extern ConfigVariableBool cl_ping;
extern ConfigVariableDouble cl_ping_interval;
extern ConfigVariableBool cl_report_ping;

/**
 * Returns proper buffering duration for interpolation, factoring
 * in interp and interp ratio.
 */
inline float
get_client_interp_amount() {
  return (float)std::max(cl_interp.get_value(), cl_interp_ratio.get_value() / (double)cl_update_rate.get_value());
}

#endif // CLIENT_CONFIG_H
