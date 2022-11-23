"""SoldierResponses module: contains the SoldierResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
SoldierBaseResponses = {
  'battle_cry': stringList('Soldier.BattleCry', (1, 6)),
  'stalemate': stringList('Soldier.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Soldier.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Soldier.Medic', (1, 3)),
  'medic_follow': stringList('Soldier.PickAxeTaunt', (1, 5)),
  'spy': stringList('Soldier.CloakedSpy', (1, 3)),
  'spy_scout': ['Soldier.CloakedSpyIdentify01'],
  'spy_soldier': ['Soldier.CloakedSpyIdentify02'],
  'spy_pyro': ['Soldier.CloakedSpyIdentify04'],
  'spy_demo': ['Soldier.CloakedSpyIdentify05'],
  'spy_heavy': ['Soldier.CloakedSpyIdentify03'],
  'spy_engineer': ['Soldier.CloakedSpyIdentify07'],
  'spy_medic': ['Soldier.CloakedSpyIdentify06'],
  'spy_sniper': ['Soldier.CloakedSpyIdentify08'],
  'spy_spy': ['Soldier.CloakedSpyIdentify09'],
  'teleporter_thanks': stringList('Soldier.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Soldier.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Soldier.HelpMe', (1, 3)),
  'help_capture': stringList('Soldier.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Soldier.HelpMeDefend', (1, 4)),
  'incoming': ['Soldier.Incoming01'],
  'good_job': stringList('Soldier.GoodJob', (1, 3)),
  'nice_shot': stringList('Soldier.NiceShot', (1, 3)),
  'cheers': stringList('Soldier.Cheers', (1, 6)),
  'jeers': stringList('Soldier.Jeers', (1, 12)),
  'positive': stringList('Soldier.PositiveVocalization', (1, 5)),
  'negative': stringList('Soldier.NegativeVocalization', (1, 6)),
  'need_sentry': ['Soldier.NeedSentry01'],
  'need_dispenser': ['Soldier.NeedDispenser01'],
  'need_teleporter': ['Soldier.NeedTeleporter01'],
  'sentry_ahead': stringList('Soldier.SentryAhead', (1, 3)),
  'activate_charge': stringList('Soldier.ActivateCharge', (1, 3)),
  'yes': stringList('Soldier.Yes', (1, 4)),
  'no': stringList('Soldier.No', (1, 3)),
  'go': stringList('Soldier.Go', (1, 3)),
  'move_up': stringList('Soldier.MoveUp', (1, 3)),
  'go_left': stringList('Soldier.HeadLeft', (1, 3)),
  'go_right': stringList('Soldier.HeadRight', (1, 3)),
  'thanks': stringList('Soldier.Thanks', (1, 2)),
  'assist_thanks': ['Soldier.SpecialCompleted-AssistedKill01']
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SoldierBaseResponses)
    system.sortRules()
    return system
