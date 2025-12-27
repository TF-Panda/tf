#ifndef NETWORKOBJECT_H
#define NETWORKOBJECT_H

#include "referenceCount.h"

class NetworkClass;

typedef uint32_t DO_ID;

/**
 * Base class for a networked object.  This is like the DistributedObject in DIRECT.
 */
class NetworkObject : virtual public ReferenceCount {
public:
  virtual NetworkClass *get_network_class() const=0;

  inline void set_do_id(DO_ID do_id);
  inline DO_ID get_do_id() const;

private:
  DO_ID _do_id;
};

/**
 * 
 */
inline void NetworkObject::
set_do_id(DO_ID do_id) {
  _do_id = do_id;
}

/**
 * Returns the shared network identifier for this object.  The distributed object ID.
 */
inline DO_ID NetworkObject::
get_do_id() const {
  return _do_id;
}

#endif // NETWORKOBJECT_H
