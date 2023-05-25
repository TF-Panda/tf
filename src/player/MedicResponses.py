"""MedicResponses module: contains the MedicResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
MedicBaseResponses = {
  'battle_cry': stringList('Medic.BattleCry', (1, 6)),
  'stalemate': stringList('Medic.AutoDejectedTie', (1, 7)),
  'capped_ctf': stringList('Medic.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Medic.AutoCappedControlPoint', (1, 3)),
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
  'positive': stringList('Medic.PositiveVocalization', (1, 3)) + stringList('Medic.PositiveVocalization', (5, 6)),
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
  'assist_thanks': stringList('Medic.SpecialCompleted-AssistedKill', (1, 2)),
  'melee_dare': [
    'Medic.Taunts01', 'Medic.Taunts04', 'Medic.Taunts05',
    'Medic.Taunts06', 'Medic.Taunts10', 'Medic.Taunts12',
    'Medic.Taunts13', 'Medic.Taunts15'
  ],
  'revenge': [
    'Medic.GoodJob02', 'Medic.NegativeVocalization02',
    'Medic.NegativeVocalization06', 'Medic.NegativeVocalization07'
  ],
  'domination': [
    'Medic.Taunts14', 'Medic.Taunts12', 'Medic.LaughLong01',
    'Medic.LaughLong02', 'Medic.LaughHappy01', 'Medic.LaughHappy02',
    'Medic.LaughHappy03', 'Medic.LaughEvil02', 'Medic.LaughEvil05',
    'Medic.LaughShort03'
  ]
}

medicKilledPlayerManyLines = [
  'Medic.Taunts02', 'Medic.SpecialCompleted12'
]
medicKilledPlayerVeryManyLines = [
  'Medic.SpecialCompleted09', 'Medic.SpecialCompleted02',
  'Medic.SpecialCompleted10', 'Medic.SpecialCompleted11'
]
medicMeleeKillLines = [
  'Medic.SpecialCompleted01'
]
medicChargeReadyLines = [
  "Medic.AutoChargeReady01",
  "Medic.AutoChargeReady02",
  "Medic.AutoChargeReady03"
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, MedicBaseResponses)
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isManyRecentKills, notKillSpeech, percentChance30
        ],
        [
          Response(
            [
              ResponseLine(x) for x in medicKilledPlayerManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isVeryManyRecentKills, notKillSpeech, percentChance50
        ],
        [
          Response(
            [
              ResponseLine(x) for x in medicKilledPlayerVeryManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsMelee, percentChance30,
          lambda data: not data.get('KillSpeechMelee')
        ],
        [
          Response(
            [
              ResponseLine(x) for x in medicMeleeKillLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechMelee', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # When we get full ubercharge.
    system.addRule(
      SpeechConcept.ChargeReady,
      Rule(
        [],
        [
          Response(
            [
              ResponseLine(x) for x in medicChargeReadyLines
            ]
          )
        ]
      )
    )
    system.sortRules()
    return system
