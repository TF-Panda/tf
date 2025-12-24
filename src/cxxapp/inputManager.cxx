/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file inputManager.cxx
 * @author brian
 * @date 2024-08-31
 */

#include "inputManager.h"
#include "graphicsWindow.h"
#include "mouseAndKeyboard.h"
#include "buttonThrower.h"
#include "modifierButtons.h"
#include "keyboardButton.h"
#include "buttonHandle.h"
#include "mouseWatcher.h"
#include "globals.h"
#include "mouseButton.h"

NotifyCategoryDef(input, "");

/**
 *
 */
void InputManager::InputDeviceContext::
map_button(int code, ButtonHandle button) {
  InputMapping map;
  map.button = button;
  map.mapping_type = MT_button;
  mappings[code] = std::move(map);
}

/**
 *
 */
void InputManager::InputDeviceContext::
map_axis(int code, InputDevice::Axis axis) {
  InputMapping map;
  map.axis = axis;
  map.mapping_type = MT_axis;
  mappings[code] = std::move(map);
}

/**
 *
 */
InputManager::
InputManager() :
  _device_mgr(InputDeviceManager::get_global_ptr()),
  _data_root("dataroot")
{
}

/**
 *
 */
void InputManager::
initialize(GraphicsWindow *window) {
  _device_mgr->update();

  for (int i = 0; i < window->get_num_input_devices(); ++i) {
    InputDevice *device = window->get_input_device(i);

    NodePath mak = _data_root.attach_new_node(
      new MouseAndKeyboard(window, i, window->get_input_device_name(i)));
    _mouse_and_keyboard.add_path(mak);

    // Watch the mouse.
    std::ostringstream mwss;
    mwss << "watcher-" << i;
    PT(MouseWatcher) mw = new MouseWatcher(mwss.str());
    if (window->get_side_by_side_stereo()) {
      mw->set_display_region(window->get_overlay_display_region());
    }

    // Watch the mouse.
    ModifierButtons mmods = mw->get_modifier_buttons();
    mmods.add_button(KeyboardButton::shift());
    mmods.add_button(KeyboardButton::control());
    mmods.add_button(KeyboardButton::alt());
    mmods.add_button(KeyboardButton::meta());
    mw->set_modifier_buttons(mmods);
    NodePath mwnp = mak.attach_new_node(mw);
    _mouse_watcher.add_path(mwnp);

    // Watch for keyboard buttons.
    std::ostringstream btss;
    btss << "buttons-" << i;
    PT(ButtonThrower) bt = new ButtonThrower(btss.str());
    if (i != 0) {
      std::ostringstream press;
      press << "mousedev" << i << "-";
      bt->set_prefix(press.str());
    }
    ModifierButtons mods;
    mods.add_button(KeyboardButton::shift());
    mods.add_button(KeyboardButton::control());
    mods.add_button(KeyboardButton::alt());
    mods.add_button(KeyboardButton::meta());
    bt->set_modifier_buttons(mods);
    NodePath btnp = mak.attach_new_node(bt);
    _kb_button_thrower.add_path(btnp);

    input_cat.info()
      << "Detected input device " << window->get_input_device_name(i) << "\n";
    input_cat.info()
      << "Device class: " << device->get_device_class() << "\n";
    InputDeviceContext ctx;
    ctx.device = window->get_input_device(i);
    init_device_mappings(&ctx);
    _device_contexts.push_back(ctx);
  }

  // Determine which input devices are connected for game input.
  InputDeviceSet devices = _device_mgr->get_devices();
  size_t device_count = devices.size();
  for (size_t i = 0; i < device_count; ++i) {
    InputDevice *device = devices[i];
    input_cat.info()
      << "Detected input device " << device->get_name() << "\n";
    input_cat.info()
      << "Device class: " << device->get_device_class() << "\n";
    InputDeviceContext ctx;
    ctx.device = device;
    init_device_mappings(&ctx);
    _device_contexts.push_back(ctx);
  }
}

/**
 *
 */
void InputManager::
update() {
  _device_mgr->update();
  for (size_t i = 0; i < _device_contexts.size(); ++i) {
    _device_contexts[i].device->poll();
  }
  _dgtrav.traverse(_data_root.node());
}

