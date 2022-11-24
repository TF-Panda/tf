""" TFLocalizerFrench: French localization """

### Startup ###

# Legal Disclaimer
TFDisclaimer = 'Team Fortress and the Team Fortress logo are registered trademarks of Valve Corporation.  ' \
               'Team Fortress 2 Panda is not affiliated with Valve Corporation.  ' \
               'Team Fortress 2 Panda runs on a modified version of the Panda3D game engine.  ' \
               'Panda3D is Copyright (c) Carnegie Mellon University.  ' \
               'FMOD Studio is Copyright (c) Firelight Technologies Pty Ltd.'

Loading = "Loading..."
MainMenuStartPlaying = 'Start Playing'

Quit = 'Quit'
Retry = 'Retry'
Cancel = 'Cancel'
OK = 'OK'
Yes = 'Yes'
No = 'No'

ConnectingToServer = 'Connecting to %s...'
ConnectionFailed = 'Failed to connect to %s.'
Authenticating = 'Authenticating...'
JoiningGame = 'Joining game...'
LostConnection = 'Your internet connection to the servers has been unexpectedly broken.'

### Debug ###

ConsolePRCData = "Enter PRC data"

#### Team Selection ###

ChooseAClass = "Select a Class"
ChooseATeam = "Select a Team"

### Player Names ###

Scout = 'Scout'
Soldier = 'Soldier'
Pyro = 'Pyro'
Demoman = 'Demoman'
Heavy = 'Heavy'
Engineer = 'Engineer'
Medic = 'Medic'
Sniper = 'Sniper'
Spy = 'Spy'

### Player Weapons ###

# Engineer Weapons
SentryGun = 'Sentry Gun'
Dispenser = 'Dispenser'
Teleporter = 'Teleporter'
Wrench = 'Wrench'
Pistol = 'Pistol'
#Shotgun = 'Shotgun'
ConstructionPDA = 'Construction PDA'
DestructionPDA = 'Destruction PDA'
# Shared
Toolbox = 'Toolbox'
Object = 'Object'
ObjectNotBuilt = '%s not built'
ObjectAlreadyBuilt = "Already Built"
NotBuilt = 'Not Built'
BUILD = "BUILD"
Building = 'Building...'
NotEnoughMetal = "Not Enough Metal"
BuiltBy = " built by "
Metal = "\nMetal: %i"
RequiredMetal = "%i Metal"
MetalHUD = "Metal"
StickiesHUD = "Stickies"
# Sentry
Shells = 'Shells'
Rockets = 'Rockets'
Upgrade = 'Upgrade'
SentryKillsText = 'Kills: %i (%i)'
Level = "\nLevel %i"
UpgradeProgress = "\nUpgrade progress: %i / %i"
# Teleporter
Entrance = 'Entrance'
Exit = 'Exit'
TeleporterEntrance = 'Teleporter Entrance'
TeleporterExit = 'Teleporter Exit'
TeleporterSending = "\nSending..."
TeleporterReceiving = "\nReceiving..."

# Soldier Weapons
RocketLauncher = 'Rocket Launcher'
Shovel = 'Shovel'
#Shotgun = 'Shotgun'

# Heavy Weapons
Minigun = 'Minigun'
Fists = 'Fists'
Shotgun = 'Shotgun'

# Medic Weapons
MediGun = 'Medigun'
BoneSaw = 'Bone Saw'
SyringeGun = 'Syringe Gun'
Healer = "Healer: "
Healing = "Healing: "

# Spy Weapons
Revolver = 'Revolver'
InvisWatch = 'Invis Watch'
DiguiseKit = 'DisguiseKit'
Knife = 'Knife'

# Pyro Weapons
FlameThrower = 'Flame Thrower'
FireAxe = 'Fire Axe'
#Shotgun = 'Shotgun'

# Demoman Weapons
Bottle = 'Bottle'
StickyBombLauncher = 'Sticky Bomb Launcher'
GrenadeLauncher = 'Grenade Launcher'

# Sniper Weapons
SniperRifle = 'Sniper Rifle'
SMG = 'SMG'
Kukri = 'Kukri'

# Scout Weapons
Bat = 'Bat'
ScatterGun = 'Scattergun'
#Shotgun = 'Shotgun'

### RED vs BLU ###

RED = 'RED'
BLU = 'BLU'

### Kill Screen ###

