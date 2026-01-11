#include "indexBufferCombiner.h"
#include "geomNode.h"
#include "geomVertexReader.h"

/**
 *
 */
IndexBufferCombiner::
IndexBufferCombiner(const NodePath &root, int max_indices) :
  _root(root),
  _max_indices(max_indices)
{
}

/**
 *
 */
void IndexBufferCombiner::
combine() {
  NodePathCollection geom_nodes = _root.find_all_matches("**/+GeomNode");
  if (_root.node()->is_of_type(GeomNode::get_class_type())) {
    // The root node may also be a GeomNode.
    geom_nodes.add_path(_root);
  }

  for (int i = 0; i < geom_nodes.get_num_paths(); ++i) {
    GeomNode *gn = DCAST(GeomNode, geom_nodes.get_path(i).node());

    for (int j = 0; j < gn->get_num_geoms(); ++j) {
      PT(Geom) geom = gn->modify_geom(j);
      bool geom_modified = false;

      for (int k = 0; k < geom->get_num_primitives(); ++k) {
	if (!geom->get_primitive(k)->is_indexed()) {
	  // Primitive is non-indexed so we don't have to do anything.
	  continue;
	}

	geom_modified = true;

	PT(GeomPrimitive) prim = geom->modify_primitive(k);

	if ((_writer.get_write_row() + prim->get_num_vertices()) >= _max_indices) {
	  // We are going to exceed the max indices if we add this primitive.
	  // Start with a fresh buffer.
	  make_buffer();
	}

	CPT(GeomIndexArrayData) from_indices = prim->get_vertices();
	GeomVertexReader reader(from_indices, 0);

	// Chuck all of the primitive's indices onto our big buffer,
	// and assign the primitive the section that we added its
	// indices to.
	int prim_start = _writer.get_write_row();
	while (!reader.is_at_end()) {
	  int index = reader.get_data1i();
	  _writer.add_data1i(index);
	}
	int prim_count = _writer.get_write_row() - prim_start;
	prim->set_vertices(_buffer, prim_count, prim_start);
	geom->set_primitive(k, prim);
      }

      if (geom_modified) {
	// Set the new geom if we combined any buffers.
	gn->set_geom(j, geom);
      }
    }
  }
}

/**
 *
 */
void IndexBufferCombiner::
make_buffer() {
  _buffer = new GeomIndexArrayData(GeomEnums::NT_uint32, GeomEnums::UH_static);
  _writer = GeomVertexWriter(_buffer, 0);
}
