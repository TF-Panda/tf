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
  'melee_dare': stringList('sniper.MeleeDare', (1, 9)),
  'domination_scout': stringList('Soldier.DominationScout', (1, 11)),
  'domination_soldier': stringList('Soldier.DominationSoldier', (1, 6)),
  'domination_pyro': stringList('Soldier.DominationPyro', (1, 9)),
  'domination_demo': stringList('Soldier.DominationDemoman', (1, 6)),
  'domination_heavy': stringList('Soldier.DominationHeavy', (1, 7)),
  'domination_engineer': stringList('Soldier.DominationEngineer', (1, 6)),
  'domination_medic': stringList('Soldier.DominationMedic', (1, 7)),
  'domination_sniper': stringList('Soldier.DominationSniper', (1, 14)),
  'domination_spy': stringList('Soldier.DominationSpy', (1, 8))
}

zoomInPositiveLines = stringList("Sniper.PositiveVocalization", (6, 10))
zoomInNegativeLines = stringList("Sniper.NegativeVocalization", (6, 9))
sniperDefaultRevengeLines = [ # default, non-zoomed in
  'Sniper.Cheers01', 'Sniper.PositiveVocalization04',
  'Sniper.Taunts03', 'Sniper.Taunts04', 'Sniper.Taunts15',
  'Sniper.Taunts16', 'Sniper.PositiveVocalizataion03',
  'Sniper.GoodJob01'
]
sniperDefaultWhisperRevengeLines = [ # default, zoomed in
  'Sniper.Taunts25', 'Sniper.Taunts26'
]
sniperScoutRevengeLines = [
  'sniper.Revenge02', 'sniper.Revenge13', 'sniper.Revenge24'
]
sniperSoldierRevengeLines = [
  'sniper.Revenge09', 'sniper.Revenge21'
]
sniperPyroRevengeLines = [
  'sniper.Revenge11', 'sniper.Revenge14', 'sniper.Revenge17'
]
sniperDemoRevengeLines = [
  'sniper.Revenge01', 'sniper.Revenge07'
]
sniperHeavyRevengeLines = [
  'sniper.Revenge15', 'sniper.Revenge20'
]
sniperEngineerRevengeLines = [
  'sniper.Revenge12'
]
sniperMedicRevengeLines = [
  'sniper.Revenge23'
]
sniperSniperRevengeLines = [
  'sniper.Revenge16', 'sniper.Revenge18',
  'sniper.Revenge19', 'sniper.Revenge22'
]
sniperSpyRevengeLines = [
  'sniper.Revenge04', 'sniper.Revenge03',
  'sniper.Revenge05', 'sniper.Revenge06',
  'sniper.Revenge10'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SniperBaseResponses)

    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, percentChance50
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperDefaultRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Default revenge, zoomed in.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isZoomedIn, percentChance50
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperDefaultWhisperRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Revenge lines directed at classes.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimScout
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperScoutRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimSoldier
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperSoldierRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimPyro
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperPyroRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimDemo
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperDemoRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimHeavy
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperHeavyRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimEngineer
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperEngineerRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimMedic
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperMedicRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimSniper
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperSniperRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill, isVictimSpy
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in sniperSpyRevengeLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )

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
