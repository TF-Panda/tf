"""DemoResponses module: contains the DemoResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
DemoBaseResponses = {
  'battle_cry': stringList('Demoman.BattleCry', (1, 7)),
  'stalemate': stringList('Demoman.AutoDejectedTie', (1, 4)),
  'capped_ctf': stringList('Demoman.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Demoman.AutoCappedControlPoint', (1, 3)),
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
  'melee_dare': [
    'Demoman.Taunts03', 'Demoman.Taunts05', 'Demoman.Taunts14'
  ],
  'revenge': [
    'Demoman.GoodJob01', 'Demoman.Taunts16', 'Demoman.SpecialCompleted09',
    'Demoman.PositiveVocalization02'
  ],
  'domination_scout': stringList('Demoman.dominationscout', (1, 8)),
  'domination_soldier': stringList('Demoman.dominationsoldier', (1, 5)),
  'domination_pyro': stringList('Demoman.dominationpyro', (1, 4)),
  'domination_demo': stringList('Demoman.dominationdemoman', (1, 4)),
  'domination_heavy': stringList('Demoman.dominationheavy', (1, 5)),
  'domination_engineer': stringList('Demoman.dominationengineer', (1, 6)),
  'domination_medic': stringList('Demoman.dominationmedic', (1, 4)),
  'domination_sniper': stringList('Demoman.dominationsniper', (1, 4)),
  'domination_spy': stringList('Demoman.dominationspy', (1, 3))
}

demoKilledPlayerManyLines = [
  'Demoman.SpecialCompleted04',
  'Demoman.Taunts02', 'Demoman.Taunts04',
  'Demoman.Taunts08'
]
demoKilledPlayerVeryManyLines = [
  'Demoman.SpecialCompleted01', 'Demoman.SpecialCompleted03',
  'Demoman.SpecialCompleted07', 'Demoman.SpecialCompleted08',
  'Demoman.SpecialCompleted10', 'Demoman.Taunts12'
]
demoMeleeKillLines = [
  'Demoman.gibberish01', 'Demoman.gibberish02',
  'Demoman.gibberish04', 'Demoman.gibberish05',
  'Demoman.gibberish06', 'Demoman.gibberish07',
  'Demoman.gibberish08', 'Demoman.gibberish10',
  'Demoman.SpecialCompleted02'
]
demoDestructionLines = [
  'Demoman.SpecialCompleted11', 'Demoman.SpecialCompleted12'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, DemoBaseResponses)
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isManyRecentKills, weaponIsSecondary, notKillSpeech, percentChance30
        ],
        [
          Response(
            [
              ResponseLine(x) for x in demoKilledPlayerManyLines
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
          isVeryManyRecentKills, weaponIsSecondary, notKillSpeech, percentChance50
        ],
        [
          Response(
            [
              ResponseLine(x) for x in demoKilledPlayerVeryManyLines
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
              ResponseLine(x) for x in demoMeleeKillLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechMelee', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledObject,
      Rule(
        [
          percentChance30, isARecentKill,
          lambda data: not data.get('KillSpeechObject')
        ],
        [
          Response(
            [
              ResponseLine(x) for x in demoDestructionLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechObject', 'value': 1, 'expireTime': 30}
        ]
      )
    )
    system.sortRules()
    return system
