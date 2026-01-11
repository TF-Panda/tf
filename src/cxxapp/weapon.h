#ifndef WEAPON_H
#define WEAPON_H

#include "entity.h"

class TFPlayer;

/**
 * Base class for a weapon.
 */
class Weapon : public Entity {
public:
  virtual void item_pre_frame();
  virtual void item_busy_frame();
  virtual void item_post_frame();
  virtual void abort_reload();
  virtual void activate();
  virtual void deactivate();

  TFPlayer *get_owner() const;

public:
  DO_ID player_id = 0;
  int max_ammo = 0, max_ammo_2 = 0;
  int max_clip = 0, max_clip_2 = 0;
  int ammo = 0, ammo_2 = 0;
  int clip = 0, clip_2 = 0;
  float next_primary_attack = 0.0f;
  float next_secondary_attack = 0.0f;
  float time_weapon_idle = 0.0f;

  // Net class stuff
public:
  inline static NetworkObject *make_Weapon() {
    return new Weapon;
  }
  virtual NetworkClass *get_network_class() const override {
    return _network_class;
  }
  static NetworkClass *get_type_network_class() {
    return _network_class;
  }
  static void init_network_class();
private:
  static NetworkClass *_network_class;
};

#endif // WEAPON_H
