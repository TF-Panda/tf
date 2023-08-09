"""DistributedTriggerHurt module: contains the DistributedTriggerHurt class."""

from tf.tfbase.TFGlobals import DamageType
from tf.weapon.TakeDamageInfo import TakeDamageInfo

from .DistributedTrigger import DistributedTrigger


class DistributedTriggerHurt(DistributedTrigger):

    if not IS_CLIENT:
        def onEntityStartTouch(self, entity):
            DistributedTrigger.onEntityStartTouch(self, entity)
            # It should already be an alive player.
            info = TakeDamageInfo()
            info.setDamage(entity.health)
            info.damageType = DamageType.Fall
            info.inflictor = base.world
            info.attacker = base.world
            entity.takeDamage(info)

if not IS_CLIENT:
    DistributedTriggerHurtAI = DistributedTriggerHurt
    DistributedTriggerHurtAI.__name__ = 'DistributedTriggerHurtAI'
