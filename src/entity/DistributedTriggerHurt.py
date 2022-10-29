"""DistributedTriggerHurt module: contains the DistributedTriggerHurt class."""

from .DistributedTrigger import DistributedTrigger

from tf.tfbase.TFGlobals import DamageType
from tf.weapon.TakeDamageInfo import TakeDamageInfo

class DistributedTriggerHurt(DistributedTrigger):

    if not IS_CLIENT:
        def onTriggerEnter(self, entity):
            if not self.triggerEnabled:
                return
            DistributedTrigger.onTriggerEnter(self, entity)
            if not entity.isDead():
                info = TakeDamageInfo()
                info.setDamage(entity.health)
                info.damageType = DamageType.Fall
                info.inflictor = base.world
                info.attacker = base.world
                entity.takeDamage(info)

if not IS_CLIENT:
    DistributedTriggerHurtAI = DistributedTriggerHurt
    DistributedTriggerHurtAI.__name__ = 'DistributedTriggerHurtAI'
