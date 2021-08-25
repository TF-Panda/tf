if IS_CLIENT:
    from tf.character.DistributedChar import DistributedChar
    BaseClass = DistributedChar
else:
    from tf.character.DistributedCharAI import DistributedCharAI
    BaseClass = DistributedCharAI

from panda3d.core import Vec3

from tf.tfbase.TFGlobals import Contents, SolidFlag, SolidShape
from tf.weapon.TakeDamageInfo import TakeDamageInfo, applyMultiDamage

class ProjectileBase(BaseClass):

    def __init__(self):
        BaseClass.__init__(self)

        self.initialVel = Vec3()
        self.critical = False
        if IS_CLIENT:
            self.spawnTime = 0.0
        else:
            self.damage = 0.0
            self.scorer = -1
            self.solidMask = Contents.Solid | Contents.HitBox | Contents.AnyTeam
            self.solidFlags = SolidFlag.Trigger
            self.solidShape = SolidShape.Box
            self.triggerCallback = True

    if not IS_CLIENT:
        def onTriggerEnter(self, ent):


if not IS_CLIENT:
    ProjectileBaseAI = ProjectileBase
    ProjectileBaseAI.__name__ = 'ProjectileBaseAI'
