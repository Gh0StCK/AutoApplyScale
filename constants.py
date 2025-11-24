from typing import Set, Dict, List, Optional, Tuple
from mathutils import Vector

# Типы объектов
OBJECT_TYPES = [
    ('MESH', "Mesh", "Полигональные объекты"),
    ('CURVE', "Curve", "Кривые"),
    ('SURFACE', "Surface", "Поверхности"),
    ('META', "Metaball", "Мета-объекты"),
    ('ARMATURE', "Armature", "Арматуры"),
    ('LATTICE', "Lattice", "Решетки"),
    ('EMPTY', "Empty", "Пустые объекты")
]

# Типы трансформаций
TRANSFORM_TYPES = ('scale',)

# Глобальные переменные
auto_apply_scale_running = False 