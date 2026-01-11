#include "prediction.h"
#include "client.h"
#include "../gameGlobals.h"
#include "localTFPlayer.h"
#include "../tfPlayer.h"

Prediction *Prediction::_global_ptr = nullptr;

constexpr float prediction_on_epsilon = 0.1f;
constexpr float prediction_max_forward = 6.0f;
constexpr float prediction_min_correction_distance = 0.25f;
constexpr float prediction_min_epsilon = 0.5f;
constexpr float prediction_max_error = 64.0f;

/**
 *
 */
PredictionCopy::
PredictionCopy(CopyMode _mode, PredictedObject *_obj, PTA_uchar _dest, PTA_uchar _src, bool _count_errors,
	       bool _report_errors, bool _perform_copy) :
  mode(_mode),
  obj(_obj),
  src_buf(_src),
  dest_buf(_dest),
  error_check(_count_errors),
  report_errors(_report_errors),
  perform_copy(_perform_copy),
  current_command_reference(0),
  dest_slot(0),
  cmd_num(0),
  ent(_obj->entity)
{
}

/**
 *
 */
int PredictionCopy::
transfer_data(int current_command_reference, int dest_slot) {
  current_command_reference = current_command_reference;
  dest_slot = dest_slot;
  cmd_num = current_command_reference + dest_slot;

  for (size_t i = 0; i < obj->fields.size(); ++i) {
    const PredictionFieldBase *field = obj->fields[i];

    bool ignore_field = false;
    if (field->is_private) {
      ignore_field = true;
    } else if (mode == CM_non_networked_only && field->networked) {
      ignore_field = true;
    } else if (mode == CM_networked_only && !field->networked) {
      ignore_field = true;
    }

    field->transfer(this);
  }

  return error_count;
}

/**
 *
 */
void PredictedObject::
calc_sizes() {
  encoded_size = 0u;

  for (int i = 0; i < fields.size(); ++i) {
    PredictionFieldBase *pred_field = fields[i];
    pred_field->offset = encoded_size;
    pred_field->stride = pred_field->get_stride();
    encoded_size += pred_field->stride;
  }
}

/**
 * Copies current data from the entity into the prediction history buffer at the given slot.
 */
int PredictedObject::
save_data(int slot, PredictionCopy::CopyMode mode) {
  PTA_uchar dest = alloc_slot(slot);
  if (slot != -1) {
    intermediate_data_count = slot;
  }
  PredictionCopy copy(mode, this, dest, PTA_uchar());
  return copy.transfer_data();
}

/**p
 * Copies data from the prediction history buffer at the given slot back into the entity.
 */
int PredictedObject::
restore_data(int slot, PredictionCopy::CopyMode mode) {
  PTA_uchar src = alloc_slot(slot);
  PredictionCopy copy(mode, this, PTA_uchar(), src);
  return copy.transfer_data();
}

/**
 * Allocates an intermediate result buffer at the indicated slot, and returns
 * the buffer.
 */
PTA_uchar PredictedObject::
alloc_slot(int slot) {
  nassertr(slot >= -1, PTA_uchar());

  if (slot == -1) {
    if (original_data.is_null()) {
      original_data.resize(encoded_size);
      memset(original_data.p(), 0, encoded_size);
    }
    return original_data;

  } else {
    slot = slot % prediction_num_data_slots;
    if (data_slots[slot].is_null()) {
      data_slots[slot].resize(encoded_size);
      memset(data_slots[slot].p(), 0, encoded_size);
    }
    return data_slots[slot];
  }
}

/**
 *
 */
CPTA_uchar PredictedObject::
get_slot(int slot) const {
  nassertr(slot >= 0 && slot < prediction_num_data_slots, CPTA_uchar());
  return data_slots[slot];
}

/**
 *
 */
