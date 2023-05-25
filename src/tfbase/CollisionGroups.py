"""CollisionGroups module: contains the CollisionGroups class."""

World = 1 << 0
Sky = 1 << 1
PlayerClip = 1 << 2
RedPlayer = 1 << 3
RedBuilding = 1 << 4
BluePlayer = 1 << 5
BlueBuilding = 1 << 6
Projectile = 1 << 7
HitBox = 1 << 8
# Gibs, weapon drops, etc.
Debris = 1 << 9
Trigger = 1 << 10
# Special bit for teleporters because all players collide
# with teleporters on both teams.
Teleporter = 1 << 11

Mask_Player = RedPlayer | BluePlayer
Mask_Building = RedBuilding | BlueBuilding | Teleporter
Mask_Red = RedPlayer | RedBuilding | Teleporter
Mask_Blue = BluePlayer | BlueBuilding | Teleporter
Mask_AllTeam = Mask_Player | Mask_Building

# What bullets collide with.
Mask_BulletCollide = Mask_AllTeam | World | HitBox | Projectile | Debris

# What debris collides with.
Mask_DebrisCollide = World
