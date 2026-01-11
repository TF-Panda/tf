#ifndef PREDICTION_H
#define PREDICTION_H

#include "../networkField.h"
#include "../networkClass.h"
#include "lvecBase2.h"
#include "referenceCount.h"
#include "luse.h"
#include "pointerTo.h"
#include <type_traits>

struct PredictedObject;

/**
 *
 */
struct PredictionCopy {
  enum DiffType {
    DT_differs,
    DT_identical,
    DT_within_tolerance,
  };
  enum CopyMode {
    CM_everything,
    CM_non_networked_only,
    CM_networked_only,
  };
  bool error_check;
  bool perform_copy;
  bool report_errors;
  int error_count;
  PTA_uchar dest_buf, src_buf;
  void *ent;
  PredictedObject *obj;
  int cmd_num;
  int current_command_reference;
  int dest_slot;
  CopyMode mode;

  PredictionCopy(CopyMode mode, PredictedObject *obj, PTA_uchar dest, PTA_uchar src, bool count_errors = false,
		 bool report_errors = false, bool perform_copy = true);
  int transfer_data(int current_command_reference = -1, int dest_slot = -1);
};

/**
 *
 */
struct PredictionFieldBase : public ReferenceCount {
  size_t offset = 0;
  size_t stride = 0;
  bool networked = true;
  bool no_error_check = false;
  bool is_private = false;
  float tolerance = 0.0f;
  std::string name;

  virtual size_t get_stride() const = 0;
  virtual PredictionCopy::DiffType transfer(PredictionCopy *ctx) const = 0;
};

/**
 *
 */
template<class Type>
struct PredictionFieldTempl : public PredictionFieldBase {
  typedef Type (*GetValueFn)(void *entity);
  typedef void (*SetValueFn)(Type value, void *entity);
  Type *data_ptr = nullptr;
  GetValueFn getter = nullptr;
  SetValueFn setter = nullptr;

  virtual PredictionCopy::DiffType transfer(PredictionCopy *ctx) const override;
  virtual size_t get_stride() const override;
  inline Type get_value(CPTA_uchar buf, void *ent) const;
  inline void set_value(Type value, PTA_uchar buf, void *ent) const;
  inline PredictionCopy::DiffType compare(Type src_val, Type dst_val) const;
  inline void report_error(int cmd, const Type &predicted, const Type &received) const;
};

/**
 *
 */
template<class Type>
PredictionCopy::DiffType PredictionFieldTempl<Type>::
transfer(PredictionCopy *ctx) const {
  PredictionCopy::DiffType diff = PredictionCopy::DT_differs;

  Type src_value = get_value(ctx->src_buf, ctx->ent);
  Type dst_value = get_value(ctx->dest_buf, ctx->ent);

  if (ctx->error_check) {
    diff = compare(src_value, dst_value);
  }

  if (ctx->perform_copy && diff != PredictionCopy::DT_identical) {
    set_value(src_value, ctx->dest_buf, ctx->ent);
  }

  if (ctx->error_check && diff == PredictionCopy::DT_differs) {
    if (ctx->report_errors) {
      report_error(ctx->cmd_num, src_value, dst_value);
    }
    ++ctx->error_count;
  }

  return diff;
}

/**
 *
 */
template<class Type>
size_t PredictionFieldTempl<Type>::
get_stride() const {
  return sizeof(Type);
}

/**
 *
 */
template<class Type>
inline Type PredictionFieldTempl<Type>::
get_value(CPTA_uchar buf, void *ent) const {
  if (buf.is_null()) {
    // Fetch the value off the entity.
    if (getter != nullptr) {
      // Value returned through a getter on the entity.
      return (*getter)(ent);
    } else {
      // We have the data pointer directly.
      return *data_ptr;
    }
  } else {
    // Grab the data from the history buffer.
    return *(Type *)(buf.p() + offset);
  }
}

/**
 *
 */
template<class Type>
inline void PredictionFieldTempl<Type>::
set_value(Type value, PTA_uchar buf, void *ent) const {
  if (buf.is_null()) {
    // Set the value on the entity.
    if (setter != nullptr) {
      (*setter)(value, ent);
    } else {
      *data_ptr = value;
    }
  } else {
    // Write to the prediction buffer.
    *(Type *)(buf.p() + offset) = value;
  }
}

/**
 *
 */
template<class Type>
inline PredictionCopy::DiffType PredictionFieldTempl<Type>::
compare(Type src_val, Type dst_val) const {
  if constexpr (std::is_floating_point_v<Type>) {

    if (src_val == dst_val) {
      return PredictionCopy::DT_identical;

    } else if (tolerance > 0.0f && cabs(dst_val - src_val) <= tolerance) {
      return PredictionCopy::DT_within_tolerance;

    } else {
      return PredictionCopy::DT_differs;
    }

  } else if constexpr (std::is_base_of_v<LVecBase2f, Type> ||
		       std::is_base_of_v<LVecBase3f, Type> ||
		       std::is_base_of_v<LVecBase4f, Type>) {

    PredictionCopy::DiffType diff = PredictionCopy::DT_identical;
    bool differs = (src_val != dst_val);
    if (differs && tolerance > 0.0f) {
      Type delta = dst_val - src_val;
      diff = PredictionCopy::DT_within_tolerance;
      for (int i = 0; i < Type::num_components; ++i) {
	if (cabs(delta[i]) > tolerance) {
	  diff = PredictionCopy::DT_differs;
	  break;
	}
      }
    } else if (differs) {
      diff = PredictionCopy::DT_differs;
    }

    return diff;

  } else {
    if (src_val != dst_val) {
      return PredictionCopy::DT_differs;
    } else {
      return PredictionCopy::DT_identical;
    }
  }
}

