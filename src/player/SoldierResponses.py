"""SoldierResponses module: contains the SoldierResponses class."""

from tf.tfbase.TFGlobals import SpeechConcept
from tf.player.TFClass import Class
import random

from .ResponseSystem import ResponseSystem, Rule, Response, ResponseLine

def makeResponseSystem(player):
    system = ResponseSystem(player)

    system.addRule(
      SpeechConcept.RoundStart,
      Rule(
        responses=[
          Response(
            [
              ResponseLine("Soldier.BattleCry01", preDelay=(1, 5)),
              ResponseLine("Soldier.BattleCry02", preDelay=(1, 5)),
              ResponseLine("Soldier.BattleCry03", preDelay=(1, 5)),
              ResponseLine("Soldier.BattleCry04", preDelay=(1, 5)),
              ResponseLine("Soldier.BattleCry05", preDelay=(1, 5)),
              ResponseLine("Soldier.BattleCry06", preDelay=(1, 5))
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
              ResponseLine("Soldier.AutoDejectedTie01"),
              ResponseLine("Soldier.AutoDejectedTie02"),
              ResponseLine("Soldier.AutoDejectedTie03"),
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
              ResponseLine("Soldier.AutoCappedIntelligence01"),
              ResponseLine("Soldier.AutoCappedIntelligence02"),
              ResponseLine("Soldier.AutoCappedIntelligence03")
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
              ResponseLine("Soldier.Medic01"),
              ResponseLine("Soldier.Medic02"),
              ResponseLine("Soldier.Medic03")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].team == data['player'].team,
          lambda data: data['crosshair_player'].tfClass == Class.Medic,
          lambda data: data['playerhealthfrac'] > 0.5
        ],
        [
          Response(
            [
              ResponseLine("Soldier.PickAxeTaunt01", preDelay=0.25),
              ResponseLine("Soldier.PickAxeTaunt02", preDelay=0.25),
              ResponseLine("Soldier.PickAxeTaunt03", preDelay=0.25),
              ResponseLine("Soldier.PickAxeTaunt04", preDelay=0.25),
              ResponseLine("Soldier.PickAxeTaunt05", preDelay=0.25)
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
              ResponseLine("Soldier.CloakedSpy01"),
              ResponseLine("Soldier.CloakedSpy02"),
              ResponseLine("Soldier.CloakedSpy03")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Scout
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify01")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Soldier
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify02")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.HWGuy
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify03")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Pyro
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify04")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Demo
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify05")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Spy
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify09")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Medic
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify06")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Engineer
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify07")
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
          lambda data: data['crosshair_player'] is not None,
          lambda data: data['crosshair_player'].tfClass == Class.Sniper
        ],
        [
          Response(
            [
              ResponseLine("Soldier.CloakedSpyIdentify08")
            ]
          )
        ]
      )
    )

    system.sortRules()

    return system
