#ifndef GAMEMANAGER_H
#define GAMEMANAGER_H

#include "networkObject.h"

/**
 *
 */
class GameManager : public NetworkObject {
public:
  virtual void generate() override;

  inline void set_level_name(const std::string &name);
  inline const std::string &get_level_name() const;

private:
  static void s_recv_join_game(void *obj, void *args);
  static void s_recv_join_game_resp(void *obj, void *args);

private:
  std::string _game_name;
  std::string _level_name;

public:
  static NetworkObject *make_GameManager() {
    return new GameManager;
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
 *
 */
inline void GameManager::
set_level_name(const std::string &name) {
  _level_name = name;
}

/**
 *
 */
inline const std::string &GameManager::
get_level_name() const {
  return _level_name;
}

#endif // GAMEMANAGER_H
