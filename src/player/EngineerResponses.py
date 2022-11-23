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
  'melee_dare': stringList('engineer_meleedare', (1, 3))
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
          lambda data: not data.get('EngineerKillSpeech')
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
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isVeryManyRecentKills, percentChance50,
          lambda data: not data.get('EngineerKillSpeech')
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted01")
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10}
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
          lambda data: not data.get('EngineerKillSpeech')
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
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )

    # Revenge kill responses.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill
        ],
        [
          Response(
            [
              ResponseLine("Engineer.BattleCry07", preDelay=2.5),
              ResponseLine("Engineer.Cheers01", preDelay=2.5),
              ResponseLine("Engineer.Cheers06", preDelay=2.5),
              ResponseLine("Engineer.Cheers07", preDelay=2.5),
              ResponseLine("Engineer.Jeers04", preDelay=2.5),
              ResponseLine("Engineer.LaughEvil01", preDelay=2.5),
              ResponseLine("Engineer.LaughEvil02", preDelay=2.5),
              ResponseLine("Engineer.LaughEvil05", preDelay=2.5),
              ResponseLine("Engineer.LaughEvil06", preDelay=2.5),
              ResponseLine("Engineer.LaughHappy01", preDelay=2.5),
              ResponseLine("Engineer.LaughHappy02", preDelay=2.5),
              ResponseLine("Engineer.LaughHappy03", preDelay=2.5),
              ResponseLine("Engineer.LaughLong01", preDelay=2.5),
              ResponseLine("Engineer.SpecialCompleted03", preDelay=2.5),
              ResponseLine("Engineer.Taunts02", preDelay=2.5),
              ResponseLine("Engineer.Taunts04", preDelay=2.5),
              ResponseLine("engineer_revenge01", preDelay=2.5),
              ResponseLine("engineer_revenge02", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Domination kill responses.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimScout
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationscout01", preDelay=2.5),
              ResponseLine("engineer_dominationscout02", preDelay=2.5),
              ResponseLine("engineer_dominationscout03", preDelay=2.5),
              ResponseLine("engineer_dominationscout04", preDelay=2.5),
              ResponseLine("engineer_dominationscout05", preDelay=2.5),
              ResponseLine("engineer_dominationscout06", preDelay=2.5),
              ResponseLine("engineer_dominationscout07", preDelay=2.5),
              ResponseLine("engineer_dominationscout08", preDelay=2.5),
              ResponseLine("engineer_dominationscout09", preDelay=2.5),
              ResponseLine("engineer_dominationscout10", preDelay=2.5),
              ResponseLine("engineer_dominationscout11", preDelay=2.5),
              ResponseLine("engineer_dominationscout12", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSoldier
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationsoldier01", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier02", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier03", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier04", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier05", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier06", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier07", preDelay=2.5),
              ResponseLine("engineer_dominationsoldier08", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimPyro
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationpyro01", preDelay=2.5),
              ResponseLine("engineer_dominationpyro02", preDelay=2.5),
              ResponseLine("engineer_dominationpyro03", preDelay=2.5),
              ResponseLine("engineer_dominationpyro04", preDelay=2.5),
              ResponseLine("engineer_dominationpyro05", preDelay=2.5),
              ResponseLine("engineer_dominationpyro06", preDelay=2.5),
              ResponseLine("engineer_dominationpyro07", preDelay=2.5),
              ResponseLine("engineer_dominationpyro08", preDelay=2.5),
              ResponseLine("engineer_dominationpyro09", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimDemo
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationdemoman01", preDelay=2.5),
              ResponseLine("engineer_dominationdemoman02", preDelay=2.5),
              ResponseLine("engineer_dominationdemoman03", preDelay=2.5),
              ResponseLine("engineer_dominationdemoman04", preDelay=2.5),
              ResponseLine("engineer_dominationdemoman05", preDelay=2.5),
              ResponseLine("engineer_dominationdemoman06", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimHeavy
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationheavy01", preDelay=2.5),
              ResponseLine("engineer_dominationheavy02", preDelay=2.5),
              ResponseLine("engineer_dominationheavy03", preDelay=2.5),
              ResponseLine("engineer_dominationheavy04", preDelay=2.5),
              ResponseLine("engineer_dominationheavy05", preDelay=2.5),
              ResponseLine("engineer_dominationheavy06", preDelay=2.5),
              ResponseLine("engineer_dominationheavy07", preDelay=2.5),
              ResponseLine("engineer_dominationheavy08", preDelay=2.5),
              ResponseLine("engineer_dominationheavy09", preDelay=2.5),
              ResponseLine("engineer_dominationheavy10", preDelay=2.5),
              ResponseLine("engineer_dominationheavy11", preDelay=2.5),
              ResponseLine("engineer_dominationheavy12", preDelay=2.5),
              ResponseLine("engineer_dominationheavy13", preDelay=2.5),
              ResponseLine("engineer_dominationheavy14", preDelay=2.5),
              ResponseLine("engineer_dominationheavy15", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimEngineer
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationengineer01", preDelay=2.5),
              ResponseLine("engineer_dominationengineer02", preDelay=2.5),
              ResponseLine("engineer_dominationengineer03", preDelay=2.5),
              ResponseLine("engineer_dominationengineer04", preDelay=2.5),
              ResponseLine("engineer_dominationengineer05", preDelay=2.5),
              ResponseLine("engineer_dominationengineer06", preDelay=2.5),
              ResponseLine("engineer_dominationengineer07", preDelay=2.5),
              ResponseLine("engineer_dominationengineer08", preDelay=2.5),
              ResponseLine("engineer_dominationengineer09", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimMedic
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationmedic01", preDelay=2.5),
              ResponseLine("engineer_dominationmedic02", preDelay=2.5),
              ResponseLine("engineer_dominationmedic03", preDelay=2.5),
              ResponseLine("engineer_dominationmedic04", preDelay=2.5),
              ResponseLine("engineer_dominationmedic05", preDelay=2.5),
              ResponseLine("engineer_dominationmedic06", preDelay=2.5),
              ResponseLine("engineer_dominationmedic07", preDelay=2.5),
              ResponseLine("engineer_dominationmedic08", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSniper
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationsniper01", preDelay=2.5),
              ResponseLine("engineer_dominationsniper02", preDelay=2.5),
              ResponseLine("engineer_dominationsniper03", preDelay=2.5),
              ResponseLine("engineer_dominationsniper04", preDelay=2.5),
              ResponseLine("engineer_dominationsniper05", preDelay=2.5),
              ResponseLine("engineer_dominationsniper06", preDelay=2.5),
              ResponseLine("engineer_dominationsniper07", preDelay=2.5),
              ResponseLine("engineer_dominationsniper08", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSpy
        ],
        [
          Response(
            [
              ResponseLine("engineer_dominationspy01", preDelay=2.5),
              ResponseLine("engineer_dominationspy02", preDelay=2.5),
              ResponseLine("engineer_dominationspy03", preDelay=2.5),
              ResponseLine("engineer_dominationspy04", preDelay=2.5),
              ResponseLine("engineer_dominationspy05", preDelay=2.5),
              ResponseLine("engineer_dominationspy06", preDelay=2.5),
              ResponseLine("engineer_dominationspy07", preDelay=2.5),
              ResponseLine("engineer_dominationspy08", preDelay=2.5),
              ResponseLine("engineer_dominationspy09", preDelay=2.5),
              ResponseLine("engineer_dominationspy10", preDelay=2.5),
              ResponseLine("engineer_dominationspy11", preDelay=2.5),
              ResponseLine("engineer_dominationspy12", preDelay=2.5),
              ResponseLine("engineer_dominationspy13", preDelay=2.5)
            ]
          )
        ],
        [
          {'name': 'EngineerKillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )

    system.sortRules()

    return system
