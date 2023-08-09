"""SpyResponses module: contains the SpyResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseSystem import Response, ResponseLine, Rule
from .ResponseSystemBase import *

# All classes share a lot of response rules but
# with lines specific to each class.  This simplifies things.
SpyBaseResponses = {
  'battle_cry': stringList('Spy.BattleCry', (1, 4)),
  'stalemate': stringList('Spy.AutoDejectedTie', (1, 3)),
  'capped_ctf': stringList('Spy.AutoCappedIntelligence', (1, 3)),
  'capped_cp': stringList('Spy.AutoCappedControlPoint', (1, 3)),
  'medic_call': stringList('Spy.Medic', (1, 3)),
  'medic_follow': stringList('Spy.MedicFollow', (1, 2)),
  'spy': stringList('Spy.CloakedSpy', (1, 4)),
  'spy_scout': ['Spy.CloakedSpyIdentify01'],
  'spy_soldier': ['Spy.CloakedSpyIdentify02'],
  'spy_pyro': ['Spy.CloakedSpyIdentify04'],
  'spy_demo': ['Spy.CloakedSpyIdentify05'],
  'spy_heavy': ['Spy.CloakedSpyIdentify03'],
  'spy_engineer': ['Spy.CloakedSpyIdentify09'],
  'spy_medic': ['Spy.CloakedSpyIdentify08'],
  'spy_sniper': ['Spy.CloakedSpyIdentify10'],
  'spy_spy': ['Spy.CloakedSpyIdentify06', 'Spy.CloakedSpyIdentify07'],
  'teleporter_thanks': stringList('Spy.ThanksForTheTeleporter', (1, 3)),
  'heal_thanks': stringList('Spy.ThanksForTheHeal', (1, 3)),
  'help_me': stringList('Spy.HelpMe', (1, 3)),
  'help_capture': stringList('Spy.HelpMeCapture', (1, 3)),
  'help_defend': stringList('Spy.HelpMeDefend', (1, 3)),
  'incoming': stringList('Spy.Incoming', (1, 3)),
  'good_job': stringList('Spy.GoodJob', (1, 3)),
  'nice_shot': stringList('Spy.NiceShot', (1, 3)),
  'cheers': stringList('Spy.Cheers', (1, 8)),
  'jeers': stringList('Spy.Jeers', (1, 6)),
  'positive': stringList('Spy.PositiveVocalization', (1, 5)),
  'negative': stringList('Spy.NegativeVocalization', (1, 9)),
  'need_sentry': ['Spy.NeedSentry01'],
  'need_dispenser': ['Spy.NeedDispenser01'],
  'need_teleporter': ['Spy.NeedTeleporter01'],
  'sentry_ahead': stringList('Spy.SentryAhead', (1, 2)),
  'activate_charge': stringList('Spy.ActivateCharge', (1, 3)),
  'yes': stringList('Spy.Yes', (1, 3)),
  'no': stringList('Spy.No', (1, 3)),
  'go': stringList('Spy.Go', (1, 3)),
  'move_up': stringList('Spy.MoveUp', (1, 2)),
  'go_left': stringList('Spy.HeadLeft', (1, 3)),
  'go_right': stringList('Spy.HeadRight', (1, 3)),
  'thanks': stringList('Spy.Thanks', (1, 3)),
  'assist_thanks': stringList('Spy.SpecialCompleted-AssistedKill', (1, 2)),
  'melee_dare': [
    'Spy.MeleeDare01', 'Spy.MeleeDare02',
    'Spy.SpecialCompleted09', 'Spy.Taunts01', 'Spy.Taunts10',
    'Spy.Taunts11', 'Spy.Taunts13'
  ],
  'revenge': [
    'Spy.PositiveVocalization01', 'Spy.Cheers01',
    'Spy.GoodJob01', 'Spy.PositiveVocalization04',
    'Spy.PositiveVocalization05', 'Spy.Revenge01',
    'Spy.Revenge02', 'Spy.Revenge03',
    'Spy.Taunts16'
  ],
  'domination_scout': stringList('Spy.DominationScout', (1, 8)),
  'domination_soldier': stringList('Spy.DominationSoldier', (1, 5)),
  'domination_pyro': stringList('Spy.DominationPyro', (1, 5)),
  'domination_demo': stringList('Spy.DominationDemoMan', (1, 7)),
  'domination_heavy': stringList('Spy.DominationHeavy', (1, 8)),
  'domination_engineer': stringList('Spy.DominationEngineer', (1, 6)),
  'domination_medic': stringList('Spy.DominationMedic', (1, 6)),
  'domination_sniper': stringList('Spy.DominationSniper', (1, 7)),
  'domination_spy': stringList('Spy.DominationSpy', (1, 5))
}

spyKilledPlayerManyLines = [
  'Spy.LaughEvil01', 'Spy.LaughEvil02', 'Spy.LaughHappy01',
  'Spy.LaughHappy02', 'Spy.LaughHappy03', 'Spy.LaughLong01',
  'Spy.LaughShort06', 'Spy.SpecialCompleted09',
  'Spy.SpecialCompleted10'
]
spyMeleeKillLines = [
  'Spy.SpecialCompleted11', 'Spy.SpecialCompleted02',
  'Spy.SpecialCompleted03'
]

def makeResponseSystem(player):
    system = makeBaseTFResponseSystem(player, SpyBaseResponses)

    # Killed multiple players with revolver
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          weaponIsSecondary, isManyRecentKills, percentChance30,
          notKillSpeech
        ],
        [
          Response(
            [
              ResponseLine(x) for x in spyKilledPlayerManyLines
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10}
        ]
      )
    )

    # Melee kill.
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
              ResponseLine(x) for x in spyMeleeKillLines
            ]
          )
        ],
        [
          {'name': 'KillSpeechMelee', 'value': 1, 'expireTime': 5}
        ]
      )
    )

    system.sortRules()
    return system
