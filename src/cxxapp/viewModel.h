#ifndef VIEWMODEL_H
#define VIEWMODEL_H

#include "entity.h"

/**
 *
 */
class ViewModel : public Entity {
public:
  ViewModel();

  inline int get_player_id() const;

private:
  int _player_id;

  // Net class stuff
public:
  inline static NetworkObject *make_ViewModel() {
    return new ViewModel;
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

/**
 * Returns the doID of the player that owns the viewmodel.
 */
inline int ViewModel::
get_player_id() const {
  return _player_id;
}

#endif // VIEWMODEL_H
