#ifndef GAMEENUMS_H
#define GAMEENUMS_H

#include "networkField.h"

enum EntityParentCode {
  EPC_unchanged = -1,
  EPC_render = -2,
  EPC_hidden = -3,
  EPC_viewmodel = -4,
  EPC_viemwodel_camera = -5,
  EPC_camera = -6,
  EPC_dyn_render = -7,
  EPC_skybox = -8,
};

enum TFTeam {
  TFTEAM_no_team,
  TFTEAM_spectate,
  TFTEAM_red,
  TFTEAM_blue,
};

enum InputCommand {
  IC_primary_attack = 1 << 0,
  IC_secondary_attack = 1 << 1,
  IC_move_forward = 1 << 2,
  IC_move_back = 1 << 3,
  IC_move_left = 1 << 4,
  IC_move_right = 1 << 5,
  IC_jump = 1 << 6,
  IC_duck = 1 << 7,
  IC_reload = 1 << 8,
  IC_walk = 1 << 9,
  IC_sprint = 1 << 10,
  IC_interact = 1 << 11,
  IC_pause = 1 << 12,
  IC_axis_move_x = 1 << 13,
  IC_axis_move_y = 1 << 14,
  IC_axis_look_x = 1 << 15,
  IC_axis_look_y = 1 << 16,
};

/**
 * Player class.
 */
enum TFClass {
  TFCLASS_scout,
  TFCLASS_soldier,
  TFCLASS_pyro,
  TFCLASS_demoman,
  TFCLASS_hwguy,
  TFCLASS_engineer,
  TFCLASS_sniper,
  TFCLASS_medic,
  TFCLASS_spy,
  TFCLASS_COUNT,
};
template<>
struct NetworkFieldTypeTraits<TFClass> : NetworkFieldTypeTraits<int> { };

/**
 *
 */
enum VoiceCommand {
  VOICECOMMAND_help,
  VOICECOMMAND_thanks,
  VOICECOMMAND_medic,
  VOICECOMMAND_go,
  VOICECOMMAND_move_up,
  VOICECOMMAND_go_left,
  VOICECOMMAND_go_right,
  VOICECOMMAND_yes,
  VOICECOMMAND_no,
  VOICECOMMAND_incoming,
  VOICECOMMAND_spy,
  VOICECOMMAND_sentry_ahead,
  VOICECOMMAND_teleporter_here,
  VOICECOMMAND_sentry_here,
  VOICECOMMAND_activate_charge,
  VOICECOMMAND_charge_ready,
  VOICECOMMAND_battle_cry,
  VOICECOMMAND_cheers,
  VOICECOMMAND_jeers,
  VOICECOMMAND_positive,
  VOICECOMMAND_negative,
  VOICECOMMAND_nice_shot,
  VOICECOMMAND_good_job,
};

/**
 * Bitmasks identifying camera type.  Used for hiding/showing nodes
 * from specific cameras.
 */
enum CameraMask {
  CAMERAMASK_main = 1 << 0,
  CAMERAMASK_reflection = 1 << 1,
  CAMERAMASK_shadow = 1 << 2,
};

enum CollisionMask {
  CollideMask_world = 1 << 0,
  CollideMask_sky = 1 << 1,
  CollideMask_player_clip = 1 << 2,
  CollideMask_red_player = 1 << 3,
  CollideMask_red_building = 1 << 4,
  CollideMask_blue_player = 1 << 5,
  CollideMask_blue_building = 1 << 6,
  CollideMask_projectile = 1 << 7,
  CollideMask_hitbox = 1 << 8,
  // Gibs, weapon drops, etc.
  CollideMask_debris = 1 << 9,
  CollideMask_trigger = 1 << 10,
  // Special bit for teleporters because all players collide
  // with teleporters on both teams.
  CollideMask_teleporter = 1 << 11,

  CollideMask_player = CollideMask_red_player | CollideMask_blue_player,
  CollideMask_building = CollideMask_red_building | CollideMask_blue_building | CollideMask_teleporter,
  CollideMask_red = CollideMask_red_player | CollideMask_red_building | CollideMask_teleporter,
  CollideMask_blue = CollideMask_blue_player | CollideMask_blue_building | CollideMask_teleporter,
  CollideMask_all_team = CollideMask_player | CollideMask_building,
  // What bullets collide with.
  CollideMask_bullet_collide = CollideMask_all_team | CollideMask_world | CollideMask_hitbox
                               | CollideMask_projectile | CollideMask_debris,
  // What debris collides with.
  CollideMask_debris_collide = CollideMask_world,
};

enum CollideShape {
  CollideShape_empty, // Nothing.
  CollideShape_box, // Bounding box.
  CollideShape_sphere, // Bounding sphere.
  CollideShape_model, // Use model collision data.
};

enum CollideFlag {
  CollideFlag_intangible = 0,
  CollideFlag_tangible = 1 << 0,
  CollideFlag_trigger = 1 << 1,
};

#endif // GAMEENUMS_H