/**
 *
 */
template<class Type>
void PredictionFieldTempl<Type>::
report_error(int cmd, const Type &predicted, const Type &received) const {
  if constexpr (std::is_floating_point_v<Type> ||
		std::is_base_of_v<LVecBase2f, Type> ||
		std::is_base_of_v<LVecBase3f, Type> ||
		std::is_base_of_v<LVecBase4f, Type>) {
    // Report delta for floats/vecs.
    Type delta = received - predicted;
    std::cerr << "PREDICTION: " << name << " differs (command "
	      << cmd << "): pred " << predicted << ", net "
	      << received << ", delta " << delta << "\n";
  } else {
    // Report the two values.
    std::cerr << "PREDICTION: " << name << " differs (command "
	      << cmd << "): pred " << predicted << ", net "
	      << received << "\n";
  }
}

static constexpr int prediction_num_data_slots = 90;

/**
 *
 */
struct PredictedObject : public ReferenceCount {
  typedef pvector<PT(PredictionFieldBase)> PredFields;
  PredFields fields;

  PTA_uchar data_slots[prediction_num_data_slots];
  PTA_uchar original_data;
  int intermediate_data_count = 0;
  size_t encoded_size = 0;
  void *entity = nullptr;

  void calc_sizes();
  int save_data(int slot, PredictionCopy::CopyMode mode);
  int restore_data(int slot, PredictionCopy::CopyMode mode);
  PTA_uchar alloc_slot(int slot);
  CPTA_uchar get_slot(int slot) const;
  void shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run);
  void pre_entity_packet_received(int commands_acked);
  void post_entity_packet_received();
  bool post_networked_data_received(int commands_acked, int curr_reference);
};

class TFPlayer;
struct PlayerCommand;

/**
 *
 */
struct Prediction {
  bool in_prediction = false;
  bool first_time_predicted = false;
  int incoming_packet_number = 0;
  int previous_start_frame = -1;
  int num_commands_predicted = 0;
  int num_server_commands_acknowledged = 0;
  int current_command_reference = 0;
  bool previous_ack_had_errors = false;
  int final_predicted_tick = 0;
  // For checking for a prediction error in local avatar position.
  PredictionFieldTempl<LVecBase3f> *local_av_pos_field = nullptr;

  typedef pvector<PT(PredictedObject)> Predictables;
  Predictables predictables;

  inline bool has_been_predicted() const;
  inline bool is_first_time_predicted() const;
  inline void add_predictable(PredictedObject *obj);
  inline void remove_predictable(PredictedObject *obj);

  void pre_entity_packet_received(int commands_acked, int current_world_update_packet);
  void post_entity_packet_received();
  void on_receive_uncompressed_packet();
  void post_network_data_received(int commands_acked);
  void restore_original_entity_state();
  void restore_entity_to_predicted_frame(int frame);
  void shift_intermediate_data_forward(int slots_to_remove, int num_cmds_run);
  void store_prediction_results(int slot);
  int compute_first_command_to_execute(bool received_world_update, int incoming_acked, int outgoing_command);
  bool perform_prediction(bool received_world_update, TFPlayer *local_avater, int incoming_acked, int outgoing_command);
  void run_simulation(int current_command, PlayerCommand *cmd, TFPlayer *local_avatar);
  void update(int start_frame, bool valid_frame, int incoming_acked, int outgoing_cmd);
  void do_update(bool received_world_update, bool valid_frame, int incoming_acked, int outgoing_cmd);
  void check_error(int commands_acked);

  inline static Prediction *ptr();

private:
  static Prediction *_global_ptr;
};

/**
 *
 */
inline bool Prediction::
has_been_predicted() const {
  return in_prediction && !first_time_predicted;
}

/**
 *
 */
inline bool Prediction::
is_first_time_predicted() const {
  return in_prediction && first_time_predicted;
}

/**
 *
 */
inline void Prediction::
add_predictable(PredictedObject *obj) {
  nassertv(std::find(predictables.begin(), predictables.end(), obj) == predictables.end());
  predictables.push_back(obj);
}

/**
 *
 */
inline void Prediction::
remove_predictable(PredictedObject *obj) {
  Predictables::const_iterator it = std::find(predictables.begin(), predictables.end(), obj);
  if (it != predictables.end()) {
    predictables.erase(it);
  }
}

/**
 *
 */
inline Prediction *Prediction::
ptr() {
  if (_global_ptr == nullptr) {
    _global_ptr = new Prediction;
  }
  return _global_ptr;
}

#endif // PREDICTION_H
