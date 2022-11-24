"""GuiPanel module: contains the GuiPanel class."""

from direct.gui.DirectGui import *
from direct.showbase.DirectObject import DirectObject

class GuiPanel(DirectFrame):
    """
    This is a base class for a popup GUI panel that associates commands
    with input device buttons.

    Multiple popup panels can be open at the same time, in which case keyboard
    events are transmitted to panels in order of most recently opened to least
    recently opened.  If two panels open at the same time are interested in the
    same keyboard button, only the most recently opened panel interested in the
    event will receive the button.
    """

    OpenPanels = []
    NextSort = 0
    GlobalPanelHandler = DirectObject()

    @staticmethod
    def initialize():
        bt = base.buttonThrowers[0].node()
        bt.setButtonDownEvent("button-down")
        GuiPanel.GlobalPanelHandler.accept("button-down", GuiPanel.__globalButtonDown)

    @staticmethod
    def __globalButtonDown(buttonName):
        for panel in reversed(GuiPanel.OpenPanels):
            if buttonName in panel.buttons:
                cmd, extraArgs = panel.buttons[buttonName]
                if extraArgs:
                    cmd(*extraArgs)
                else:
                    cmd()
                break

    def __init__(self, *args, **kwargs):
        DirectFrame.__init__(self, *args, **kwargs)
        self.buttons = {}
        self.initialiseoptions(GuiPanel)

    def bindButton(self, name, method, extraArgs=[]):
        self.buttons[name] = (method, extraArgs)

    def unbindButton(self, name):
        if name in self.buttons:
            del self.buttons[name]

    def unbindAllButtons(self):
        self.buttons = {}

    def destroy(self):
        self.closePanel()
        DirectFrame.destroy(self)

    def openPanel(self):
        assert self not in GuiPanel.OpenPanels
        self.setBin('gui-panel', GuiPanel.NextSort)
        GuiPanel.NextSort += 1
        GuiPanel.OpenPanels.append(self)

    def closePanel(self):
        if self in GuiPanel.OpenPanels:
            GuiPanel.OpenPanels.remove(self)


