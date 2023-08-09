"""HeavyResponses module: contains the HeavyResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Response, ResponseLine, Rule
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
HeavyBaseResponses = {
  'battle_cry': stringList('Heavy.BattleCry', (1, 6)),
  'stalemate': stringList('Heavy.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Heavy.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Heavy.AutoCappedControlPoint', (1, 3)),
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
  'assist_thanks': ['Heavy.SpecialCompleted-AssistedKill01'],
  'melee_dare': stringList('Heavy.MeleeDare', (1, 13)),
  'revenge': stringList('Heavy.Revenge', (1, 15)) + [
    'Heavy.Cheers03', 'Heavy.Cheers06', 'Heavy.PositiveVocalization03'
  ],
  'domination': stringList('Heavy.Domination', (1, 18)) + [
    'Heavy.Taunts12', 'Heavy.LaughterBig02', 'Heavy.LaughHappy03',
    'Heavy.LaughHappy04', 'Heavy.LaughHappy05', 'Heavy.LaughterBig03',
    'Heavy.LaughterBig04', 'Heavy.GoodJob02', 'Heavy.Jeers06',
    'Heavy.LaughEvil01', 'Heavy.LaughHappy01', 'Heavy.LaughHappy02',
    'Heavy.LaughLong01', 'Heavy.LaughLong02', 'Heavy.PositiveVocalization01',
    'Heavy.PositiveVocalization02'
  ]
}

heavyKilledPlayerManyLines = [
  'Heavy.SpecialCompleted09', 'Heavy.SpecialCompleted10',
  'Heavy.SpecialCompleted11', 'Heavy.Taunts04',
  'Heavy.Taunts05', 'Heavy.Taunts11'
]
heavyKilledPlayerVeryManyLines = [
  'Heavy.SpecialCompleted07', 'Heavy.SpecialCompleted08',
  'Heavy.Taunts01', 'Heavy.Taunts10', 'Heavy.Taunts14',
  'Heavy.Taunts19'
]
heavyDestructionLines = [
  'Heavy.SpecialCompleted02', 'Heavy.SpecialCompleted03',
  'Heavy.SpecialCompleted01', 'Heavy.LaughterBig01'
]
heavyMeleeKillLines = [
  'Heavy.LaughShort01', 'Heavy.LaughShort02'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, HeavyBaseResponses)

    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isManyRecentKills, weaponIsPrimary, notKillSpeech, percentChance30
        ],
        [
          Response(
            [
              ResponseLine(x) for x in heavyKilledPlayerManyLines
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
          isVeryManyRecentKills, weaponIsPrimary, notKillSpeech, percentChance50
        ],
        [
          Response(
            [
              ResponseLine(x) for x in heavyKilledPlayerVeryManyLines
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
              ResponseLine(x) for x in heavyMeleeKillLines
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
              ResponseLine(x) for x in heavyDestructionLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechObject', 'value': 1, 'expireTime': 30}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledObject,
      Rule(
        [
          percentChance10,
          lambda data: data.get('objecttype') == 'sentry',
          lambda data: not data.get('KillSpeechObject')
        ],
        [
          Response(
            [
              ResponseLine('Heavy.Taunts17')
            ]
          )
        ],
        [
          {'name': 'KillSpeechObject', 'value': 1, 'expireTime': 30}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledObject,
      Rule(
        [
          percentChance10,
          lambda data: data.get('objecttype') == 'dispenser',
          lambda data: not data.get('KillSpeechObject')
        ],
        [
          Response(
            [
              ResponseLine('Heavy.Taunts13')
            ]
          )
        ],
        [
          {'name': 'KillSpeechObject', 'value': 1, 'expireTime': 30}
        ]
      )
    )

    # Custom response battle cry against an Engineer.
    system.addRule(
      SpeechConcept.BattleCry,
      Rule(
        [
          isHoveringEnemy, isHoveringEngineer, percentChance30
        ],
        [
          Response(
            [
              ResponseLine('Heavy.Taunts13'),
              ResponseLine('Heavy.Taunts17')
            ]
          )
        ]
      )
    )
    # Custom response for taunt against non-Heavies.
    system.addRule(
      SpeechConcept.BattleCry,
      Rule(
        [
          isHoveringEnemy, isNotHoveringHeavy, isActiveWeaponNotMelee,
          percentChance75,
          lambda data: not data.get('GunTauntHeavy')
        ],
        [
          Response(
            [
              ResponseLine('Heavy.Taunts07'),
              ResponseLine('Heavy.Taunts10'),
              ResponseLine('Heavy.Taunts11')
            ]
          )
        ],
        [
          {'name': 'GunTauntHeavy', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.sortRules()
    return system
