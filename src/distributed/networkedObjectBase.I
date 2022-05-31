/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectBase.I
 * @author brian
 * @date 2022-05-03
 */

/**
 *
 */
INLINE NetworkedObjectBase::
NetworkedObjectBase() :
  _network_id(0u),
  _zone_id(0u),
  _life_state(LS_fresh)
{
}

/**
 *
 */
INLINE void NetworkedObjectBase::
set_do_id(doid_t do_id) {
  // DoId can't change after it has been generated.
  nassertv(_life_state == LS_fresh);
  _network_id = do_id;
}

/**
 * Returns the unique network identifier of this object.
 */
INLINE doid_t NetworkedObjectBase::
get_network_id() const {
  return _network_id;
}

/**
 * Alias for get_network_id().
 */
INLINE doid_t NetworkedObjectBase::
get_do_id() const {
  return _network_id;
}

/**
 *
 */
INLINE void NetworkedObjectBase::
set_zone_id(zoneid_t zone_id) {
  _zone_id = zone_id;
}

/**
 * Returns the network location of the object.  This can be thought of as the
 * network-space "room" that the object is in.
 */
INLINE zoneid_t NetworkedObjectBase::
get_zone_id() const {
  return _zone_id;
}

/**
 *
 */
INLINE NetworkedObjectBase::LifeState NetworkedObjectBase::
get_do_state() const {
  return _life_state;
}

/**
 *
 */
INLINE bool NetworkedObjectBase::
is_do_fresh() const {
  return _life_state == LS_fresh;
}

/**
 *
 */
INLINE bool NetworkedObjectBase::
is_do_generated() const {
  return _life_state >= LS_generated;
}

/**
 *
 */
INLINE bool NetworkedObjectBase::
is_do_alive() const {
  return _life_state == LS_alive;
}

/**
 *
 */
INLINE bool NetworkedObjectBase::
is_do_disabled() const {
  return _life_state <= LS_disabled;
}

/**
 *
 */
INLINE bool NetworkedObjectBase::
is_do_deleted() const {
  return _life_state == LS_deleted;
}
