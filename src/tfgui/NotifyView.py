"""NotifyView module: contains the NotifyView class"""

from panda3d.core import LineStream, Notify, StreamWriter, TextNode

from direct.directnotify.Notifier import Notifier
from direct.gui.DirectGui import DirectLabel


class NotifyView:
    """
    Redirects notify output to a set of DirectGUI labels on screen.
    """

    def __init__(self):
        # Labels will be parented here.
        self.node = base.a2dTopLeft.attachNewNode("notifyview")
        self.node.setPos(0.05, 0, -0.05)
        self.node.setBin('gui-popup', 1000)

        # Create a label to display the output.
        self.label = DirectLabel(
                                 #frameColor = (0, 0, 0, 0.5),
                                 #borderWidth = (0.012, 0.012),
                                 text = '',
                                 text_scale = 0.03,
                                 text_align = TextNode.ALeft,
                                 text_fg = (1, 1, 1, 1),
                                 text_bg = (0, 0, 0, 0.5),
                                 #text_shadow = (0, 0, 0, 1),
                                 parent = self.node
                                 )

        # Hijack the output of Notify so we can query it here.
        self.notifyOut = LineStream()
        Notify.ptr().setOstreamPtr(self.notifyOut, 0)
        Notifier.streamWriter = StreamWriter(Notify.out(), True)

        # We use this object to compute wordwrapping for us.  (It
        # should have the same font as the above label.  Here, they
        # both use the default font.)
        self.wordWrapObj = TextNode('wordWrapObj')
        self.wordWrapObj.setWordwrap(100)

        # This is the history of output lines that we will display
        # within the label.
        self.lines = []

        # Parameters that control the number of lines to retain and
        # display.
        self.numKeepLines = 100
        self.numDisplayLines = 10

        # Now spawn a task to keep things up to date.
        self.__updateText()
        taskMgr.add(self.updateNotify, 'updateNotify')

    def updateNotify(self, task):
        """ This method is run every frame as a task to query for the
        latest Notify output. """

        while self.notifyOut.isTextAvailable():
            self.addLine(self.notifyOut.getLine())
        return task.cont

    def addLine(self, line):
        """ Adds a single line to the output.  The line is wordwrapped
        into multiple lines if necessary. """

        # Check for notify level indicators and push text properties as
        # needed.
        if "(warning)" in line:
            line = "\1warning\1" + line + "\2"
        elif "(error)" in line or "(fatal)" in line or "Assertion failed" in line:
            line = "\1error\1" + line + "\2"

        # We handle wordwrap explicitly, so that we can keep an
        # accurate count of the number of lines.
        self.wordWrapObj.setText(line)
        result = self.wordWrapObj.getWordwrappedText().split('\n')
        self.lines += result

        self.__updateText()

    def __updateText(self):
        """ Called internally whenever self.lines is modified, to
        update the label display and do other maintenance. """

        # Truncate the text to keep only numKeepLines lines, so we
        # don't bloat memory indefinitely.
        self.lines = self.lines[-self.numKeepLines:]

        # Show the last numDisplayLines in the label.
        text = '\n'.join(self.lines[-self.numDisplayLines:])
        self.label['text'] = text
