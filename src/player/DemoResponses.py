"""DemoResponses module: contains the DemoResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
DemoBaseResponses = {
  'battle_cry': stringList('Demoman.BattleCry', (1, 7)),
  'stalemate': stringList('Demoman.AutoDejectedTie', (1, 4)),
  'capped_ctf': stringList('Demoman.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Demoman.Medic', (1, 3)),
  'spy': stringList('Demoman.CloakedSpy', (1, 3)),
  'spy_scout': ['Demoman.CloakedSpyIdentify01'],
  'spy_soldier': ['Demoman.CloakedSpyIdentify02'],
  'spy_pyro': ['Demoman.CloakedSpyIdentify09'],
  'spy_demo': ['Demoman.CloakedSpyIdentify04'],
  'spy_heavy': ['Demoman.CloakedSpyIdentify03'],
  'spy_engineer': ['Demoman.CloakedSpyIdentify07'],
  'spy_medic': ['Demoman.CloakedSpyIdentify06'],
  'spy_sniper': ['Demoman.CloakedSpyIdentify08'],
  'spy_spy': ['Demoman.CloakedSpyIdentify05'],
  'teleporter_thanks': stringList('Demoman.ThanksForTheTeleporter', (1, 2)),
  'heal_thanks': stringList('Demoman.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Demoman.HelpMe', (1, 3)),
  'help_capture': stringList('Demoman.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Demoman.HelpMeDefend', (1, 3)),
  'incoming': stringList('Demoman.Incoming', (1, 3)),
  'good_job': stringList('Demoman.GoodJob', (1, 2)),
  'nice_shot': stringList('Demoman.NiceShot', (1, 3)),
  'cheers': stringList('Demoman.Cheers', (1, 8)),
  'jeers': stringList('Demoman.Jeers', (1, 11)),
  'positive': stringList('Demoman.PositiveVocalization', (1, 5)),
  'negative': stringList('Demoman.NegativeVocalization', (1, 6)),
  'need_sentry': ['Demoman.NeedSentry01'],
  'need_dispenser': ['Demoman.NeedDispenser01'],
  'need_teleporter': ['Demoman.NeedTeleporter01'],
  'sentry_ahead': stringList('Demoman.SentryAhead', (1, 3)),
  'activate_charge': stringList('Demoman.ActivateCharge', (1, 3)),
  'yes': stringList('Demoman.Yes', (1, 3)),
  'no': stringList('Demoman.No', (1, 3)),
  'go': stringList('Demoman.Go', (1, 3)),
  'move_up': stringList('Demoman.MoveUp', (1, 3)),
  'go_left': stringList('Demoman.HeadLeft', (1, 3)),
  'go_right': stringList('Demoman.HeadRight', (1, 3)),
  'thanks': stringList('Demoman.Thanks', (1, 2)),
  'assist_thanks': stringList('Demoman.SpecialCompleted-AssistedKill', (1, 2)),
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, DemoBaseResponses)
    system.sortRules()
    return system
