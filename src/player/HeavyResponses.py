"""HeavyResponses module: contains the HeavyResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
HeavyBaseResponses = {
  'battle_cry': stringList('Heavy.BattleCry', (1, 6)),
  'stalemate': stringList('Heavy.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Heavy.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Heavy.Medic', (1, 3)),
  'medic_follow': stringList('Heavy.MedicFollow', (1, 7)),
  'spy': stringList('Heavy.CloakedSpy', (1, 4)),
  'spy_scout': ['Heavy.CloakedSpyIdentify01'],
  'spy_soldier': ['Heavy.CloakedSpyIdentify02'],
  'spy_pyro': ['Heavy.CloakedSpyIdentify04'],
  'spy_demo': ['Heavy.CloakedSpyIdentify05'],
  'spy_heavy': ['Heavy.CloakedSpyIdentify03'],
  'spy_engineer': ['Heavy.CloakedSpyIdentify08'],
  'spy_medic': ['Heavy.CloakedSpyIdentify07'],
  'spy_sniper': ['Heavy.CloakedSpyIdentify09'],
  'spy_spy': ['Heavy.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Heavy.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Heavy.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Heavy.HelpMe', (1, 3)),
  'help_capture': stringList('Heavy.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Heavy.HelpMeDefend', (1, 3)),
  'incoming': stringList('Heavy.Incoming', (1, 3)),
  'good_job': stringList('Heavy.GoodJob', (1, 4)),
  'nice_shot': stringList('Heavy.NiceShot', (1, 3)),
  'cheers': stringList('Heavy.Cheers', (1, 8)),
  'jeers': stringList('Heavy.Jeers', (1, 9)),
  'positive': stringList('Heavy.PositiveVocalization', (1, 5)),
  'negative': stringList('Heavy.NegativeVocalization', (1, 6)),
  'need_sentry': ['Heavy.NeedSentry01'],
  'need_dispenser': ['Heavy.NeedDispenser01'],
  'need_teleporter': ['Heavy.NeedTeleporter01'],
  'sentry_ahead': stringList('Heavy.SentryAhead', (1, 2)),
  'activate_charge': stringList('Heavy.ActivateCharge', (1, 4)),
  'yes': stringList('Heavy.Yes', (1, 3)),
  'no': stringList('Heavy.No', (1, 3)),
  'go': stringList('Heavy.Go', (1, 3)),
  'move_up': stringList('Heavy.MoveUp', (1, 3)),
  'go_left': stringList('Heavy.HeadLeft', (1, 3)),
  'go_right': stringList('Heavy.HeadRight', (1, 3)),
  'thanks': stringList('Heavy.Thanks', (1, 3)),
  'assist_thanks': ['Heavy.SpecialCompleted-AssistedKill01']
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, HeavyBaseResponses)
    system.sortRules()
    return system
