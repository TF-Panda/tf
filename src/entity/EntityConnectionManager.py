"""EntityConnectionManager module: contains the EntityConnectionManager class."""

from direct.directnotify.DirectNotifyGlobal import directNotify

class OutputConnection:

    def __init__(self):
        self.targetEntityName = ''
        self.inputName = ''
        self.parameters = []
        self.once = False
        self.delay = 0.0

class EntityConnectionManager:

    notify = directNotify.newCategory('EntityConnectionManager')

    GlobalIOQueue = []

    def __init__(self, entity):
        self.entity = entity
        self.outputs = {}
        self.delayedTasks = set()

    def processIOQueue(task):
        if not EntityConnectionManager.GlobalIOQueue:
            return task.cont

        # Hold a temporary reference to the current queue, clear
        # the global queue, and iterate over the temporary queue.
        # This allows a new queue to be built up this frame while
        # we fire the inputs of the previous queue.

        theQueue = EntityConnectionManager.GlobalIOQueue
        EntityConnectionManager.GlobalIOQueue = list()
        for entity, targetEnt, func, params in theQueue:
            if entity.connMgr is None or targetEnt.connMgr is None:
                # Source or target entity was deleted.
                continue
            # Fire the input.
            if params:
                func(entity, *params)
            else:
                func(entity)

        return task.cont

    def __delayedConnectionTask(self, entity, targetEnt, func, params, task):
        # FIXME: Need to check that the entity we're calling still exists.
        if task in self.delayedTasks:
            self.delayedTasks.remove(task)
        EntityConnectionManager.GlobalIOQueue.append((entity, targetEnt, func, params))
        return task.done

    def addConnection(self, outputName, connection):
        connections = self.outputs.get(outputName, [])
        connections.append(connection)
        self.outputs[outputName] = connections

    def cleanup(self):
        self.entity = None
        self.outputs = None
        for t in self.delayedTasks:
            t.remove()
        self.delayedTasks = None

    def getConnectionEntity(self, targetName, activator, caller):
        if targetName == '!self':
            return (self.entity,)
        elif targetName == '!activator':
            return (activator,)
        elif targetName == '!caller':
            return (caller,)
        elif targetName == 'tf_gamerules':
            return (base.game.gameRulesProxy,)
        else:
            # Look up target name in entity dictionary.
            return base.entMgr.findAllEntities(targetName)

    def fireOutput(self, name, extraArgs=[], activator=None):
        connections = self.outputs.get(name)
        if not connections:
            # Output has no connections.
            return

        # Trigger all connections.
        for connection in list(connections):
            ents = self.getConnectionEntity(connection.targetEntityName, activator, None)
            if not ents:
                self.notify.warning(f'Output {name} is connected to non-existent entity {connection.targetEntityName}.')
                continue
            funcName = 'input_' + connection.inputName
            params = connection.parameters + extraArgs
            for ent in ents:
                func = getattr(ent, funcName, None)
                if func:
                    if connection.delay > 0.0:
                        # Add a task to fire it later.
                        task = base.simTaskMgr.doMethodLater(connection.delay, self.__delayedConnectionTask,
                            'delayedConnection', extraArgs=[self.entity, ent, func, params], appendTask=True)
                        self.delayedTasks.add(task)
                    else:
                        # Fire it immediately.
                        EntityConnectionManager.GlobalIOQueue.append((self.entity, ent, func, params))
                else:
                    self.notify.warning(f'Handling output {name} from entity {self.entity.__class__}, input method {funcName} does not exist on entity {ent.__class__}.')
            if connection.once:
                connections.remove(connection)


