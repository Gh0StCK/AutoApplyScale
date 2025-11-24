import logging
from functools import lru_cache
import bpy
from . import constants

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AutoApplyScale')

@lru_cache(maxsize=128)
def get_transform_key(obj_name: str, transform_type: str) -> str:
    """Кэшированный ключ для трансформаций"""
    return f"{obj_name}_{transform_type}"

def reset_auto_apply_scale_status():
    """Сбрасывает статус работы Auto Apply Scale"""
    constants.auto_apply_scale_running = False
    get_transform_key.cache_clear()
    logger.info("Статус Auto Apply Scale сброшен")

def update_auto_apply_scale(self, context):
    """Обновляет состояние авто-применения трансформаций"""
    if context.mode == 'OBJECT':
        if self.auto_apply_scale_enabled and self.auto_apply_scale:
            if not constants.auto_apply_scale_running:
                try:
                    bpy.ops.object.auto_apply_scale('INVOKE_DEFAULT')
                    logger.info("Auto Apply Scale запущен")
                except Exception as e:
                    logger.error(f"Ошибка при запуске Auto Apply Scale: {str(e)}")
    else:
        logger.warning("Auto Apply Scale работает только в Object Mode")
