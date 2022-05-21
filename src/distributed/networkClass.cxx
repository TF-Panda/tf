/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkClass.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "networkClass.h"
#include "stl_compares.h"
#include "indent.h"
#include "networkedObjectBase.h"

/**
 *
 */
NetworkClass::
NetworkClass(const std::string &name, size_t class_stride) :
  Namable(name),
  _class_stride(class_stride),
  _id(0u)
{
}

/**
 * Adds the indicated field to the NetworkClass.  If an existing field has the
 * same name, it will be replaced by the new field.
 */
void NetworkClass::
add_field(NetworkField *field) {
  Fields::iterator it = std::find_if(_fields.begin(), _fields.end(),
    [field](const NetworkField *other) {
      return field->get_name() == other->get_name();
    }
  );

  if (it != _fields.end()) {
    // Replace field with same name.
    (*it) = field;
  } else {
    // Append new field.
    _fields.push_back(field);
  }
}

/**
 * Removes the field with the indicated name from the NetworkClass.
 */
void NetworkClass::
remove_field(const std::string &name) {
  Fields::const_iterator it = std::find_if(_fields.begin(), _fields.end(),
    [name](const NetworkField *field) {
      return field->get_name() == name;
    }
  );
  if (it != _fields.end()) {
    _fields.erase(it);
  }
}

/**
 * Adds a new network message handler to the network class.
 */
void NetworkClass::
add_message(const std::string &name, MessageFunc *func, uint8_t flags) {
  Messages::iterator it = std::find_if(_messages.begin(), _messages.end(),
    [name](const MessageDef &msg) {
      return msg._name == name;
    }
  );

  if (it != _messages.end()) {
    // Replace existing message.
    MessageDef &msg = (*it);
    msg._func = func;
    msg._flags = flags;

  } else {
    // New message def.
    MessageDef msg;
    msg._name = name;
    msg._func = func;
    msg._flags = flags;
    _messages.push_back(std::move(msg));
  }
}

/**
 *
 */
void NetworkClass::
remove_message(const std::string &name) {
  Messages::const_iterator it = std::find_if(_messages.begin(), _messages.end(),
    [name](const MessageDef &msg) {
      return msg._name == name;
    }
  );
  if (it != _messages.end()) {
    _messages.erase(it);
  }
}

/**
 *
 */
void NetworkClass::
serialize(Datagram &dg, const unsigned char *base) const {
  for (const NetworkField *field : _fields) {
    field->serialize(dg, base);
  }
}

/**
 *
 */
void NetworkClass::
unserialize(DatagramIterator &scan, unsigned char *base) const {
  for (const NetworkField *field : _fields) {
    field->unserialize(scan, base);
  }
}

/**
 *
 */
size_t NetworkClass::
add_hash(size_t hash) const {
  hash = string_hash::add_hash(hash, get_name());
  hash = int_hash::add_hash(hash, (int)_fields.size());
  for (const NetworkField *field : _fields) {
    hash = field->add_hash(hash);
  }
  return hash;
}

/**
 *
 */
void NetworkClass::
output(std::ostream &out) const {
  out << "Net class " << get_name() << "\n";
  if (_linked_proxy == nullptr) {
    indent(out, 2) << "No linked proxy\n";
  } else {
    indent(out, 2) << "Proxy object TypeHandle: " << _linked_proxy->get_object_type() << "\n";
  }
  for (NetworkField *field : _fields) {
    field->output(out, 2);
  }
  for (const MessageDef &msg : _messages) {
    indent(out, 2) << "Message " << msg._name << "\n";
    indent(out, 4) << "Flags: " << msg._flags << "\n";
    indent(out, 4) << "Func: " << msg._func << "\n";
  }
}
