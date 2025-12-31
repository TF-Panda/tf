#include "playerCommand.h"
#include "randomizer.h"
#include <limits>

NetworkClass *PlayerCommandArgs::_network_class = nullptr;
TypeHandle PlayerCommand::_type_handle;

/**
 *
 */
void PlayerCommand::
clear() {
  buttons = 0;
  view_angles = 0.0f;
  mouse_delta = 0.0f;
  move = 0.0f;
  weapon_select = -1;
  has_been_predicted = false;
  tick_count = 0;
  command_number = 0;
  random_seed = 0;
}

/**
 *
 */
void PlayerCommand::
read(DatagramIterator &scan, const PlayerCommand &prev) {
  if (scan.get_bool()) {
    command_number = scan.get_uint32();
  } else {
    // Assume steady increment.
    command_number = prev.command_number + 1;
  }

  Randomizer random(command_number);
  random_seed = random.random_int(std::numeric_limits<int>::max());

  if (scan.get_bool()) {
    tick_count = scan.get_uint32();
  } else {
    // Assume steady increment.
    tick_count = prev.tick_count + 1;
  }

  if (scan.get_bool()) {
    view_angles.read_datagram_fixed(scan);
  }

  if (scan.get_bool()) {
    move.read_datagram_fixed(scan);
  }

  if (scan.get_bool()) {
    buttons = scan.get_uint32();
  }

  if (scan.get_bool()) {
    weapon_select = scan.get_int8();
  }

  if (scan.get_bool()) {
    mouse_delta.read_datagram_fixed(scan);
  }
}

/**
 *
 */
void PlayerCommand::
write(Datagram &dg, const PlayerCommand &prev) {
  if (command_number != (prev.command_number + 1)) {
    dg.add_bool(true);
    dg.add_uint32(command_number);
  } else {
    dg.add_bool(false);
  }

  if (tick_count != (prev.tick_count + 1)) {
    dg.add_bool(true);
    dg.add_uint32(tick_count);
  } else {
    dg.add_bool(false);
  }

  if (view_angles != prev.view_angles) {
    dg.add_bool(true);
    view_angles.write_datagram_fixed(dg);
  } else {
    dg.add_bool(false);
  }

  if (move != prev.move) {
    dg.add_bool(true);
    move.write_datagram_fixed(dg);
  } else {
    dg.add_bool(false);
  }

  if (buttons != prev.buttons) {
    dg.add_bool(true);
    dg.add_uint32(buttons);
  } else {
    dg.add_bool(false);
  }

  if (weapon_select != prev.weapon_select) {
    dg.add_bool(true);
    dg.add_int8(weapon_select);
  } else {
    dg.add_bool(false);
  }

  if (mouse_delta != prev.mouse_delta) {
    dg.add_bool(true);
    mouse_delta.write_datagram_fixed(dg);
  } else {
    dg.add_bool(false);
  }
}
