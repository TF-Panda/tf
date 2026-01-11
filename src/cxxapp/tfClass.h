#ifndef TFCLASS_H
#define TFCLASS_H

#include "gameEnums.h"
#include "luse.h"

/**
 * Info for a TF2 player class.
 */
struct TFClassInfo {
  std::string name;
  Filename menu_weapon;
  Filename player_model;
  Filename view_model;
  float forward_factor;
  float backward_factor;
  float crouch_factor;
  float swimming_factor;
  float view_height;
  int max_health;
  std::string phonemes;
  LVector3 head_rotation_offset;
  bool dont_do_air_walk;
};

#endif // TFCLASS_H
