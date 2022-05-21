/**
 * PANDA 3D SOFTWARE
 * Copyright (c) Carnegie Mellon University.  All rights reserved.
 *
 * All use of this software is subject to the terms of the revised BSD
 * license.  You should have received a copy of this license along
 * with this source code in a file named "LICENSE."
 *
 * @file networkedObjectBase.cxx
 * @author brian
 * @date 2022-05-03
 */

#include "networkedObjectBase.h"
#include "appBase.h"

IMPLEMENT_CLASS(NetworkedObjectBase);

/**
 *
 */
void NetworkedObjectBase::
generate() {
  _life_state = LS_generated;
}

/**
 *
 */
void NetworkedObjectBase::
announce_generate() {
  _life_state = LS_alive;
}

/**
 *
 */
void NetworkedObjectBase::
disable() {
  remove_all_tasks();
  _life_state = LS_disabled;
}

/**
 *
 */
void NetworkedObjectBase::
destroy() {
  _life_state = LS_deleted;
}

/**
 * Called before unpacking new state information onto the object.
 * If generate is true, this is the initial state information of the object.
 */
void NetworkedObjectBase::
pre_data_update(bool generate) {
}

/**
 * Called after unpacking new state information onto the object.
 * If generate is true, this is a new object, and the initial state was just
 * unpacked.
 */
void NetworkedObjectBase::
post_data_update(bool generate) {
}

/**
 *
 */
GenericAsyncTask *NetworkedObjectBase::
add_task(const std::string &name, GenericAsyncTask::TaskFunc *func, int sort) {
  remove_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name, func, this);
  task->set_sort(sort);
  task->set_upon_death(task_death);
  base->get_task_mgr()->add(task);
  _task_map.insert({ name, task });
  return task;
}

/**
 *
 */
GenericAsyncTask *NetworkedObjectBase::
do_task_later(const std::string &name, GenericAsyncTask::TaskFunc *func, float delay, int sort) {
  remove_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name, func, this);
  task->set_sort(sort);
  task->set_upon_death(task_death);
  task->set_delay(delay);
  base->get_task_mgr()->add(task);
  _task_map.insert({ name, task });
  return task;
}

/**
 *
 */
GenericAsyncTask *NetworkedObjectBase::
add_sim_task(const std::string &name, GenericAsyncTask::TaskFunc *func, int sort) {
  remove_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name, func, this);
  task->set_sort(sort);
  task->set_upon_death(task_death);
  base->get_sim_task_mgr()->add(task);
  _task_map.insert({ name, task });
  return task;
}

/**
 *
 */
GenericAsyncTask *NetworkedObjectBase::
do_sim_task_later(const std::string &name, GenericAsyncTask::TaskFunc *func, float delay, int sort) {
  remove_task(name);
  PT(GenericAsyncTask) task = new GenericAsyncTask(name, func, this);
  task->set_sort(sort);
  task->set_upon_death(task_death);
  task->set_delay(delay);
  base->get_sim_task_mgr()->add(task);
  _task_map.insert({ name, task });
  return task;
}

/**
 *
 */
void NetworkedObjectBase::
remove_task(const std::string &name) {
  auto it = _task_map.find(name);
  if (it != _task_map.end()) {
    (*it).second->set_upon_death(nullptr);
    (*it).second->remove();
    _task_map.erase(it);
  }
}

/**
 *
 */
void NetworkedObjectBase::
remove_all_tasks() {
  for (auto it = _task_map.begin(); it != _task_map.end(); ++it) {
    GenericAsyncTask *task = (*it).second;
    task->set_upon_death(nullptr);
    task->remove();
  }
  _task_map.clear();
}

/**
 *
 */
void NetworkedObjectBase::
task_death(GenericAsyncTask *task, bool clean_exit, void *user_data) {
  NetworkedObjectBase *self = (NetworkedObjectBase *)user_data;
  auto it = self->_task_map.find(task->get_name());
  if (it != self->_task_map.end()) {
    self->_task_map.erase(it);
  }
}
