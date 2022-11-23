"""SpyResponses module: contains the SpyResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
SpyBaseResponses = {
  'battle_cry': stringList('Spy.BattleCry', (1, 4)),
  'stalemate': stringList('Spy.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Spy.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Spy.Medic', (1, 3)),
  'medic_follow': stringList('Spy.MedicFollow', (1, 2)),
  'spy': stringList('Spy.CloakedSpy', (1, 4)),
  'spy_scout': ['Spy.CloakedSpyIdentify01'],
  'spy_soldier': ['Spy.CloakedSpyIdentify02'],
  'spy_pyro': ['Spy.CloakedSpyIdentify04'],
  'spy_demo': ['Spy.CloakedSpyIdentify05'],
  'spy_heavy': ['Spy.CloakedSpyIdentify03'],
  'spy_engineer': ['Spy.CloakedSpyIdentify08'],
  'spy_medic': ['Spy.CloakedSpyIdentify07'],
  'spy_sniper': ['Spy.CloakedSpyIdentify09'],
  'spy_spy': ['Spy.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Spy.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Spy.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Spy.HelpMe', (1, 3)),
  'help_capture': stringList('Spy.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Spy.HelpMeDefend', (1, 3)),
  'incoming': stringList('Spy.Incoming', (1, 3)),
  'good_job': stringList('Spy.GoodJob', (1, 3)),
  'nice_shot': stringList('Spy.NiceShot', (1, 3)),
  'cheers': stringList('Spy.Cheers', (1, 8)),
  'jeers': stringList('Spy.Jeers', (1, 6)),
  'positive': stringList('Spy.PositiveVocalization', (1, 5)),
  'negative': stringList('Spy.NegativeVocalization', (1, 9)),
  'need_sentry': ['Spy.NeedSentry01'],
  'need_dispenser': ['Spy.NeedDispenser01'],
  'need_teleporter': ['Spy.NeedTeleporter01'],
  'sentry_ahead': stringList('Spy.SentryAhead', (1, 2)),
  'activate_charge': stringList('Spy.ActivateCharge', (1, 3)),
  'yes': stringList('Spy.Yes', (1, 3)),
  'no': stringList('Spy.No', (1, 3)),
  'go': stringList('Spy.Go', (1, 3)),
  'move_up': stringList('Spy.MoveUp', (1, 2)),
  'go_left': stringList('Spy.HeadLeft', (1, 3)),
  'go_right': stringList('Spy.HeadRight', (1, 3)),
  'thanks': stringList('Spy.Thanks', (1, 3)),
  'assist_thanks': stringList('Spy.SpecialCompleted-AssistedKill', (1, 2)),
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SpyBaseResponses)
    system.sortRules()
    return system
