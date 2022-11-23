"""ScoutResponses module: contains the ScoutResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
ScoutBaseResponses = {
  'battle_cry': stringList('Scout.BattleCry', (1, 5)),
  'stalemate': stringList('Scout.AutoDejectedTie', (1, 4)),
  'capped_ctf': stringList('Scout.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Scout.Medic', (1, 3)),
  'medic_follow': stringList('Scout.MedicFollow', (1, 4)),
  'spy': stringList('Scout.CloakedSpy', (1, 4)),
  'spy_scout': ['Soldier.CloakedSpyIdentify01'],
  'spy_soldier': ['Soldier.CloakedSpyIdentify02'],
  'spy_pyro': ['Soldier.CloakedSpyIdentify04'],
  'spy_demo': ['Soldier.CloakedSpyIdentify05'],
  'spy_heavy': ['Soldier.CloakedSpyIdentify03'],
  'spy_engineer': ['Soldier.CloakedSpyIdentify08'],
  'spy_medic': ['Soldier.CloakedSpyIdentify07'],
  'spy_sniper': ['Soldier.CloakedSpyIdentify09'],
  'spy_spy': ['Soldier.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Scout.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Scout.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Scout.HelpMe', (1, 4)),
  'help_capture': stringList('Scout.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Scout.HelpMeDefend', (1, 3)),
  'incoming': stringList('Scout.Incoming', (1, 3)),
  'good_job': stringList('Scout.GoodJob', (1, 4)),
  'nice_shot': stringList('Scout.NiceShot', (1, 3)),
  'cheers': stringList('Scout.Cheers', (1, 6)),
  'jeers': stringList('Scout.Jeers', (2, 12)),
  'positive': stringList('Scout.PositiveVocalization', (1, 5)),
  'negative': stringList('Scout.NegativeVocalization', (1, 5)),
  'need_sentry': ['Scout.NeedSentry01'],
  'need_dispenser': ['Scout.NeedDispenser01'],
  'need_teleporter': ['Scout.NeedTeleporter01'],
  'sentry_ahead': stringList('Scout.SentryAhead', (1, 3)),
  'activate_charge': stringList('Scout.ActivateCharge', (1, 3)),
  'yes': stringList('Scout.Yes', (1, 3)),
  'no': stringList('Scout.No', (1, 3)),
  'go': stringList('Scout.Go', (1, 4)),
  'move_up': stringList('Scout.MoveUp', (1, 3)),
  'go_left': stringList('Scout.HeadLeft', (1, 3)),
  'go_right': stringList('Scout.HeadRight', (1, 3)),
  'thanks': stringList('Scout.Thanks', (1, 2)),
  'assist_thanks': stringList('Scout.SpecialCompleted-AssistedKill', (1, 2)),
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, ScoutBaseResponses)
    system.sortRules()
    return system
