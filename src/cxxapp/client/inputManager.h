/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file inputManager.h
 * @author brian
 * @date 2024-08-31
 */

#ifndef INPUTMANAGER_H
#define INPUTMANAGER_H

#include "nodePath.h"
#include "simpleHashMap.h"
#include "inputDeviceManager.h"
#include "inputDevice.h"
#include "nodePathCollection.h"
#include "dataGraphTraverser.h"
#include "notifyCategoryProxy.h"
#include "inputButtons.h"

class GraphicsWindow;

NotifyCategoryDeclNoExport(input);

class Camera;

class InputManager {
public:
  enum MappingType {
    MT_unknown,
    MT_button,
    MT_axis,
  };

  class InputMapping {
  public:
    MappingType mapping_type;
    ButtonHandle button;
    InputDevice::Axis axis;

    bool get_button_value() const;
    float get_axis_value() const;
  };

  // Maintains a mapping of game-code actions to actual
  // buttons/axes on the device, so we can properly query
  // the device for the state of game-code actions.
  class InputDeviceContext {
  public:
    InputDevice *device;
    SimpleHashMap<int, InputMapping, int_hash> mappings;

    void map_button(int code, ButtonHandle button);
    void map_axis(int code, InputDevice::Axis axis);
  };

  struct InputState {
    float axis = 0.0f;
    bool button = false;
  };

public:
  InputManager();

  void initialize(GraphicsWindow *window, Camera *cam);

  virtual void init_device_mappings(InputDeviceContext *ctx);

  void init_default_keyboard_mappings(InputDeviceContext *ctx);
  void init_default_mouse_mappings(InputDeviceContext *ctx);
  void init_default_gamepad_mappings(InputDeviceContext *ctx);

  bool get_button_value(int button) const;
  float get_axis_value(int axis_type) const;

  bool was_button_pressed(int button) const;
  bool was_button_released(int button) const;
  bool is_button_down(int button) const;
  bool was_button_down(int button) const;
  float get_axis(int axis) const;
  float get_prev_axis(int axis) const;

  void update();

  void enable_mouse();
  void disable_mouse();
  void use_drive();
  void use_trackball();
  void change_mouse_interface(NodePath change_to);

  LPoint2 get_mouse_in_window() const;
  bool has_mouse_in_window() const;

private:
  typedef SimpleHashMap<InputDevice *, NodePath, pointer_hash> InputDeviceMap;
  InputDeviceMap _input_devices;

  GraphicsWindow *_win;

  typedef pvector<InputDeviceContext> DeviceContexts;
  DeviceContexts _device_contexts;

  NodePath _data_root;
  NodePathCollection _mouse_and_keyboard;
  NodePathCollection _mouse_watcher;
  NodePathCollection _kb_button_thrower;

  InputDeviceManager *_device_mgr;

  DataGraphTraverser _dgtrav;

  NodePath _trackball;
  NodePath _drive;
  NodePath _mouse2cam;
  NodePath _mouse_interface;

  InputState _prev_states[IB_COUNT];
  InputState _states[IB_COUNT];
};

#include "inputManager.I"

#endif // INPUTMANAGER_H
