/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file quickRopeNode.h
 * @author brian
 * @date 2023-08-27
 */

#ifndef QUICKROPENODE_H
#define QUICKROPENODE_H

#include "tfbase.h"
#include "pandaNode.h"
#include "geomTristrips.h"
#include "cycleData.h"
#include "cycleDataReader.h"
#include "cycleDataWriter.h"
#include "pvector.h"
#include "pointerTo.h"
#include "weakPointerTo.h"
#include "camera.h"
#include "luse.h"
#include "lightMutex.h"
#include "pmap.h"

/**
 * Simplied version of RopeNode that tries to be as efficient as possible.
 * Renders a set of points as one continuous, billboarded, triangle strip, with
 * a specified thickness.  The points can also be subdivded a user-configured
 * amount for smoother rendering.  The subdivision is done using a Catmull-Rom
 * spline algorithm, rather than the slower NurbsCurveEvaluator used in RopeNode.
 */
class EXPCL_TF_CXX QuickRopeNode : public PandaNode {
  DECLARE_CLASS(QuickRopeNode, PandaNode);

PUBLISHED:
  QuickRopeNode(const std::string &name, int num_vertices, PN_stdfloat thickness, int subdiv = 1);

  INLINE void set_point(int n, const LPoint3 &point);
  INLINE int get_num_points() const { return (int)_points.size(); }
  INLINE void finish_modify_points();

  void recompute_interpolated_points();

public:
  virtual void add_for_draw(CullTraverser *trav, CullTraverserData &data) override;

  virtual void compute_internal_bounds(CPT(BoundingVolume) &internal_bounds,
                                       int &internal_vertices,
                                       int pipeline_stage,
                                       Thread *current_thread) const override;

private:
  // We only need one set of fixed indices, shared between each
  // camera.
  PT(GeomTristrips) _tristrips;

  int _subdiv;

  PN_stdfloat _thickness;
  // Protects the cam data cache.
  LightMutex _lock;

  class CamData : public ReferenceCount {
  public:
    // Double-buffered vertex datas for Panda pipelining
    // AND GPU pipelining.
    PT(GeomVertexData) _vertex_data[2];
    PT(Geom) _geom;
    int _last_frame = 0;
  };
  pflat_hash_map<WPT(Camera), PT(CamData)> _cam_data;

  pvector<LPoint3> _points;

  // Interpolated spline points.
  pvector<LPoint3> _interp_points;
};

#include "quickRopeNode.I"

#endif // QUICKROPENODE_H
