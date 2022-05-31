/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkClass.h
 * @author brian
 * @date 2022-05-03
 */

#ifndef NETWORKCLASS_H
#define NETWORKCLASS_H

#include "tfbase.h"
#include "namable.h"
#include "datagram.h"
#include "datagramIterator.h"
#include "networkField.h"

class NetworkedObjectProxy;
class NetworkedObjectBase;

/**
 *
 */
class EXPCL_TF_DISTRIBUTED NetworkClass : public Namable {
public:
  typedef void MessageFunc(DatagramIterator &scan, NetworkedObjectBase *obj);
  enum MessageFlags : uint8_t {
    MF_unreliable = 1 << 0,
    MF_broadcast  = 1 << 1,
    MF_clsend     = 1 << 2,
    MF_ownsend    = 1 << 3,
    MF_ownrecv    = 1 << 4,
    MF_airecv     = 1 << 5,
    MF_event      = 1 << 6,
  };
  class MessageDef {
  public:
    std::string _name;
    MessageFunc *_func;
    uint8_t _flags;
  };

  NetworkClass(const std::string &name, size_t class_stride);

  void serialize(Datagram &dg, const unsigned char *base) const;
  void unserialize(DatagramIterator &scan, unsigned char *base) const;

  INLINE void set_id(uint16_t id);
  INLINE uint16_t get_id() const;

  INLINE size_t get_class_stride() const;

  void add_field(NetworkField *field);
  void remove_field(const std::string &name);

  void add_message(const std::string &name, MessageFunc *func, uint8_t flags);
  void remove_message(const std::string &name);

  INLINE size_t get_num_messages() const;
  INLINE const MessageDef *get_message(size_t n) const;

  INLINE size_t get_num_fields() const;
  INLINE NetworkField *get_field(size_t i) const;

  INLINE void set_linked_proxy(NetworkedObjectProxy *proxy);
  INLINE NetworkedObjectProxy *get_linked_proxy() const;

  size_t add_hash(size_t hash) const;

  void output(std::ostream &out) const;

  INLINE bool operator < (const NetworkClass &other) const;

private:
  size_t _class_stride;
  typedef pvector<NetworkField *> Fields;
  Fields _fields;

  typedef pvector<MessageDef> Messages;
  Messages _messages;

  uint16_t _id;

  // The NetworkedObjectProxy associated with this NetworkClass.
  // Analogous to the Python class linked to a DCClass.
  NetworkedObjectProxy *_linked_proxy;
};

#include "networkClass.I"

#endif // NETWORKCLASS_H