void PredictedObject::
shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run) {
  nassertv(num_cmds_run >= slots_to_remove);

  pvector<PTA_uchar> saved;
  saved.reserve(slots_to_remove);

  int i = 0;
  // Remember first slots.
  while (i < slots_to_remove) {
    saved.push_back(data_slots[i]);
    ++i;
  }
  // Move rest of slots forward up to last slot.
  while (i < num_cmds_run) {
    data_slots[i - slots_to_remove] = data_slots[i];
    ++i;
  }
  // Put remembered slots onto end.
  for (i = 0; i < slots_to_remove; ++i) {
    int slot = num_cmds_run - slots_to_remove + i;
    data_slots[slot] = saved[i];
  }
}

/**
 *
 */
void PredictedObject::
pre_entity_packet_received(int commands_acked) {
  bool copy_intermediate = (commands_acked > 0);

  if (copy_intermediate) {
    restore_data(commands_acked - 1, PredictionCopy::CM_non_networked_only);
    restore_data(-1, PredictionCopy::CM_networked_only);
  } else {
    restore_data(-1, PredictionCopy::CM_everything);
  }
}

/**
 *
 */
void PredictedObject::
post_entity_packet_received() {
  save_data(-1, PredictionCopy::CM_networked_only);
}

/**
 *
 */
bool PredictedObject::
post_networked_data_received(int commands_acked, int curr_reference) {
  bool had_errors = false;
  bool error_check = (commands_acked > 0);

  save_data(-1, PredictionCopy::CM_everything);

  if (error_check) {
    PTA_uchar predicted_state_data = alloc_slot(commands_acked - 1);
    PTA_uchar original_state_data = alloc_slot(-1);
    bool count_errors = true;
    bool copy_data = false;
    PredictionCopy copy(PredictionCopy::CM_networked_only, this, predicted_state_data, original_state_data,
			count_errors, true, copy_data);
    int error_count = copy.transfer_data(curr_reference, commands_acked - 1);
    if (error_count > 0) {
      had_errors = true;
    }
  }

  return had_errors;
}

/**
 *
 */
void Prediction::
check_error(int commands_acked) {
  if (commands_acked > prediction_num_data_slots) {
    return;
  }

  LocalTFPlayer *local_player = globals.local_avatar->get_local_player();
  if (local_player != nullptr) {
    return;
  }

  PredictedObject *pred = globals.local_avatar->get_pred();
  if (pred == nullptr) {
    return;
  }
  if (local_av_pos_field == nullptr) {
    PredictedObject::PredFields::iterator it = std::find_if(pred->fields.begin(), pred->fields.end(), [](PredictionFieldBase *field)
    {
      return field->name == "pos";
    });
    if (it != pred->fields.end()) {
      local_av_pos_field = (PredictionFieldTempl<LVecBase3f> *)(*it).p();
    }
  }
  LPoint3f predicted_pos = local_av_pos_field->get_value(pred->get_slot(commands_acked - 1), globals.local_avatar);

  LPoint3f net_pos = globals.local_avatar->get_pos();
  // Compare what the server returned with that we had predicted it to be.
  LVector3f delta = predicted_pos - net_pos;
  float length = delta.length();
  if (length > prediction_max_error) {
    // A teleport or something, clear out error.
    length = 0.0f;
  } else {
    if (length > prediction_min_epsilon) {
      local_player->note_prediction_error(delta);
      // Difference is outside tolerance but within an acceptable amount to
      // smooth it out.
      std::cerr << "Prediction error " << length << " units (" << delta[0] << " " << delta[1] << " " << delta[2] << ")\n";
    }
  }
}

/**
 *
 */
void Prediction::
pre_entity_packet_received(int commands_acked, int current_world_update_packet) {
  // Cache off incoming packet #

  // Transfer intermediate data from other predictables.
  for (PredictedObject *p : predictables) {
    p->pre_entity_packet_received(commands_acked);
  }
}

/**
 *
 */
void Prediction::
post_entity_packet_received() {
  // Transfer intermediate data from other predictables.
  for (PredictedObject *p : predictables) {
    p->post_entity_packet_received();
  }
}

/**
 *
 */