/**
 *
 */
void InputManager::
init_default_mouse_mappings(InputDeviceContext *ctx) {
  input_cat.info()
    << "Init mouse mappings for " << ctx->device->get_name() << "\n";
  ctx->map_button(IC_primary_attack, MouseButton::one());
  ctx->map_button(IC_secondary_attack, MouseButton::three());
}

/**
 *
 */
void InputManager::
init_default_keyboard_mappings(InputDeviceContext *ctx) {
  input_cat.info()
    << "Init keyboard mappings for " << ctx->device->get_name() << "\n";
  ctx->map_button(IC_move_forward, KeyboardButton::ascii_key('w'));
  ctx->map_button(IC_move_back, KeyboardButton::ascii_key('s'));
  ctx->map_button(IC_move_left, KeyboardButton::ascii_key('a'));
  ctx->map_button(IC_move_right, KeyboardButton::ascii_key('d'));
  ctx->map_button(IC_jump, KeyboardButton::space());
  ctx->map_button(IC_duck, KeyboardButton::control());
  ctx->map_button(IC_interact, KeyboardButton::ascii_key('e'));
  ctx->map_button(IC_reload, KeyboardButton::ascii_key('r'));
  ctx->map_button(IC_sprint, KeyboardButton::shift());
  ctx->map_button(IC_walk, KeyboardButton::alt());
  ctx->map_button(IC_pause, KeyboardButton::escape());
}

/**
 *
 */
void InputManager::
init_default_gamepad_mappings(InputDeviceContext *ctx) {

}

/**
 *
 */
void InputManager::
init_device_mappings(InputDeviceContext *ctx) {
  switch (ctx->device->get_device_class()) {
  case InputDevice::DeviceClass::virtual_device:
    {
      if (ctx->device->has_keyboard()) {
        init_default_keyboard_mappings(ctx);
      }
      if (ctx->device->has_pointer()) {
        init_default_mouse_mappings(ctx);
      }
      break;
    }
  case InputDevice::DeviceClass::KEYBOARD:
    init_default_keyboard_mappings(ctx);
    break;
  case InputDevice::DeviceClass::MOUSE:
    init_default_mouse_mappings(ctx);
    break;
  case InputDevice::DeviceClass::GAMEPAD:
    init_default_gamepad_mappings(ctx);
    break;
  }

  std::cout << "num buttons " << ctx->device->get_num_buttons() << "\n";
  for (int i = 0; i < ctx->device->get_num_buttons(); ++i) {
    input_cat.info()
      << i << ": " << ctx->device->get_button_map(i) << "\n";
  }
}

/**
 *
 */
bool InputManager::
get_button_value(int button) const {
  for (size_t i = 0; i < _device_contexts.size(); ++i) {
    const InputDeviceContext &ctx = _device_contexts[i];
    int ibutton = ctx.mappings.find(button);
    if (ibutton != -1) {
      const InputMapping &map = ctx.mappings.get_data(ibutton);
      if (map.mapping_type != MT_button) {
        continue;
      }
      if (i < _mouse_watcher.size()) {
        // Keyboard/mouse pair from the window get button events through the MouseWatcher,
        // while other devices go through the InputDevice.
        MouseWatcher *mw = DCAST(MouseWatcher, _mouse_watcher.get_path(i).node());
        if (mw->is_button_down(map.button)) {
          return true;
        }
      } else {
        InputDevice::ButtonState state = ctx.device->find_button(map.button);
        if (state.is_known() && state.is_pressed()) {
          return true;
        }
      }
    }
  }

  return false;
}

/**
 *
 */
float InputManager::
get_axis_value(int axis) const {
  float value = 0.0f;

  for (const InputDeviceContext &ctx : _device_contexts) {
    int iaxis = ctx.mappings.find(axis);
    if (iaxis != -1) {
      const InputMapping &map = ctx.mappings.get_data(iaxis);
      if (map.mapping_type != MT_axis) {
        continue;
      }
      InputDevice::AxisState state = ctx.device->find_axis(map.axis);
      if (state.known && state.value != 0.0) {
        value += (float)state.value;
      }
    }
  }

  return std::max(0.0f, std::min(1.0f, value));
}
