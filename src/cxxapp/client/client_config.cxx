#include "client_config.h"

ConfigVariableInt cl_cmd_rate
("cl-cmd-rate", 100,
 PRC_DESC("Rate at which the client sends player commands to the server."));

ConfigVariableInt cl_update_rate
("cl-update-rate", 20,
 PRC_DESC("Rate at which client should receive world updates from server."));

ConfigVariableDouble cl_interp
("cl-interp", 0.1,
 PRC_DESC("The duration world state updates are buffered for interpolation."));

ConfigVariableDouble cl_interp_ratio
("cl-interp-ratio", 2.0,
 PRC_DESC(""));

ConfigVariableBool cl_ping
("cl-ping", true,
 PRC_DESC("Toggles pinging the server to measure latency."));
ConfigVariableDouble cl_ping_interval
("cl-ping-interval", true,
 PRC_DESC("How often the client pings the server to measure latency."));
ConfigVariableBool cl_report_ping
("cl-report-ping", false,
 PRC_DESC("Should we print the latest ping measurement to console?"));
