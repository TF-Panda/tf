"""ResponseCriteria module: contains the ResponseCriteria class."""

import random

from tf.weapon.WeaponMode import TFWeaponType
from tf.player.TFClass import Class

def isARecentKill(data):
    return data['recentkills'] > 0

def isManyRecentKills(data):
    return data['recentkills'] > 1

def isVeryManyRecentKills(data):
    return data['recentkills'] > 3

def percentChance30(data):
    return random.random() <= 0.3

def percentChance50(data):
    return random.random() <= 0.5

def superHighHealthContext(data):
    return data['playerhealthfrac'] > 1.4

def weaponIsMelee(data):
    return data.get('withweapon') and data['withweapon'].weaponType == TFWeaponType.Melee

def isNotSentryKill(data):
    return not data['issentrykill']

def isSentryKill(data):
    return data['issentrykill']

def isRevengeKill(data):
    return data.get('isrevenge', False)

def isDominationKill(data):
    return data.get('isnemesis', False)

def isVictimScout(data):
    return data['killedplayer'].tfClass == Class.Scout

def isVictimSoldier(data):
    return data['killedplayer'].tfClass == Class.Soldier

def isVictimPyro(data):
    return data['killedplayer'].tfClass == Class.Pyro

def isVictimDemo(data):
    return data['killedplayer'].tfClass == Class.Demo

def isVictimHeavy(data):
    return data['killedplayer'].tfClass == Class.HWGuy

def isVictimEngineer(data):
    return data['killedplayer'].tfClass == Class.Engineer

def isVictimMedic(data):
    return data['killedplayer'].tfClass == Class.Medic

def isVictimSniper(data):
    return data['killedplayer'].tfClass == Class.Sniper

def isVictimSpy(data):
    return data['killedplayer'].tfClass == Class.Spy

def isHoveringPlayer(data):
    return data.get('crosshair_player') is not None

def isHoveringTeammate(data):
    return isHoveringPlayer(data) and data['crosshair_player'].team == data['player'].team

def isHoveringEnemy(data):
    return isHoveringPlayer(data) and data['crosshair_player'].team != data['player'].team

def isHoveringScout(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Scout

def isHoveringSoldier(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Soldier

def isHoveringPyro(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Pyro

def isHoveringDemo(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Demo

def isHoveringHeavy(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.HWGuy

def isHoveringEngineer(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Engineer

def isHoveringMedic(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Medic

def isHoveringSniper(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Sniper

def isHoveringSpy(data):
    return isHoveringPlayer(data) and data['crosshair_player'].tfClass == Class.Spy

def isZoomedIn(data):
    return data['player'].inCondition(data['player'].CondZoomed)
