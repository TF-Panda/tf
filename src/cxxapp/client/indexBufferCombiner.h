#ifndef INDEXBUFFERCOMBINER_H
#define INDEXBUFFERCOMBINER_H

#include "nodePath.h"
#include "geomIndexArrayData.h"
#include "geomVertexWriter.h"

/**
 * Small helper class to combine the index buffers from all GeomPrimitives in
 * a scene graph to as few larger index buffer as possible.
 *
 * Usage is simply to create an IndexBufferCombiner instance with the root node
 * of the scene/model, then call combine().  It operates in place.
 */
class IndexBufferCombiner {
public:
  IndexBufferCombiner(const NodePath &root, int max_indices = 65535);

  void combine();

private:
  void make_buffer();

private:
  int _max_indices;
  NodePath _root;
  GeomVertexWriter _writer;
  PT(GeomIndexArrayData) _buffer;
};


#endif // INDEXBUFFERCOMBINER_H
