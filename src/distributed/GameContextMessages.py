"""GameContextMessages module: contains the GameContextMessages class."""

from tf.tfbase import TFLocalizer

class GameContextMessage:

    CTF_Enemy_PickedUp = 0
    CTF_Enemy_Dropped = 1
    CTF_Enemy_Captured = 2
    CTF_Enemy_Returned = 3
    CTF_Team_PickedUp = 4
    CTF_Team_Dropped = 5
    CTF_Team_Captured = 6
    CTF_Team_Returned = 7
    CTF_Player_PickedUp = 8

ContextMessages = {
  GameContextMessage.CTF_Enemy_PickedUp: TFLocalizer.TF_CTF_OtherTeamPickup,
  GameContextMessage.CTF_Enemy_Dropped: TFLocalizer.TF_CTF_OtherTeamDrop,
  GameContextMessage.CTF_Enemy_Captured: TFLocalizer.TF_CTF_OtherTeamCapture,
  GameContextMessage.CTF_Enemy_Returned: TFLocalizer.TF_CTF_OtherTeamReset,
  GameContextMessage.CTF_Team_PickedUp: TFLocalizer.TF_CTF_PlayerTeamPickup,
  GameContextMessage.CTF_Team_Dropped: TFLocalizer.TF_CTF_PlayerTeamDrop,
  GameContextMessage.CTF_Team_Captured: TFLocalizer.TF_CTF_PlayerTeamCapture,
  GameContextMessage.CTF_Team_Returned: TFLocalizer.TF_CTF_PlayerTeamReset,
  GameContextMessage.CTF_Player_PickedUp: TFLocalizer.TF_CTF_Wrong_Goal
}