RespawnIn = "Respawn in: "
RespawnWaitNewRound = "Wait for new round"
RespawnWait = "Prepare to respawn"
RespawnSeconds = " seconds"
YouWereKilledBy = "You were killed by "
YouWereKilledByNemesis = "You were killed again by "
YouWereKilledByThe = "You were killed by the "
YouWereKilledByTheNemesis = "You were killed again by the "
KillerLate = "late "
KillerSentryGun = "Sentry Gun of "
KillerTheLate = "the late "
PlayerFinishedOff = "\2 finished off "
PlayerKilled = " killed "
PlayerSwitchTeam = "\2 bid farewell, cruel world!"
PlayerKillHealth = "\2 fell to a clumsy, painful death"
Dead = "Dead"
PlayerIsDominating = "%s is DOMINATING %s"
PlayerGotRevenge = "%s got REVENGE on %s"
NemesisText = "NEMESIS!"

### Shared Between Kill Screen, Engineer panel, Medic Panel ###

HealthOutOf = "Health: %i / %i"
PressKey = "Press %s"
AmmoOutOf = "\nAmmo: %i / %i"
Ammo = "\nAmmo: %i"
Charge = "\nCharge: "
ChargeFull = "\nCharge: 100%"

### Capture the Flag ###
# Pickup
TF_CTF_PlayerPickup = "You PICKED UP the ENEMY INTELLIGENCE!\n\nReturn to BASE!"
TF_CTF_PlayerTeamPickup = "Your team PICKED UP the ENEMY INTELLIGENCE!"
TF_CTF_OtherTeamPickup = "Your INTELLIGENCE has been PICKED UP!"
# Capture
TF_CTF_PlayerCapture = "You CAPTURED the ENEMY INTELLIGENCE!"
TF_CTF_PlayerTeamCapture = "Your team CAPTURED the ENEMY INTELLIGENCE!"
TF_CTF_OtherTeamCapture = "Your INTELLIGENCE was CAPTURED!"
# Drop
TF_CTF_PlayerDrop = "You dropped the ENEMY INTELLIGENCE!"
TF_CTF_PlayerTeamDrop = "The ENEMY INTELLIGENCE was dropped!"
TF_CTF_OtherTeamDrop = "Your INTELLIGENCE has been dropped!"
# Reset
TF_CTF_PlayerTeamReset = "Your INTELLIGENCE has been returned!"
TF_CTF_OtherTeamReset = "The ENEMY INTELLIGENCE was returned!"
TF_CTF_Wrong_Goal = "Take the INTELLIGENCE back to YOUR BASE."
# Specials
TF_CTF_No_Invuln = "You cannot be INVULNERABLE while carrying the ENEMY INTELLIGENCE!"
TF_CTF_No_Tele = "You cannot TELEPORT while carrying the ENEMY INTELLIGENCE!"
# Intelligence is missing
TF_CTF_Cannot_Capture = "Cannot capture - your flag is not at base!"

# Voice commands
#
# Menu 1 (z)
VoiceCommandMedic = "MEDIC!"
VoiceCommandThanks = "Thanks!"
VoiceCommandGoGoGo = "Go Go Go!"
VoiceCommandMoveUp = "Move Up!"
VoiceCommandGoLeft = "Go Left"
VoiceCommandGoRight = "Go Right"
VoiceCommandYes = "Yes"
VoiceCommandNo = "No"
# Menu 2 (x)
VoiceCommandIncoming = "Incoming!"
VoiceCommandSpy = "Spy!"
VoiceCommandSentryAhead = "Sentry Ahead!"
VoiceCommandTeleporterHere = "Teleporter Here"
VoiceCommandDispenserHere = "Dispenser Here"
VoiceCommandSentryHere = "Sentry Here"
VoiceCommandActivateCharge = "Activate ÜberCharge!"
VoiceCommandUberChargeReady = "MEDIC: ÜberCharge Ready"
# Menu 3 (c)
VoiceCommandHelp = "Help!"
VoiceCommandBattleCry = "Battle Cry"
VoiceCommandCheers = "Cheers"
VoiceCommandJeers = "Jeers"
VoiceCommandPositive = "Positive"
VoiceCommandNegative = "Negative"
VoiceCommandNiceShot = "Nice Shot"
VoiceCommandGoodJob = "Good Job"

ChatDeadPrefix = "*DEAD*"
ChatVoicePrefix = "(Voice)"
ChatTeamPrefix = "(Team)"
ChatJoinedGame = "%s has joined the game."
ChatLeftGame = "%s left the game."
ChatJoinedTeam = "%s joined team %s."
ChatJoinedTeamAuto = "%s was automatically assigned to team %s."
ChatYouWillRespawnAs = "*You will spawn as %s."
ChatCannotChangeClass = "You can't change class at this time."
ChatCannotChangeTeam = "You can't change team at this time."
