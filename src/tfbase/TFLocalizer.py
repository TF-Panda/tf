
from panda3d.core import ConfigVariableString

language = ConfigVariableString("tf-language", "english")

from direct.directnotify.DirectNotifyGlobal import directNotify

notify = directNotify.newCategory("TFLocalizer")
notify.info("Running in language: " + language.getValue())

if language == 'english':
    from .TFLocalizerEnglish import *

if language == 'french':
    from .TFLocalizerFrench import *

if language == 'german':
    from .TFLocalizerGerman import *

def getLocalizedString(string):
    if string[0] != "#":
        # Not a localizer string name.
        return string
    # Look up the name in the localizer.
    return globals().get(string[1:], string)
