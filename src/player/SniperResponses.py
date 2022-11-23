"""SniperResponses module: contains the SniperResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseSystemBase import *
from .ResponseCriteria import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
SniperBaseResponses = {
  'battle_cry': stringList('Sniper.BattleCry', (1, 6)),
  'stalemate': stringList('Sniper.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Sniper.AutoCappedIntelligence', (1, 5)),
  'medic_call': stringList('Sniper.Medic', (1, 2)),
  'medic_follow': stringList('sniper.MedicFollow', (1, 5)),
  'spy': stringList('Sniper.CloakedSpy', (1, 3)),
  'spy_scout': ['Sniper.CloakedSpyIdentify01'],
  'spy_soldier': ['Sniper.CloakedSpyIdentify02'],
  'spy_pyro': ['Sniper.CloakedSpyIdentify04'],
  'spy_demo': ['Sniper.CloakedSpyIdentify05'],
  'spy_heavy': ['Sniper.CloakedSpyIdentify03'],
  'spy_engineer': ['Sniper.CloakedSpyIdentify08'],
  'spy_medic': ['Sniper.CloakedSpyIdentify07'],
  'spy_sniper': ['Sniper.CloakedSpyIdentify09'],
  'spy_spy': ['Sniper.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Sniper.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Sniper.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Sniper.HelpMe', (1, 3)),
  'help_capture': stringList('Sniper.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Sniper.HelpMeDefend', (1, 3)),
  'incoming': stringList('Sniper.Incoming', (1, 4)),
  'good_job': stringList('Sniper.GoodJob', (1, 3)),
  'nice_shot': stringList('Sniper.NiceShot', (1, 3)),
  'cheers': stringList('Sniper.Cheers', (1, 8)),
  'jeers': stringList('Sniper.Jeers', (1, 8)),
  'positive': stringList('Sniper.PositiveVocalization', (1, 5)), # non-zoomed in
  'negative': stringList('Sniper.NegativeVocalization', (1, 5)), # non-zoomed in
  'need_sentry': ['Sniper.NeedSentry01'],
  'need_dispenser': ['Sniper.NeedDispenser01'],
  'need_teleporter': ['Sniper.NeedTeleporter01'],
  'sentry_ahead': ['Sniper.SentryAhead01'],
  'activate_charge': stringList('Sniper.ActivateCharge', (1, 4)),
  'yes': stringList('Sniper.Yes', (1, 3)),
  'no': stringList('Sniper.No', (1, 4)),
  'go': stringList('Sniper.Go', (1, 3)),
  'move_up': stringList('Sniper.MoveUp', (1, 2)),
  'go_left': stringList('Sniper.HeadLeft', (1, 3)),
  'go_right': stringList('Sniper.HeadRight', (1, 3)),
  'thanks': stringList('Sniper.Thanks', (1, 2)),
  'assist_thanks': stringList('Sniper.SpecialCompleted-AssistedKill', (1, 2)),
}

zoomInPositiveLines = stringList("Sniper.PositiveVocalization", (6, 10))
zoomInNegativeLines = stringList("Sniper.NegativeVocalization", (6, 9))

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SniperBaseResponses)

    # Whisper lines here when zoomed in.
    system.addRule(
      SpeechConcept.Positive,
      Rule(
        [
          isZoomedIn
        ],
        [
          Response(
            [
              ResponseLine(x) for x in zoomInPositiveLines
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Negative,
      Rule(
        [
          isZoomedIn
        ],
        [
          Response(
            [
              ResponseLine(x) for x in zoomInNegativeLines
            ]
          )
        ]
      )
    )


    system.sortRules()
    return system
