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

    def __init__(self, entity):
        self.entity = entity
        self.outputs = {}

    def addConnection(self, outputName, connection):
        connections = self.outputs.get(outputName, [])
        connections.append(connection)
        self.outputs[outputName] = connections

    def cleanup(self):
        self.entity = None
        self.outputs = None

    def getConnectionEntity(self, targetName, activator, caller):
        if targetName == '!self':
            return (self.entity,)
        elif targetName == '!activator':
            return (activator,)
        elif targetName == '!caller':
            return (caller,)
        else:
            # Look up target name in entity dictionary.
            return base.entMgr.findEntity(targetName)

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
            # TODO: Delays
            funcName = 'input_' + connection.inputName
            params = connection.parameters + extraArgs
            for ent in ents:
                func = getattr(ent, funcName)
                if func:
                    if params:
                        func(self.entity, *params)
                    else:
                        func(self.entity)
                else:
                    self.notify.warning(f'Handling output {name} from entity {self.entity}, input method {funcName} does not exist on entity {ent}.')
            if connection.once:
                connections.remove(connection)