void Prediction::
on_receive_uncompressed_packet() {
  num_commands_predicted = 0;
  num_server_commands_acknowledged = 0;
  previous_start_frame = -1;
}

/**
 * Called at the end of the frame if any packets were received.
 */
void Prediction::
post_network_data_received(int commands_acked) {
  num_server_commands_acknowledged += commands_acked;
  previous_ack_had_errors = false;

  // Transfer intermediate data from other predictables.
  for (PredictedObject *p : predictables) {
    p->post_networked_data_received(num_server_commands_acknowledged, current_command_reference);
  }
}

/**
 * Restores all predicted entities to their most recently networked state.
 */
void Prediction::
restore_original_entity_state() {
  for (PredictedObject *p : predictables) {
    p->restore_data(-1, PredictionCopy::CM_everything);
  }
}

/**
 *
 */
void Prediction::
restore_entity_to_predicted_frame(int frame) {
  for (PredictedObject *p : predictables) {
    p->restore_data(frame, PredictionCopy::CM_everything);
  }
}

/**
 *
 */
void Prediction::
shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run) {
  for (PredictedObject *p : predictables) {
    p->shift_intermediate_data_forward(slots_to_remove, num_cmds_run);
  }
}

/**
 *
 */
void Prediction::
store_prediction_results(int slot) {
  for (PredictedObject *p : predictables) {
    p->save_data(slot, PredictionCopy::CM_everything);
  }
}

/**
 *
 */
int Prediction::
compute_first_command_to_execute(bool received_world_update, int incoming_acked, int outgoing_command) {
  int dest_slot = 1;
  int skip_ahead = 0;

  // If we didn't receive a new update (or we received an update that didn't ack any PlayerCommands
  // so for the player it should be just like receiving no update), just jump right up to the very
  // last command we created for this very frame since we probably wouldn't have had any errors
  // without being notified by the server of such a case.
  if (!received_world_update || num_server_commands_acknowledged == 0) {
    // This is where we would normally start.
    int start = incoming_acked + 1;
    // outgoing_command is where we really want to start.
    skip_ahead = std::max(0, outgoing_command - start);
    // Don't start past the last predicted command, though, or we'll get prediction errors.
    skip_ahead = std::min(skip_ahead, num_commands_predicted);

    // Always restore since otherwise we might start prediction using an "interpolated"
    // value instead of a purely predicted value.
    restore_entity_to_predicted_frame(skip_ahead - 1);

  } else {
    // Otherwise, there is a second optimization, wherein if we did receive an update, but no
    // values differed (or were outside their epsilon) and the server actually acknlowledged running
    // one or more commands, then we can revert the entity to the predicted state from last frame,
    // shift the # of commands worth of intermediate state off of front the intermediate state array,
    // and only predict the PlayerCommand from the latest render frame.
    if (!previous_ack_had_errors && num_commands_predicted > 0 && num_server_commands_acknowledged <= num_commands_predicted) {
      // Copy all of the previously predicted data back into the entities so we can skip
      // repredicting it.  This is the final slot that we previously predicted.
      restore_entity_to_predicted_frame(num_commands_predicted - 1);
      skip_ahead = num_commands_predicted - num_server_commands_acknowledged;

    } else {
      if (previous_ack_had_errors) {
	// If an entity gets a prediction error, then we want to clear out its interpolated variables
	// so we don't mix different samples at the same timestamps.  We subtract 1 tick interval
	// here because if we don't, we'll have 3 interpolation entries with the same timestamp as
	// this predicted frame, so we don't be able to interpolate (which leads to jerky movement)
	// in the player when ANY entity like your gun gets a prediction error).

	globals.cr->enter_simulation_time(globals.local_avatar->get_tick_base() - 1);

	for (PredictedObject *p : predictables) {
	  ((NetworkObject *)p->entity)->reset_interpolated_vars();
	}

	globals.cr->exit_simulation_time();
      }
    }
  }

  dest_slot += skip_ahead;
  // Always reset these values now that we handled them.
  num_commands_predicted = 0;
  previous_ack_had_errors = false;
  num_server_commands_acknowledged = 0;

  return dest_slot;
}

