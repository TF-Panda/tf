
#include "server.h"
#include "configVariableInt.h"
#include "networkClasses.h"

ConfigVariableInt sv_port("sv-port", "27015", PRC_DESC("Server port to talk over."));

/**
 * Server entry point.
 */
int
main(int argc, char *argv[]) {
  init_network_classes();
  
  Server *sv = Server::ptr();

  sv->startup(sv_port);

  while (true) {
    sv->run_frame();
  }

  return 0;
}
