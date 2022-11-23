"""PyroResponses module: contains the PyroResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
PyroBaseResponses = {
  'battle_cry': stringList('Pyro.BattleCry', (1, 2)),
  'stalemate': ['Pyro.AutoDejectedTie01'],
  'capped_ctf': ['Pyro.AutoCappedIntelligence01'],
  'medic_call': ['Pyro.Medic01'],
  'spy': ['Pyro.CloakedSpy01'],
  'teleporter_thanks': ['Pyro.ThanksForTheTeleporter01'],
  'heal_thanks': ['Pyro.ThanksForTheHeal01'],
  'help_me': ['Pyro.HelpMe01'],
  'help_capture': ['Pyro.HelpMeCapture01'],
  'help_defend': ['Pyro.HelpMeDefend01'],
  'incoming': ['Pyro.Incoming01'],
  'good_job': ['Pyro.GoodJob01'],
  'nice_shot': ['Pyro.NiceShot01'],
  'cheers': ['Pyro.Cheers01'],
  'jeers': stringList('Pyro.Jeers', (1, 2)),
  'positive': ['Pyro.PositiveVocalization01'],
  'negative': ['Pyro.NegativeVocalization01'],
  'need_sentry': ['Pyro.NeedSentry01'],
  'need_dispenser': ['Pyro.NeedDispenser01'],
  'need_teleporter': ['Pyro.NeedTeleporter01'],
  'sentry_ahead': ['Pyro.SentryAhead01'],
  'activate_charge': ['Pyro.ActivateCharge01'],
  'yes': ['Pyro.Yes01'],
  'no': ['Pyro.No01'],
  'go': ['Pyro.Go01'],
  'move_up': ['Pyro.MoveUp01'],
  'go_left': ['Pyro.HeadLeft01'],
  'go_right': ['Pyro.HeadRight01'],
  'thanks': ['Pyro.Thanks01'],
  'assist_thanks': ['Pyro.SpecialCompleted-AssistedKill01']
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, PyroBaseResponses)
    system.sortRules()
    return system
