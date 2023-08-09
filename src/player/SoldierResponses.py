"""SoldierResponses module: contains the SoldierResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Response, ResponseLine, Rule
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
SoldierBaseResponses = {
  'battle_cry': stringList('Soldier.BattleCry', (1, 6)),
  'stalemate': stringList('Soldier.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Soldier.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Soldier.AutoCappedControlPoint', (1, 3)),
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
  'assist_thanks': ['Soldier.SpecialCompleted-AssistedKill01'],
  'melee_dare': [
    'Soldier.Taunts03', 'Soldier.Taunts08', 'Soldier.Taunts14',
    'Soldier.Taunts16', 'Soldier.Taunts19', 'Soldier.Taunts20'
  ],
  'revenge': [
    'Soldier.BattleCry06', 'Soldier.Cheers01', 'Soldier.GoodJob02'
  ],
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

soldierMeleeKillLines = [
  'Soldier.SpecialCompleted05', 'Soldier.DirectHitTaunt01',
  'Soldier.DirectHitTaunt02', 'Soldier.DirectHitTaunt03',
  'Soldier.DirectHitTaunt04'
]
soldierDestroyBuildingLines = [
  'Soldier.BattleCry01', 'Soldier.BattleCry02',
  'Soldier.SpecialCompleted04', 'Soldier.PositiveVocalization02',
  'Soldier.PositiveVocalization01'
]
soldierKilledPlayerManyLines = [
  'Soldier.SpecialCompleted03', 'Soldier.Taunts01',
  'Soldier.Taunts09', 'Soldier.Taunts10'
]
soldierKilledPlayerVeryManyLines = [
  'Soldier.Taunts02', 'Soldier.Taunts17'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SoldierBaseResponses)
    # Killed multiple players recently with primary weapon.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsPrimary, percentChance30, isManyRecentKills, notKillSpeech
        ],
        [
          Response(
            [
              ResponseLine(x) for x in soldierKilledPlayerManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Killed more than 3 players recently with primary.
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsPrimary, percentChance50, isVeryManyRecentKills,
          notKillSpeech
        ],
        [
          Response(
            [
              ResponseLine(x) for x in soldierKilledPlayerVeryManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Melee kill speech.
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
              ResponseLine(x) for x in soldierMeleeKillLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechMelee', 'value': 1, 'expireTime': 10}
        ]
      )
    )
    # Destroying engineer buildings.
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
              ResponseLine(x) for x in soldierDestroyBuildingLines
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