/**
 *
 */
bool Prediction::
perform_prediction(bool received_world_update, TFPlayer *local_avatar, int incoming_acked, int outgoing_cmd) {
  in_prediction = true;

  LocalTFPlayer *local_player = local_avatar->get_local_player();
  nassertr(local_player != nullptr, false);

  int i = compute_first_command_to_execute(received_world_update, incoming_acked, outgoing_cmd);
  nassertr(i >= 1, false);
  while (true) {
    // incoming_acknowledged is the last PlayerCommand the server acknowledged having
    // acted upon.
    int curr_cmd = incoming_acked + i;

    // Have we caught up to the current command?
    if (curr_cmd > outgoing_cmd) {
      break;
    }

    if (i >= prediction_num_data_slots) {
      break;
    }

    PlayerCommand *cmd = local_player->get_command(curr_cmd);
    if (cmd == nullptr) {
      break;
    }

    // Is this the first time predicting this?
    first_time_predicted = !cmd->has_been_predicted;

    run_simulation(curr_cmd, cmd, local_avatar);

    globals.cr->enter_simulation_time(cmd->tick_count, local_avatar->get_tick_base());

    // Store intermediate data into appropriate slot.
    store_prediction_results(i - 1); // Note that i start at 1.

    num_commands_predicted = i;

    if (curr_cmd == outgoing_cmd) {
      local_player->set_final_predicted_tick(local_avatar->get_tick_base());
      final_predicted_tick = local_avatar->get_tick_base();
    }

    // Mark that we issued any needed sounds, if not done already.
    cmd->has_been_predicted = true;

    // Copy the state over.
    ++i;

    globals.cr->exit_simulation_time();
  }

  in_prediction = false;

  // Somehow we looped past the end of the list (servere lag), don't predict at all.
  if (i > prediction_num_data_slots) {
    return false;
  }

  return true;
}

/**
 *
 */
void Prediction::
run_simulation(int current_command, PlayerCommand *cmd, TFPlayer *local_avatar) {
  LocalTFPlayer *local_player = local_avatar->get_local_player();
  nassertv(local_player != nullptr);

  LocalTFPlayer::CommandContext *ctx = local_player->get_command_context();
  ctx->needs_processing = true;
  ctx->cmd = cmd;
  ctx->command_num = current_command;

  // Make sure simulation occurs at most once per entity per PlayerCommand.
  for (PredictedObject *p : predictables) {
    ((Entity *)p->entity)->set_simulation_tick(-1);
  }

  for (PredictedObject *p : predictables) {
    globals.cr->enter_simulation_time(cmd->tick_count, local_avatar->get_tick_base());

    bool is_local = p->entity == local_avatar;

    Entity *ent = (Entity *)p->entity;
    ent->simulate();
    ent->record_values_for_interpolation(globals.cr->get_client_time(), Entity::IVF_simulation |
					 Entity::IVF_animation | Entity::IVF_omit_update_last_networked);

    globals.cr->exit_simulation_time();
  }
}

/**
 *
 */
void Prediction::
update(int start_frame, bool valid_frame, int incoming_acked, int outgoing_cmd) {
  current_command_reference = incoming_acked;

  bool received_new_world_update = true;
  // Still starting at same frame, so make sure we don't do extra
  // prediction.
  if (previous_start_frame == start_frame) {
    received_new_world_update = false;
  }

  previous_start_frame = start_frame;

  do_update(received_new_world_update, valid_frame, incoming_acked, outgoing_cmd);
}

/**
 *
 */
void Prediction::
do_update(bool received_world_update, bool valid_frame, int incoming_acked, int outgoing_command) {
  if (!valid_frame) {
    return;
  }

  if (received_world_update) {
    restore_original_entity_state();
  }

  perform_prediction(received_world_update, globals.local_avatar, incoming_acked, outgoing_command);
}
