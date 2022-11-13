"""EngineerResponses module: contains the EngineerResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine
from .ResponseCriteria import *

def makeResponseSystem(player):
    system = ResponseSystem(player)

    system.addRule(
      SpeechConcept.RoundStart,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.BattleCry01", preDelay=(1, 5)),
              ResponseLine("Engineer.BattleCry03", preDelay=(1, 5)),
              ResponseLine("Engineer.BattleCry04", preDelay=(1, 5)),
              ResponseLine("Engineer.BattleCry05", preDelay=(1, 5)),
              ResponseLine("Engineer.BattleCry06", preDelay=(1, 5)),
              ResponseLine("Engineer.BattleCry07", preDelay=(1, 5))
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.RoundEnd,
      Rule(
        [
          lambda data: data['isstalemate']
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoDejectedTie01"),
              ResponseLine("Engineer.AutoDejectedTie02"),
              ResponseLine("Engineer.AutoDejectedTie03"),
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.CappedObjective,
      Rule(
        [
          lambda data: data['gamemode'] == 'ctf'
        ],
        [
          Response(
            [
              ResponseLine("Engineer.AutoCappedIntelligence01"),
              ResponseLine("Engineer.AutoCappedIntelligence02"),
              ResponseLine("Engineer.AutoCappedIntelligence03")
            ]
          )
        ]
      )
    )

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
    # Generic medic call
    system.addRule(
      SpeechConcept.MedicCall,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Medic01"),
              ResponseLine("Engineer.Medic02"),
              ResponseLine("Engineer.Medic03")
            ]
          )
        ]
      )
    )
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
              ResponseLine("engineer_medicfollow01", preDelay=0.25),
              ResponseLine("engineer_medicfollow02", preDelay=0.25),
              ResponseLine("engineer_medicfollow03", preDelay=0.25)
            ]
          )
        ]
      )
    )

    # Spy identify, generic.
    system.addRule(
      SpeechConcept.SpyIdentify,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.CloakedSpy01"),
              ResponseLine("Engineer.CloakedSpy02"),
              ResponseLine("Engineer.CloakedSpy03")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify01")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify02")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify03")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify04")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify05")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify06"),
              ResponseLine("Engineer.CloakedSpyIdentify10")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify07")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify08")
            ]
          )
        ]
      )
    )
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
              ResponseLine("Engineer.CloakedSpyIdentify09")
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

    system.addRule(
      SpeechConcept.Teleported,
      Rule(
        [
          percentChance30
        ],
        [
          Response(
            [
              ResponseLine("Engineer.ThanksForTheTeleporter01"),
              ResponseLine("Engineer.ThanksForTheTeleporter02")
            ]
          )
        ]
      )
    )

    system.addRule(
      SpeechConcept.StoppedBeingHealed,
      Rule(
        [
          percentChance50, superHighHealthContext,
          lambda data: not data.get("EngineerSaidHealThanks")
        ],
        [
          Response(
            [
              ResponseLine("Engineer.ThanksForTheHeal01"),
              ResponseLine("Engineer.ThanksForTheHeal02")
            ]
          )
        ],
        [
          {'name': 'EngineerSaidHealThanks', 'value': 1, 'expireTime': 20}
        ]
      )
    )

    system.addRule(
      SpeechConcept.Thanks,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Thanks01")
            ]
          )
        ]
      )
    )
    # Thanks for assist, if we have a recent kill and haven't said
    # thanks for assist recently.
    system.addRule(
      SpeechConcept.Thanks,
      Rule(
        [
          isARecentKill,
          lambda data: not data.get("EngineerAssistSpeech")
        ],
        [
          Response(
            [
              ResponseLine("Engineer.SpecialCompleted-AssistedKill01"),
              ResponseLine("Engineer.SpecialCompleted-AssistedKill02")
            ]
          )
        ],
        [
          {'name': 'EngineerAssistSpeech', 'value': 1, 'expireTime': 20}
        ]
      )
    )

    system.addRule(
      SpeechConcept.HelpMe,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.HelpMe01"),
              ResponseLine("Engineer.HelpMe02"),
              ResponseLine("Engineer.HelpMe03")
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
              ResponseLine("Engineer.BattleCry01"),
              ResponseLine("Engineer.BattleCry03"),
              ResponseLine("Engineer.BattleCry04"),
              ResponseLine("Engineer.BattleCry05"),
              ResponseLine("Engineer.BattleCry06"),
              ResponseLine("Engineer.BattleCry07")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Incoming,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Incoming01"),
              ResponseLine("Engineer.Incoming02"),
              ResponseLine("Engineer.Incoming03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.GoodJob,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.GoodJob01"),
              ResponseLine("Engineer.GoodJob02"),
              ResponseLine("Engineer.GoodJob03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.NiceShot,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.NiceShot01"),
              ResponseLine("Engineer.NiceShot02"),
              ResponseLine("Engineer.NiceShot03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Cheers,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Cheers01"),
              ResponseLine("Engineer.Cheers02"),
              ResponseLine("Engineer.Cheers03"),
              ResponseLine("Engineer.Cheers04"),
              ResponseLine("Engineer.Cheers05"),
              ResponseLine("Engineer.Cheers06"),
              ResponseLine("Engineer.Cheers07")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Positive,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.PositiveVocalization01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Jeers,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Jeers01"),
              ResponseLine("Engineer.Jeers02"),
              ResponseLine("Engineer.Jeers03"),
              ResponseLine("Engineer.Jeers04")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Negative,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.NegativeVocalization01"),
              ResponseLine("Engineer.NegativeVocalization02"),
              ResponseLine("Engineer.NegativeVocalization03"),
              ResponseLine("Engineer.NegativeVocalization04"),
              ResponseLine("Engineer.NegativeVocalization05"),
              ResponseLine("Engineer.NegativeVocalization06"),
              ResponseLine("Engineer.NegativeVocalization07"),
              ResponseLine("Engineer.NegativeVocalization08"),
              ResponseLine("Engineer.NegativeVocalization09"),
              ResponseLine("Engineer.NegativeVocalization10"),
              ResponseLine("Engineer.NegativeVocalization11"),
              ResponseLine("Engineer.NegativeVocalization12")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.SentryHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.NeedSentry01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.DispenserHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.NeedDispenser01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.TeleporterHere,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.NeedTeleporter01"),
              ResponseLine("Engineer.NeedTeleporter02")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.SentryAhead,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.SentryAhead01"),
              ResponseLine("Engineer.SentryAhead02")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.ActivateCharge,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.ActivateCharge01"),
              ResponseLine("Engineer.ActivateCharge02"),
              ResponseLine("Engineer.ActivateCharge03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Yes,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Yes01"),
              ResponseLine("Engineer.Yes02"),
              ResponseLine("Engineer.Yes03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.No,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.No01"),
              ResponseLine("Engineer.No02"),
              ResponseLine("Engineer.No03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.Go,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.Go01"),
              ResponseLine("Engineer.Go02"),
              ResponseLine("Engineer.Go03")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.MoveUp,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.MoveUp01")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.GoLeft,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.HeadLeft01"),
              ResponseLine("Engineer.HeadLeft02")
            ]
          )
        ]
      )
    )
    system.addRule(
      SpeechConcept.GoRight,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Engineer.HeadRight01"),
              ResponseLine("Engineer.HeadRight02"),
              ResponseLine("Engineer.HeadRight03")
            ]
          )
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
