from functools import lru_cache
import bpy
from bpy.app.handlers import persistent
from . import constants

@lru_cache(maxsize=128)
def get_transform_key(obj_name: str, transform_type: str) -> str:
    """Кэшированный ключ для трансформаций"""
    return f"{obj_name}_{transform_type}"

def reset_auto_apply_scale_status():
    """Сбрасывает статус работы Auto Apply Scale"""
    constants.auto_apply_scale_running = False
    get_transform_key.cache_clear()

def update_auto_apply_scale(self, context):
    """Обновляет состояние авто-применения трансформаций"""
    if context.mode == 'OBJECT':
        if self.auto_apply_scale_enabled and self.auto_apply_scale:
            if not constants.auto_apply_scale_running:
                try:
                    bpy.ops.object.auto_apply_scale('INVOKE_DEFAULT')
                except Exception:
                    pass

@persistent
def auto_apply_scale_load_post(dummy):
    """Перезапускает оператор после загрузки .blend файла.
    
    При загрузке файла Blender восстанавливает свойства сцены, но не вызывает
    update-коллбэки BoolProperty, поэтому modal-оператор нужно запускать вручную.
    """
    def delayed_start():
        try:
            reset_auto_apply_scale_status()
            scene = bpy.context.scene
            if (scene
                    and getattr(scene, 'auto_apply_scale_enabled', False)
                    and getattr(scene, 'auto_apply_scale', False)):
                if bpy.context.mode == 'OBJECT':
                    bpy.ops.object.auto_apply_scale('INVOKE_DEFAULT')
        except Exception:
            pass
        return None  # однократный таймер

    bpy.app.timers.register(delayed_start, first_interval=1.0)
