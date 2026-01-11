#include "weapon.h"
#include "networkClass.h"
#include "gameGlobals.h"

NetworkClass *Weapon::_network_class = nullptr;

/**
 *
 */
void Weapon::
item_pre_frame() {

}

/**
 *
 */
void Weapon::
item_post_frame() {

}

/**
 *
 */
void Weapon::
item_busy_frame() {

}

/**
 *
 */
void Weapon::
abort_reload() {

}

/**
 *
 */
void Weapon::
activate() {

}

/**
 *
 */
void Weapon::
deactivate() {

}

/**
 * Returns a pointer to the player that owns this weapon.
 */
TFPlayer *Weapon::
get_owner() const {
  return (TFPlayer *)globals.get_do_by_id(player_id);
}

/**
 *
 */
void Weapon::
init_network_class() {
  BEGIN_NETWORK_CLASS(Weapon, Entity);
  _network_class->set_factory_func(make_Weapon);
  MAKE_NET_FIELD(Weapon, player_id, NetworkField::DT_int32);
  MAKE_NET_FIELD(Weapon, max_ammo, NetworkField::DT_uint16);
  MAKE_NET_FIELD(Weapon, max_ammo_2, NetworkField::DT_uint16);
  MAKE_NET_FIELD(Weapon, max_clip, NetworkField::DT_uint8);
  MAKE_NET_FIELD(Weapon, max_clip_2, NetworkField::DT_uint8);
  MAKE_NET_FIELD(Weapon, ammo, NetworkField::DT_uint16);
  MAKE_NET_FIELD(Weapon, ammo_2, NetworkField::DT_uint16);
  MAKE_NET_FIELD(Weapon, clip, NetworkField::DT_uint8);
  MAKE_NET_FIELD(Weapon, clip_2, NetworkField::DT_uint8);
  MAKE_NET_FIELD(Weapon, next_primary_attack, NetworkField::DT_float);
  MAKE_NET_FIELD(Weapon, next_secondary_attack, NetworkField::DT_float);
  MAKE_NET_FIELD(Weapon, time_weapon_idle, NetworkField::DT_float);
  END_NETWORK_CLASS();
}
