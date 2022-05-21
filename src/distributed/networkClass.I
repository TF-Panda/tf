/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkClass.I
 * @author brian
 * @date 2022-05-03
 */

/**
 *
 */
INLINE void NetworkClass::
set_id(uint16_t id) {
  _id = id;
}

/**
 *
 */
INLINE uint16_t NetworkClass::
get_id() const {
  return _id;
}

/**
 *
 */
INLINE size_t NetworkClass::
get_class_stride() const {
  return _class_stride;
}

/**
 *
 */
INLINE size_t NetworkClass::
get_num_messages() const {
  return _messages.size();
}

/**
 *
 */
INLINE const NetworkClass::MessageDef *NetworkClass::
get_message(size_t n) const {
  if (n >= _messages.size()) {
    return nullptr;
  }
  return &_messages[n];
}

/**
 *
 */
INLINE size_t NetworkClass::
get_num_fields() const {
  return _fields.size();
}

/**
 *
 */
INLINE NetworkField *NetworkClass::
get_field(size_t n) const {
  if (n >= _fields.size()) {
    return nullptr;
  }
  return _fields[n];
}

/**
 *
 */
INLINE void NetworkClass::
set_linked_proxy(NetworkedObjectProxy *proxy) {
  _linked_proxy = proxy;
}

/**
 *
 */
INLINE NetworkedObjectProxy *NetworkClass::
get_linked_proxy() const {
  return _linked_proxy;
}

/**
 *
 */
INLINE bool NetworkClass::
operator < (const NetworkClass &other) const {
  return _id < other._id;
}
