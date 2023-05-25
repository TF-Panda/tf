"""ObjectDefs module: contains the ObjectDefs class."""

from panda3d.core import Vec3

from .ObjectType import ObjectType

ObjectDefs = {
    ObjectType.SentryGun:
    {
        "buildhull": (Vec3(-17, -23, 0), Vec3(17, 20, 45)),
        "cost": 130,
        "blueprint": "models/buildables/sentry1_blueprint",
        "entity": "tf_obj_sentrygun",
        "objecttype": "sentry",
        "name": "#SentryGun"
    },

    ObjectType.Dispenser:
    {
        "buildhull": (Vec3(-26, -15, 0), Vec3(26, 15, 56)),
        "cost": 100,
        "blueprint": "models/buildables/dispenser_blueprint",
        "entity": "tf_obj_dispenser",
        "objecttype": "dispenser",
        "name": "#Dispenser"
    },

    ObjectType.TeleporterEntrance:
    {
        "buildhull": (Vec3(-25.5, -15, 0), Vec3(25.5, 15, 18)),
        "cost": 50,
        "blueprint": "models/buildables/teleporter_blueprint_enter",
        "entity": "tf_obj_teleporter_entrance",
        "objecttype": "teleporter",
        "name": "#Entrance"
    },

    ObjectType.TeleporterExit:
    {
        "buildhull": (Vec3(-25.5, -15, 0), Vec3(25.5, 15, 18)),
        "cost": 50,
        "blueprint": "models/buildables/teleporter_blueprint_exit",
        "entity": "tf_obj_teleporter_exit",
        "objecttype": "teleporter",
        "name": "#Exit"
    }
}
