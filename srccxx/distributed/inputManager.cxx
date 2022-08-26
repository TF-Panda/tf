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
 * @date 2022-08-25
 */

#include "inputManager.h"
#include "inputDeviceManager.h"
#include "graphicsEngine.h"
#include "mouseAndKeyboard.h"
#include "mouseWatcher.h"
#include "string_utils.h"
#include "modifierButtons.h"
#include "buttonThrower.h"
#include "keyboardButton.h"

/**
 *
 */
InputManager::
InputManager(GraphicsEngine *engine, GraphicsWindow *window) :
  _engine(engine),
  _window(window),
  _data_root("dataRoot"),
  _device_mgr(InputDeviceManager::get_global_ptr())
{
}

/**
 *
 */
void InputManager::
initialize() {
  _engine->open_windows();
  _device_mgr->update();

  // Initialize the data graph.

  for (int i = 0; i < _window->get_num_input_devices(); ++i) {
    NodePath mak = _data_root.attach_new_node(
      new MouseAndKeyboard(_window, i, _window->get_input_device_name(i)));
    _mouse_and_keyboard.add_path(mak);

    // Watch the mouse.
    PT(MouseWatcher) mw = new MouseWatcher("mouseWatcher" + format_string(i));

    if (_window->get_side_by_side_stereo()) {
      mw->set_display_region(_window->get_overlay_display_region());
    }

    ModifierButtons mmods = mw->get_modifier_buttons();
    mmods.add_button(KeyboardButton::shift());
    mmods.add_button(KeyboardButton::control());
    mmods.add_button(KeyboardButton::alt());
    mmods.add_button(KeyboardButton::meta());
    mw->set_modifier_buttons(mmods);
    NodePath mwnp = mak.attach_new_node(mw);
    _mouse_watcher.add_path(mwnp);

    // Watch for keyboard buttons.
  }
}
