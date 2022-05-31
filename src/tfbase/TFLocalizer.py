
from panda3d.core import ConfigVariableString
language = ConfigVariableString("tf-language", "english")

from direct.directnotify.DirectNotifyGlobal import directNotify
notify = directNotify.newCategory("TFLocalizer")
notify.info("Running in language: " + language.getValue())

if language == 'english':
    from .TFLocalizerEnglish import *
