"""EngineerResponses module: contains the EngineerResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseCriteria import *
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
EngineerBaseResponses = {
  'battle_cry': ['Engineer.BattleCry01'] + stringList('Engineer.BattleCry', (3, 7)),
  'stalemate': stringList('Engineer.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Engineer.AutoCappedIntelligence', (1, 3)),
  'medic_call': stringList('Engineer.Medic', (1, 3)),
  'medic_follow': stringList('engineer_medicfollow', (1, 3)),
  'spy': stringList('Engineer.CloakedSpy', (1, 3)),
  'spy_scout': ['Engineer.CloakedSpyIdentify01'],
  'spy_soldier': ['Engineer.CloakedSpyIdentify02'],
  'spy_pyro': ['Engineer.CloakedSpyIdentify04'],
  'spy_demo': ['Engineer.CloakedSpyIdentify05'],
  'spy_heavy': ['Engineer.CloakedSpyIdentify03'],
  'spy_engineer': ['Engineer.CloakedSpyIdentify08'],
  'spy_medic': ['Engineer.CloakedSpyIdentify07'],
  'spy_sniper': ['Engineer.CloakedSpyIdentify09'],
  'spy_spy': ['Engineer.CloakedSpyIdentify10', 'Engineer.CloakedSpyIdentify06'],
  'teleporter_thanks': stringList('Engineer.ThanksForTheTeleporter', (1, 2)),
  'heal_thanks': stringList('Engineer.ThanksForTheHeal', (1, 2)),
  'help_me': stringList('Engineer.HelpMe', (1, 3)),
  'help_capture': stringList('Engineer.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Engineer.HelpMeDefend', (1, 3)),
  'incoming': stringList('Engineer.Incoming', (1, 3)),
  'good_job': stringList('Engineer.GoodJob', (1, 3)),
  'nice_shot': stringList('Engineer.NiceShot', (1, 3)),
  'cheers': stringList('Engineer.Cheers', (1, 7)),
  'jeers': stringList('Engineer.Jeers', (1, 4)),
  'positive': ['Engineer.PositiveVocalization01'],
  'negative': stringList('Engineer.NegativeVocalization', (1, 12)),
  'need_sentry': ['Engineer.NeedSentry01'],
  'need_dispenser': ['Engineer.NeedDispenser01'],
  'need_teleporter': stringList('Engineer.NeedTeleporter', (1, 2)),
  'sentry_ahead': stringList('Engineer.SentryAhead', (1, 2)),
  'activate_charge': stringList('Engineer.ActivateCharge', (1, 3)),
  'yes': stringList('Engineer.Yes', (1, 3)),
  'no': stringList('Engineer.No', (1, 3)),
  'go': stringList('Engineer.Go', (1, 3)),
  'move_up': ['Engineer.MoveUp01'],
  'go_left': stringList('Engineer.HeadLeft', (1, 2)),
  'go_right': stringList('Engineer.HeadRight', (1, 3)),
  'thanks': ['Engineer.Thanks01'],
  'assist_thanks': stringList('Engineer.SpecialCompleted-AssistedKill', (1, 2)),
  'melee_dare': stringList('engineer_meleedare', (1, 3)) + [
    'Engineer.Taunts01', 'Engineer.Taunts03', 'Engineer.Taunts05',
    'Engineer.Taunts06', 'Engineer.Taunts08', 'Engineer.Taunts10',
    'Engineer.Taunts12'
  ],
  'domination_scout': stringList('engineer_dominationscout', (1, 12)),
  'domination_solder': stringList('engineer_dominationsoldier', (1, 8)),
  'domination_pyro': stringList('engineer_dominationpyro', (1, 9)),
  'domination_demo': stringList('engineer_dominationdemoman', (1, 6)),
  'domination_heavy': stringList('engineer_dominationheavy', (1, 15)),
  'domination_engineer': stringList('engineer_dominationengineer', (1, 9)),
  'domination_medic': stringList('engineer_dominationmedic', (1, 8)),
  'domination_sniper': stringList('engineer_dominationsniper', (1, 8)),
  'domination_spy': stringList('engineer_dominationspy', (1, 13)),
  'revenge': [
    'Engineer.BattleCry07', 'Engineer.Cheers01', 'Engineer.Cheers06',
    'Engineer.Cheers07', 'Engineer.Jeers04', 'Engineer.LaughEvil01',
    'Engineer.LaughEvil02', 'Engineer.LaughEvil05', 'Engineer.LaughEvil06',
    'Engineer.LaughHappy01', 'Engineer.LaughHappy02', 'Engineer.LaughHappy03',
    'Engineer.LaughLong01', 'Engineer.SpecialCompleted03', 'Engineer.Taunts02',
    'Engineer.Taunts04', 'engineer_revenge01', 'engineer_revenge02'
  ]
}

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, EngineerBaseResponses)

    system.addRule(
      SpeechConcept.ObjectDestroyed,
      Rule(
        [
          lambda data: data['objecttype'] == 'sentry'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoDestroyedSentry01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ObjectDestroyed,
      Rule(
        [
          lambda data: data['objecttype'] == 'dispenser'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoDestroyedDispenser01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ObjectDestroyed,
      Rule(
        [
          lambda data: data['objecttype'] == 'teleporter'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoDestroyedTeleporter01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ObjectBuilding,
      Rule(
        [
          lambda data: data['objecttype'] == 'sentry'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoBuildingSentry01"),
              ResponseLine("Engineer.AutoBuildingSentry02")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ObjectBuilding,
      Rule(
        [
          lambda data: data['objecttype'] == 'dispenser'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoBuildingDispenser01"),
              ResponseLine("Engineer.AutoBuildingDispenser02")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ObjectBuilding,
      Rule(
        [
          lambda data: data['objecttype'] == 'teleporter'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoBuildingTeleporter01"),
              ResponseLine("Engineer.AutoBuildingTeleporter02")
            ]
          )
        ]
      )
    )

    # Killed multiple players recently.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isManyRecentKills, percentChance30,
          lambda data: not data.get('KillSpeech')
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted05"),
              ResponseLine("Engineer.SpecialCompleted10"),
              ResponseLine("Engineer.SpecialCompleted11")
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
          isVeryManyRecentKills, percentChance50,
          lambda data: not data.get('KillSpeech')
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted01")
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Killed player with melee.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          percentChance30, weaponIsMelee, isNotSentryKill,
          lambda data: not data.get('EngineerKillSpeechMelee')
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted07")
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeechMelee', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Sentry kill streak.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isManyRecentKills, isSentryKill, percentChance30,
          lambda data: not data.get('KillSpeech')
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted09"),
              ResponseLine("Engineer.SpecialCompleted06"),
              ResponseLine("Engineer.SpecialCompleted08"),
              ResponseLine("Engineer.SpecialCompleted02")
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )

    system.sortRules()

    return system
