"""ScoutResponses module: contains the ScoutResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Rule, Response, ResponseLine
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
ScoutBaseResponses = {
  'battle_cry': stringList('Scout.BattleCry', (1, 5)),
  'stalemate': stringList('Scout.AutoDejectedTie', (1, 4)),
  'capped_ctf': stringList('Scout.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Scout.AutoCappedControlPoint', (1, 4)),
  'medic_call': stringList('Scout.Medic', (1, 3)),
  'medic_follow': stringList('Scout.MedicFollow', (1, 4)),
  'spy': stringList('Scout.CloakedSpy', (1, 4)),
  'spy_scout': ['Scout.CloakedSpyIdentify01'],
  'spy_soldier': ['Scout.CloakedSpyIdentify02'],
  'spy_pyro': ['Scout.CloakedSpyIdentify04'],
  'spy_demo': ['Scout.CloakedSpyIdentify05'],
  'spy_heavy': ['Scout.CloakedSpyIdentify03'],
  'spy_engineer': ['Scout.CloakedSpyIdentify08'],
  'spy_medic': ['Scout.CloakedSpyIdentify07'],
  'spy_sniper': ['Scout.CloakedSpyIdentify09'],
  'spy_spy': ['Scout.CloakedSpyIdentify06'],
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
  'melee_dare': stringList('Scout.MeleeDare', (1, 6)) + [
    'Scout.Misc03', 'Scout.Taunts06', 'Scout.Taunts05',
    'Scout.Taunts10'
  ],
  'revenge': stringList('Scout.Revenge', (1, 9)) + [
    'Scout.Award12', 'Scout.Misc02', 'Scout.Misc09',
    'Scout.NiceShot02', 'Scout.SpecialCompleted12'
  ],
  'domination_scout': stringList('Scout.DominationSct', (1, 3)) + [
    'Scout.Domination13', 'Scout.Domination07', 'Scout.Domination05',
    'Scout.Domination20', 'Scout.Domination19', 'Scout.Domination21',
    'Scout.Misc07'
  ],
  'domination_soldier': stringList('Scout.DominationSol', (1, 6)),
  'domination_pyro': stringList('Scout.DominationPyr', (1, 6)) + [
    'Scout.Domination06', 'Scout.Misc08'
  ],
  'domination_demo': stringList('Scout.DominationDem', (1, 5)) + [
    'Scout.Domination01', 'Scout.Domination10'
  ],
  'domination_heavy': stringList('Scout.DominationHvy', (1, 10)) + [
    'Scout.Domination08', 'Scout.Domination09'
  ],
  'domination_engineer': stringList('Scout.DominationEng', (1, 6)) + ['Scout.Domination17'],
  'domination_medic': stringList('Scout.DominationMed', (1, 6)) + ['Scout.Misc02'],
  'domination_sniper': stringList('Scout.DominationSnp', (1, 5)) + ['Scout.Domination12'],
  'domination_spy': stringList('Soldier.DominationSpy', (1, 4)) + ['Scout.Award10']
}

scoutKilledPlayerManyLines = [
  'Scout.GoodJob02', 'Scout.LaughEvil02', 'Scout.LaughHappy01',
  'Scout.LaughHappy02', 'Scout.LaughHappy03', 'Scout.LaughHappy04',
  'Scout.LaughLong01', 'Scout.LaughLong02', 'Scout.Taunts04',
  'Scout.Taunts16'
]
scoutMeleeKillLines = [
  'Scout.SpecialCompleted03', 'Scout.SpecialCompleted02',
  'Scout.Taunts08', 'Scout.SpecialCompleted11',
  # These ones are specific to the bat.
  'Scout.SpecialCompleted04', 'Scout.SpecialCompleted06',
  'Scout.SpecialCompleted07', 'Scout.Taunts11',
  'Scout.SpecialCompleted09'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, ScoutBaseResponses)

    # Killed multiple players with primary weapon.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsPrimary, percentChance30, notKillSpeech, isManyRecentKills
        ],
        [
          Response(
            [
              ResponseLine(x) for x in scoutKilledPlayerManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 5}
        ]
      )
    )

    # Melee kill with the bat.
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
              ResponseLine(x) for x in scoutMeleeKillLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechMelee', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Eat it fatty! (Melee kill on Heavy).
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsMelee, isVictimHeavy, percentChance75,
          lambda data: not data.get('KillSpeechMeleeFat')
        ],
        [
          Response(
            [
              ResponseLine('Scout.SpecialCompleted01')
            ]
          )
        ],
        [
          {'name': 'KillSpeechMeleeFat', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # I broke your stupid crap moron! (Killed a building).
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
              ResponseLine('Scout.SpecialCompleted10')
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
