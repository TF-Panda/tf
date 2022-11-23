"""MedicResponses module: contains the MedicResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
MedicBaseResponses = {
  'battle_cry': stringList('Medic.BattleCry', (1, 6)),
  'stalemate': stringList('Medic.AutoDejectedTie', (1, 7)),
  'capped_ctf': stringList('Medic.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Medic.Medic', (1, 3)),
  'spy': stringList('Medic.CloakedSpy', (1, 2)),
  'spy_scout': ['Medic.CloakedSpyIdentify01'],
  'spy_soldier': ['Medic.CloakedSpyIdentify02'],
  'spy_pyro': ['Medic.CloakedSpyIdentify04'],
  'spy_demo': ['Medic.CloakedSpyIdentify05'],
  'spy_heavy': ['Medic.CloakedSpyIdentify03'],
  'spy_engineer': ['Medic.CloakedSpyIdentify08'],
  'spy_medic': ['Medic.CloakedSpyIdentify07'],
  'spy_sniper': ['Medic.CloakedSpyIdentify09'],
  'spy_spy': ['Medic.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Medic.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Medic.ThanksForTheHeal', (1, 2)),
  'help_me': stringList('Medic.HelpMe', (1, 3)),
  'help_capture': stringList('Medic.HelpMeCapture', (1, 2)),
  'help_defend': stringList('Medic.HelpMeDefend', (1, 3)),
  'incoming': stringList('Medic.Incoming', (1, 3)),
  'good_job': stringList('Medic.GoodJob', (1, 3)),
  'nice_shot': stringList('Medic.NiceShot', (1, 2)),
  'cheers': stringList('Medic.Cheers', (1, 6)),
  'jeers': stringList('Medic.Jeers', (1, 12)),
  'positive': stringList('Medic.PositiveVocalization', (1, 6)),
  'negative': stringList('Medic.NegativeVocalization', (1, 7)),
  'need_sentry': ['Medic.NeedSentry01'],
  'need_dispenser': ['Medic.NeedDispenser01'],
  'need_teleporter': ['Medic.NeedTeleporter01'],
  'sentry_ahead': stringList('Medic.SentryAhead', (1, 2)),
  'activate_charge': stringList('Medic.ActivateCharge', (1, 3)),
  'yes': stringList('Medic.Yes', (1, 3)),
  'no': stringList('Medic.No', (1, 3)),
  'go': stringList('Medic.Go', (1, 4)),
  'move_up': stringList('Medic.MoveUp', (1, 2)),
  'go_left': stringList('Medic.HeadLeft', (1, 3)),
  'go_right': stringList('Medic.HeadRight', (1, 3)),
  'thanks': stringList('Medic.Thanks', (1, 2)),
  'assist_thanks': stringList('Medic.SpecialCompleted-AssistedKill', (1, 2))
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, MedicBaseResponses)
    system.sortRules()
    return system
