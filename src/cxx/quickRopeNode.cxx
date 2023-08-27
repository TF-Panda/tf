/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file quickRopeNode.cxx
 * @author brian
 * @date 2023-08-27
 */

#include "quickRopeNode.h"
#include "cullTraverser.h"
#include "cullTraverserData.h"
#include "geomVertexData.h"
#include "geomVertexWriter.h"
#include "cullHandler.h"
#include "boundingSphere.h"
#include "boundingBox.h"

IMPLEMENT_CLASS(QuickRopeNode);

/**
 *
 */
class CatmullRomSpline {
public:
  void set_points(const LVecBase3 &p1, const LVecBase3 &p2, const LVecBase3 &p3, const LVecBase3 &p4);
  LVecBase3 evaluate(PN_stdfloat t) const;

public:
  LVector3 _t1, _t2, _t3, _c;
};

/**
 *
 */
void CatmullRomSpline::
set_points(const LVecBase3 &p1, const LVecBase3 &p2, const LVecBase3 &p3, const LVecBase3 &p4) {
  _t3 = 0.5f * ((-1 * p1) + (3 * p2) + (-3 * p3) + p4);
  _t2 = 0.5f * ((2 * p1) + (-5 * p2) + (4 * p3) - p4);
  _t1 = 0.5f * ((-1 * p1) + p3);
  _c = p2;
}

/**
 *
 */
LVecBase3 CatmullRomSpline::
evaluate(PN_stdfloat t) const {
  return _c + (t * _t1) + (t * t * _t2) + (t * t * t * _t3);
}

/**
 *
 */
QuickRopeNode::
QuickRopeNode(const std::string &name, int num_points, PN_stdfloat thickness, int subdiv) :
  PandaNode(name),
  _thickness(thickness),
  _subdiv(std::max(1, subdiv))
{
  _points.resize(num_points);
  for (int i = 0; i < num_points; ++i) {
    _points[i].set(0, 0, 0);
  }

  int num_interp_points = _subdiv * (num_points - 1) + 1;

  _tristrips = new GeomTristrips(GeomEnums::UH_static);
  _tristrips->add_consecutive_vertices(0, num_interp_points * 2);
  _tristrips->close_primitive();

  _interp_points.resize(num_interp_points);
  for (int i = 0; i < num_interp_points; ++i) {
    _interp_points[i].set(0, 0, 0);
  }

  set_renderable();
}

/**
 *
 */
void QuickRopeNode::
recompute_interpolated_points() {
  int interp_index = 0;
  int num_points = (int)_points.size();
  int prev = 0;
  for (int i = 0; i < (int)_points.size(); ++i) {
    if (i < (num_points - 1)) {
      int next = i + 1;
      int next_next = i + 2;
      if (next >= num_points) {
        next = next_next = (num_points - 1);
      } else if (next_next >= num_points) {
        next_next = (num_points - 1);
      }

      CatmullRomSpline spline;
      spline.set_points(_points[prev], _points[i], _points[next], _points[next_next]);

      for (int j = 0; j < _subdiv; ++j) {
        PN_stdfloat t = (PN_stdfloat)j / (PN_stdfloat)_subdiv;
        _interp_points[interp_index++] = spline.evaluate(t);
      }

      prev = i;

    } else {
      _interp_points[interp_index++] = _points[i];
    }
  }
}

/**
 * Returns a newly-allocated BoundingVolume that represents the internal
 * contents of the node.  Should be overridden by PandaNode classes that
 * contain something internally.
 */
void QuickRopeNode::
compute_internal_bounds(CPT(BoundingVolume) &internal_bounds,
                        int &internal_vertices,
                        int pipeline_stage,
                        Thread *current_thread) const {
  PT(GeometricBoundingVolume) gbv;
  if (_points.empty()) {
    gbv = new BoundingBox;
  } else {
    LPoint3 mins = _points[0] - LVector3(_thickness);
    LPoint3 maxs = _points[0] + LVector3(_thickness);
    for (int i = 1; i < (int)_points.size(); ++i) {
      mins = mins.fmin(_points[i] - LVector3(_thickness));
      maxs = maxs.fmax(_points[i] + LVector3(_thickness));
    }
    gbv = new BoundingBox(mins, maxs);
  }

  internal_bounds = gbv;
  internal_vertices = _points.size() * 2;
}

/**
 *
 */
void QuickRopeNode::
add_for_draw(CullTraverser *trav, CullTraverserData &data) {
  Camera *camera = trav->get_scene()->get_camera_node();
  CamData *cam_data;
  _lock.acquire();
  auto it = _cam_data.find(camera);
  if (it != _cam_data.end()) {
    cam_data = it->second;
  }
  else {
    cam_data = new CamData;
    _cam_data.insert({ camera, cam_data });
  }
  _lock.release();

  int num_points = (int)_interp_points.size();
  int num_verts = num_points * 2;

  if (cam_data->_geom == nullptr) {
    for (int i = 0; i < 2; ++i) {
      PT(GeomVertexData) vdata = new GeomVertexData("rope", GeomVertexFormat::get_v3(), GeomEnums::UH_dynamic);
      vdata->unclean_set_num_rows(num_verts);
      cam_data->_vertex_data[i] = vdata;
    }
    cam_data->_geom = new Geom(cam_data->_vertex_data[0]);
    cam_data->_geom->add_primitive(_tristrips);
  }

  const TransformState *net_transform = data.get_net_transform(trav);
  const TransformState *camera_transform = trav->get_camera_transform();

  Thread *current_thread = Thread::get_current_thread();

  CPT(TransformState) rel_transform =
    net_transform->invert_compose(camera_transform);
  LVector3 camera_vec = rel_transform->get_pos();

  GeomVertexData *vdata = cam_data->_vertex_data[cam_data->_last_frame];
  GeomVertexWriter vertex(vdata, InternalName::get_vertex());
  for (int i = 0; i < num_points; ++i) {
    // Calculate the tangent vector.
    LVector3 tangent;
    if (i == 0) {
      tangent = _interp_points[i + 1] - _interp_points[i];
    } else if (i == (num_points - 1)) {
      tangent = _interp_points[i] - _interp_points[i - 1];
    } else {
      tangent = _interp_points[i + 1] - _interp_points[i - 1];
    }
    if (IS_NEARLY_ZERO(tangent.length_squared())) {
      tangent.set(0, 0, 1);
    }

    LVector3 to_seg = _interp_points[i] - camera_vec;

    LVector3 norm = cross(tangent, to_seg);
    norm.normalize();

    vertex.set_data3(_interp_points[i] + norm * _thickness);
    vertex.set_data3(_interp_points[i] - norm * _thickness);
  }

  cam_data->_geom->set_vertex_data(vdata);
  cam_data->_last_frame ^= 1;

  CullableObject cobj(cam_data->_geom, data._state, data.get_internal_transform(trav), current_thread);
  trav->get_cull_handler()->record_object(&cobj, trav);
}
