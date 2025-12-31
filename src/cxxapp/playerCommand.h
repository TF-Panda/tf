#ifndef PLAYERCOMMAND_H
#define PLAYERCOMMAND_H

#include "datagram.h"
#include "networkClass.h"
#include "luse.h"
#include "pointerToArray.h"
#include "typedObject.h"

/**
 * Player command RPC data.
 */
struct PlayerCommandArgs {
  int num_backup_commands;
  int num_new_commands;
  // Player command is a custom delta-encoded bit stream.
  Datagram data;

public:
  static NetworkClass *get_network_class() {
    return _network_class;
  }
  static void init_network_class() {
    BEGIN_NETWORK_CLASS_NOBASE(PlayerCommandArgs);
    MAKE_NET_FIELD(PlayerCommandArgs, num_backup_commands, NetworkField::DT_uint8);
    MAKE_NET_FIELD(PlayerCommandArgs, num_new_commands, NetworkField::DT_uint8);
    MAKE_NET_FIELD(PlayerCommandArgs, data, NetworkField::DT_datagram);
    END_NETWORK_CLASS();
  }
private:
  static NetworkClass *_network_class;
};

/**
 * Player command unpacked data.
 */
struct PlayerCommand : public TypedObject {
  DECLARE_CLASS(PlayerCommand, TypedObject);

public:
  unsigned int buttons = 0;
  LVecBase3f view_angles = 0.0f;
  LVecBase2f mouse_delta = 0.0f;
  LVecBase3f move = 0.0f;
  int weapon_select = -1;
  bool has_been_predicted = false;
  unsigned int tick_count = 0;
  unsigned int command_number = 0;
  unsigned int random_seed = 0;

  void clear();
  void read(DatagramIterator &scan, const PlayerCommand &prev);
  void write(Datagram &dg, const PlayerCommand &prev);
};
typedef PointerToArray<PlayerCommand> PTA_PlayerCommand;
typedef ConstPointerToArray<PlayerCommand> CPTA_PlayerCommand;

#endif // PLAYERCOMMAND_H
