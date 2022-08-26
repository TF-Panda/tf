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
 * @date 2022-08-25
 */

#ifndef INPUTMANAGER_H
#define INPUTMANAGER_H

#include "tfbase.h"
#include "dataGraphTraverser.h"
#include "nodePath.h"
#include "nodePathCollection.h"
#include "pvector.h"
#include "pmap.h"
#include "buttonHandle.h"
#include "inputDevice.h"

class GraphicsEngine;
class GraphicsWindow;
class InputDeviceManager;

/**
 *
 */
class EXPCL_TF_DISTRIBUTED InputManager {
public:
  // The different ways we can accept input.
  enum MappingType {
    MT_unknown,
    MT_button,
    MT_axis,
  };

  /**
   *
   */
  class InputMapping {
  public:
    MappingType _mapping_type;
    union {
      ButtonHandle _button;
      InputDevice::Axis _axis;
    };
    INLINE bool get_button_value() const;
    INLINE float get_axis_value() const;
  };

  /**
   *
   */
  class InputDeviceMappings {
  public:
    InputDevice *_device;
    pflat_hash_map<int, InputMapping, int_hash> _mappings;
  };

  InputManager(GraphicsEngine *engine, GraphicsWindow *window);

  void initialize();
  void shutdown();

  void update();

private:
  pvector<InputDeviceMappings> _device_mappings;

  DataGraphTraverser _dg_trav;
  NodePath _data_root;
  NodePathCollection _mouse_and_keyboard;
  NodePathCollection _mouse_watcher;
  NodePathCollection _kb_button_thrower;
  pflat_hash_map<InputDevice *, NodePath, pointer_hash> _input_devices;
  NodePathCollection _device_button_throwers;

  GraphicsEngine *_engine;
  GraphicsWindow *_window;
  InputDeviceManager *_device_mgr;
};

#include "inputManager.I"

#endif // INPUTMANAGER_H
