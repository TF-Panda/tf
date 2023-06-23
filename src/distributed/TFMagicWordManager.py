"""TFMagicWordManager module: contains the TFMagicWordManager class."""

# Magic words allow for players to type chat messages that perform special
# functions, used for debugging, developer controls, etc.  It is based on
# the magic word system used in Toontown.  It is analogous to console commands
# in OG TF2, but it goes through the chat interface.
#
# The magic word manager lives in a special zone that the server gives
# the player interest to, if they have magic word privileges.

from direct.distributed2.DistributedObject import DistributedObject
from direct.directnotify.DirectNotifyGlobal import directNotify

class TFMagicWordManager(DistributedObject):

    notify = directNotify.newCategory("TFMagicWordManager")

    def __init__(self):
        DistributedObject.__init__(self)

        self.magicWords = {
            "probedbg": self.__toggleProbeDebug,
            "visdbg": self.__toggleVisDebug,
            "reloadshaders": self.__reloadShaders,
            "toggleik": self.__toggleIk,
            "bounds": self.__toggleBounds,
            "wireframe": self.__toggleWireframe,
            "ls": self.__ls,
            "analyze": self.__analyze,
            "buildcubemaps": self.__buildCubeMaps
        }

    def announceGenerate(self):
        DistributedObject.announceGenerate(self)
        base.cr.magicWordManager = self
        try:
            base.localAvatar.chatFeed.addChat("Magic words enabled!")
        except:
            pass

    def disable(self):
        try:
            base.localAvatar.chatFeed.addChat("Magic words disabled!")
        except:
            pass
        base.cr.magicWordManager = None
        DistributedObject.disable(self)

    def __buildCubeMaps(self, _):
        base.game.renderCubeMaps()

    def __toggleProbeDebug(self, _):
        base.game.toggleProbeVis()
        if base.game.probeVis:
            return "Probe vis ON"
        else:
            return "Probe vis OFF"

    def __toggleVisDebug(self, _):
        base.game.toggleVisDebug()
        if base.game.visDebug:
            return "Vis debug ON"
        else:
            return "Vis debug OFF"

    def __reloadShaders(self, _):
        from panda3d.core import ShaderManager
        ShaderManager.getGlobalPtr().reloadShaders()
        return "Shaders reloaded"

    def __toggleIk(self, _):
        base.toggleIk()
        if base.enableIk:
            return "IK ENABLED"
        else:
            return "IK DISABLED"

    def __toggleBounds(self, _):
        base.toggleBounds()
        if base.showingBounds:
            return "Bounds vis ON"
        else:
            return "Bounds vis OFF"

    def __toggleWireframe(self, _):
        base.toggleWireframe()
        if base.wireframeEnabled:
            return "Wireframe ON"
        else:
            return "Wireframe OFF"

    def __ls(self, args):
        if not args:
            return "Specify a scene"
        if args[0] == "render":
            base.render.ls()
        elif args[0] == "vmrender":
            base.vmRender.ls()
        elif args[0] == "sky3d":
            base.sky3DTop.ls()
        else:
            return "Unknown scene to ls: " + args[1]

    def __analyze(self, args):
        if not args:
            return "Specify a scene"
        if args[0] == "render":
            base.render.analyze()
        elif args[0] == "vmrender":
            base.vmRender.analyze()
        elif args[0] == "sky3d":
            base.sky3DTop.analyze()
        else:
            return "Unknown scene to analyze: " + args[1]

    def extractArgs(self, expr : str):
        """
        Extracts the magic word expression into a command and list of
        arguments.
        """
        if not expr or expr.isspace():
            return ("", ())
        words = expr.split()
        if not words:
            return ("", ())
        if len(words) < 2:
            return (words[0], ())
        else:
            return (words[0], words[1:])

    def b_setMagicWord(self, expr : str):
        if not expr.startswith("~"):
            return "Not a magic word expression: " + expr

        cmd, args = self.extractArgs(expr[1:].lower())

        if not cmd:
            return "Invalid magic word expression: " + expr

        if cmd in self.magicWords:
            # This is a client-side magic word.
            try:
                resp = self.magicWords[cmd](args)
                return resp
            except Exception as e:
                return "Exception thrown in " + cmd + ": " + str(e)
        else:
            # Try it on the server.
            self.sendUpdate('setMagicWord', (cmd, args))
            return ""

    def magicWordResp(self, resp):
        if resp:
            base.localAvatar.chatFeed.addChat("Magic words: " + resp)


