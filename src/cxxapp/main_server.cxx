#include "server.h"
#include "configVariableInt.h"

ConfigVariableInt sv_port("sv-port", "27015", PRC_DESC("Server port to talk over."));

int main(int argc, char *argv[]) {
  Server *sv = Server::ptr();

  sv->startup(sv_port);

  while (true) {
    sv->run_frame();
  }

  return 0;
}
