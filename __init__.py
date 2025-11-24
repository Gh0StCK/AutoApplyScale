# Этот файл нужен для обозначения директории как Python-пакета

bl_info = {
    "name": "Auto Apply Scale",
    "blender": (4, 3, 2),
    "category": "Object",
    "author": "Stanislav Kolesnikov",
    "version": (1, 5, 1),
    "description": "Автоматически применяет масштаб объектов после подтверждения. Работает только в Object Mode.",
    "location": "View 3D > Sidebar > FastTools",
}

import bpy

# Импортируем модули с помощью полных путей
if "operators" in locals():
    import importlib
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(utils)
    importlib.reload(constants)
else:
    from . import operators
    from . import panels
    from . import utils
    from . import constants

from .constants import OBJECT_TYPES
from .utils import logger

classes = [
    operators.AutoApplyScaleOperator,
    operators.AutoApplySelectCategoryOperator,
    operators.AutoApplyDeselectCategoryOperator,
    panels.AutoApplyScalePanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Основной переключатель
    bpy.types.Scene.auto_apply_scale_enabled = bpy.props.BoolProperty(
        name="Auto Apply Scale",
        description="Включить автоматическое применение трансформаций",
        default=True,
        update=utils.update_auto_apply_scale
    )
    
    # Свойство для отображения/скрытия списка типов объектов
    bpy.types.Scene.auto_apply_show_object_types = bpy.props.BoolProperty(
        name="Показать типы объектов",
        description="Показать/скрыть список типов объектов",
        default=True
    )
    
    # Настройки трансформаций
    bpy.types.Scene.auto_apply_scale = bpy.props.BoolProperty(
        name="Apply Scale",
        description="Применять масштаб",
        default=True
    )
    
    # Добавляем свойства для типов объектов
    for obj_type, _, _ in OBJECT_TYPES:
        setattr(bpy.types.Scene, f"auto_apply_{obj_type.lower()}", 
                bpy.props.BoolProperty(
                    name=f"Apply to {obj_type}",
                    description=f"Применять к объектам типа {obj_type}",
                    default=obj_type == 'MESH'  # По умолчанию включен только MESH
                ))
    
    # Автозапуск с очисткой предыдущих данных
    def auto_start():
        try:
            if bpy.context.mode == 'OBJECT':
                # Сбрасываем статус текущих запущенных операторов
                # Это решает проблему с повторным включением аддона
                utils.reset_auto_apply_scale_status()
                logger.info("Сброс статуса Auto Apply Scale")
                
                # Запускаем оператор
                utils.update_auto_apply_scale(bpy.context.scene, bpy.context)
        except Exception as e:
            logger.error(f"Ошибка автозапуска: {str(e)}")
        return None
    
    bpy.app.timers.register(auto_start, first_interval=1.0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.auto_apply_scale_enabled
    del bpy.types.Scene.auto_apply_show_object_types
    del bpy.types.Scene.auto_apply_scale
    
    # Удаляем свойства для типов объектов
    for obj_type, _, _ in OBJECT_TYPES:
        prop_name = f"auto_apply_{obj_type.lower()}"
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
    
    # Удаляем свойство для GPENCIL, если оно существует
    # (для совместимости со старыми версиями, где это свойство могло быть создано)
    if hasattr(bpy.types.Scene, "auto_apply_gpencil"):
        delattr(bpy.types.Scene, "auto_apply_gpencil")
        
    # Удаляем свойства location и rotation, если они существуют
    if hasattr(bpy.types.Scene, "auto_apply_location"):
        delattr(bpy.types.Scene, "auto_apply_location")
    if hasattr(bpy.types.Scene, "auto_apply_rotation"):
        delattr(bpy.types.Scene, "auto_apply_rotation")

if __name__ == "__main__":
    register() 