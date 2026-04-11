import logging
from functools import lru_cache
from pathlib import Path
import bpy
from . import constants

# Настройка логирования
logger = logging.getLogger('AutoApplyScale')


def _setup_logger_handlers():
    """Настраивает вывод логов в консоль и файл в папке workspace."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    has_stream_handler = any(type(h) is logging.StreamHandler for h in logger.handlers)
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    preferred_log_file_path = Path("D:/1/AutoApplyScale.log")
    fallback_log_file_path = Path(__file__).resolve().parent.parent / "AutoApplyScale.log"
    log_file_path = preferred_log_file_path if preferred_log_file_path.parent.exists() else fallback_log_file_path
    has_file_handler = any(
        isinstance(h, logging.FileHandler) and Path(getattr(h, "baseFilename", "")).resolve() == log_file_path
        for h in logger.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


_setup_logger_handlers()
logger.setLevel(logging.INFO)
logger.propagate = False


def update_logging_level(scene, context):
    """Переключает уровень логирования для аддона."""
    debug_enabled = bool(getattr(scene, "auto_apply_debug_logging", False))
    logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    logger.info("Режим логирования: %s", "DEBUG" if debug_enabled else "INFO")

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
    update_logging_level(self, context)

    if context.mode == 'OBJECT':
        if self.auto_apply_scale_enabled and self.auto_apply_scale:
            if not constants.auto_apply_scale_running:
                try:
                    bpy.ops.object.auto_apply_scale('INVOKE_DEFAULT')
                    logger.info("Auto Apply Scale запущен")
                except Exception as e:
                    logger.error(f"Ошибка при запуске Auto Apply Scale: {str(e)}")
            else:
                logger.debug("Auto Apply Scale уже запущен, повторный запуск не требуется")
        else:
            logger.debug(
                "Автоприменение отключено: enabled=%s, apply_scale=%s",
                self.auto_apply_scale_enabled,
                self.auto_apply_scale,
            )
    else:
        logger.warning("Auto Apply Scale работает только в Object Mode (текущий режим: %s)", context.mode)
