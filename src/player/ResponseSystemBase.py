"""ResponseSystemBase module: contains the ResponseSystemBase class."""

from tf.tfbase.TFGlobals import SpeechConcept

from .ResponseCriteria import *
from .ResponseSystem import Response, ResponseLine, ResponseSystem, Rule


def stringList(baseStr, ranges):
  strings = []
  if isinstance(ranges[0], (tuple, list)):
    for r in ranges:
      for i in range(r[0], r[1] + 1):
        strings.append(baseStr + str(i).zfill(2))
  else:
    for i in range(ranges[0], ranges[1] + 1):
      strings.append(baseStr + str(i).zfill(2))

  return strings

def makeBaseTFResponseSystem(player, baseDef):
  system = ResponseSystem(player)

  if 'battle_cry' in baseDef:
    system.addRule(
      SpeechConcept.RoundStart,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x, preDelay=(1, 5)) for x in baseDef['battle_cry']
            ]
          )
        ]
      )
    )

    system.addRule(
      SpeechConcept.BattleCry,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['battle_cry']
            ]
          )
        ]
      )
    )

  if 'melee_dare' in baseDef:
    system.addRule(
      SpeechConcept.BattleCry,
      Rule(
        [
          isHoveringEnemy, isActiveWeaponMelee
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['melee_dare']
            ]
          )
        ]
      )
    )

  if 'stalemate' in baseDef:
    system.addRule(
      SpeechConcept.RoundEnd,
      Rule(
        [
          lambda data: data['isstalemate']
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['stalemate']
            ]
          )
        ]
      )
    )

  if 'capped_ctf' in baseDef:
    system.addRule(
      SpeechConcept.CappedObjective,
      Rule(
        [
          lambda data: data['gamemode'] == 'ctf'
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['capped_ctf']
            ]
          )
        ]
      )
    )

  if 'capped_cp' in baseDef:
    system.addRule(
      SpeechConcept.CappedObjective,
      Rule(
        [
          lambda data: data['gamemode'] == 'cp'
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['capped_cp']
            ]
          )
        ]
      )
    )

  if 'medic_call' in baseDef:
    # Generic medic call
    system.addRule(
      SpeechConcept.MedicCall,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['medic_call']
            ]
          )
        ]
      )
    )

  if 'medic_follow' in baseDef:
    # Medic call when hovering over friendly medic.
    system.addRule(
      SpeechConcept.MedicCall,
      Rule(
        [
          isHoveringTeammate, isHoveringMedic,
          lambda data: data['playerhealthfrac'] > 0.5
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=0.25) for x in baseDef['medic_follow']
            ]
          )
        ]
      )
    )

  if 'spy' in baseDef:
    # Spy identify, generic.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['spy']
            ]
          )
        ]
      )
    )
  if 'spy_scout' in baseDef:
    # Identify spy as scout.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringScout
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_scout']
            ]
          )
        ]
      )
    )
  if 'spy_soldier' in baseDef:
    # Identify spy as soldier.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringSoldier
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_soldier']
            ]
          )
        ]
      )
    )
  if 'spy_heavy' in baseDef:
    # Identify spy as heavy.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringHeavy
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_heavy']
            ]
          )
        ]
      )
    )
  if 'spy_pyro' in baseDef:
    # Identify spy as pyro.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringPyro
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_pyro']
            ]
          )
        ]
      )
    )
  if 'spy_demo' in baseDef:
    # Identify spy as demoman.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringDemo
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_demo']
            ]
          )
        ]
      )
    )
  if 'spy_spy' in baseDef:
    # Identify spy as spy.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringSpy
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_spy']
            ]
          )
        ]
      )
    )
  if 'spy_medic' in baseDef:
    # Identify spy as medic.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringMedic
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_medic']
            ]
          )
        ]
      )
    )
  if 'spy_engineer' in baseDef:
    # Identify spy as engineer.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringEngineer
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_engineer']
            ]
          )
        ]
      )
    )
  if 'spy_sniper' in baseDef:
    # Identify spy as sniper.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        [
          isHoveringSniper
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['spy_sniper']
            ]
          )
        ]
      )
    )

  if 'teleporter_thanks' in baseDef:
    system.addRule(
      SpeechConcept.Teleported,
      Rule(
        [
          percentChance30
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['teleporter_thanks']
            ]
          )
        ]
      )
    )
  if 'heal_thanks' in baseDef:
    system.addRule(
      SpeechConcept.StoppedBeingHealed,
      Rule(
        [
          percentChance50, superHighHealthContext,
          lambda data: not data.get("SaidHealThanks")
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['heal_thanks']
            ]
          )
        ],
        [
          {'name': 'SaidHealThanks', 'value': 1, 'expireTime': 20}
        ]
      )
    )
  if 'thanks' in baseDef:
    system.addRule(
      SpeechConcept.Thanks,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['thanks']
            ]
          )
        ]
      )
    )
  if 'assist_thanks' in baseDef:
    # Thanks for assist, if we have a recent kill and haven't said
    # thanks for assist recently.
    system.addRule(
      SpeechConcept.Thanks,
      Rule(
        [
          isARecentKill,
          lambda data: not data.get("AssistSpeech")
        ],
        [
          Response(
            [
              ResponseLine(x) for x in baseDef['assist_thanks']
            ]
          )
        ],
        [
          {'name': 'AssistSpeech', 'value': 1, 'expireTime': 20}
        ]
      )
    )

  if 'help_me' in baseDef:
    system.addRule(
      SpeechConcept.HelpMe,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['help_me']
            ]
          )
        ]
      )
    )

  if 'incoming' in baseDef:
    system.addRule(
      SpeechConcept.Incoming,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['incoming']
            ]
          )
        ]
      )
    )

  if 'good_job' in baseDef:
    system.addRule(
      SpeechConcept.GoodJob,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['good_job']
            ]
          )
        ]
      )
    )

  if 'nice_shot' in baseDef:
    system.addRule(
      SpeechConcept.NiceShot,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['nice_shot']
            ]
          )
        ]
      )
    )

  if 'cheers' in baseDef:
    system.addRule(
      SpeechConcept.Cheers,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['cheers']
            ]
          )
        ]
      )
    )

  if 'positive' in baseDef:
    system.addRule(
      SpeechConcept.Positive,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['positive']
            ]
          )
        ]
      )
    )

  if 'jeers' in baseDef:
    system.addRule(
      SpeechConcept.Jeers,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['jeers']
            ]
          )
        ]
      )
    )

  if 'negative' in baseDef:
    system.addRule(
      SpeechConcept.Negative,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['negative']
            ]
          )
        ]
      )
    )

  if 'need_sentry' in baseDef:
    system.addRule(
      SpeechConcept.SentryHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['need_sentry']
            ]
          )
        ]
      )
    )
  if 'need_dispenser' in baseDef:
    system.addRule(
      SpeechConcept.DispenserHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['need_dispenser']
            ]
          )
        ]
      )
    )
  if 'need_teleporter' in baseDef:
    system.addRule(
      SpeechConcept.TeleporterHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['need_teleporter']
            ]
          )
        ]
      )
    )

  if 'sentry_ahead' in baseDef:
    system.addRule(
      SpeechConcept.SentryAhead,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['sentry_ahead']
            ]
          )
        ]
      )
    )

  if 'activate_charge' in baseDef:
    system.addRule(
      SpeechConcept.ActivateCharge,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['activate_charge']
            ]
          )
        ]
      )
    )

  if 'yes' in baseDef:
    system.addRule(
      SpeechConcept.Yes,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['yes']
            ]
          )
        ]
      )
    )

  if 'no' in baseDef:
    system.addRule(
      SpeechConcept.No,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['no']
            ]
          )
        ]
      )
    )

  if 'go' in baseDef:
    system.addRule(
      SpeechConcept.Go,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['go']
            ]
          )
        ]
      )
    )

  if 'move_up' in baseDef:
    system.addRule(
      SpeechConcept.MoveUp,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['move_up']
            ]
          )
        ]
      )
    )

  if 'go_left' in baseDef:
    system.addRule(
      SpeechConcept.GoLeft,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['go_left']
            ]
          )
        ]
      )
    )

  if 'go_right' in baseDef:
    system.addRule(
      SpeechConcept.GoRight,
      Rule(
        responses=[
          Response(
            [
              ResponseLine(x) for x in baseDef['go_right']
            ]
          )
        ]
      )
    )

  if 'domination' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_scout' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimScout
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_scout']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_soldier' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSoldier
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_soldier']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_pyro' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimPyro
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_pyro']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_demo' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimDemo
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_demo']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_heavy' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimHeavy
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_heavy']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_engineer' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimEngineer
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_engineer']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_medic' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimMedic
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_medic']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_sniper' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSniper
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_sniper']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'domination_spy' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isDominationKill, isVictimSpy
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['domination_spy']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )
  if 'revenge' in baseDef:
    system.addRule(
      SpeechConcept.KilledPlayer,
      Rule(
        [
          isRevengeKill
        ],
        [
          Response(
            [
              ResponseLine(x, preDelay=2.5) for x in baseDef['revenge']
            ]
          )
        ],
        [
          {'name': 'KillSpeech', 'value': 1, 'expireTime': 10},
          {'name': 'IsDominating', 'value': 1, 'expireTime': 10}
        ]
      )
    )

  return system
