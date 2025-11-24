import bpy
from typing import Set, Dict, List, Optional, Tuple
from mathutils import Vector
from .constants import OBJECT_TYPES
from . import constants
from .utils import logger, get_transform_key

# Категории объектов для операторов
OBJECT_CATEGORIES = {
    "Объекты:": ['MESH', 'CURVE', 'SURFACE', 'META', 'EMPTY', 'ARMATURE', 'LATTICE']
}

class AutoApplySelectCategoryOperator(bpy.types.Operator):
    """Выбрать все объекты в категории"""
    bl_idname = "object.auto_apply_select_category"
    bl_label = "Select Category"
    bl_options = {'REGISTER', 'UNDO'}
    
    category: bpy.props.StringProperty(
        name="Категория",
        description="Название категории для выбора",
        default=""
    )
    
    def execute(self, context):
        if self.category in OBJECT_CATEGORIES:
            for obj_type in OBJECT_CATEGORIES[self.category]:
                prop_name = f"auto_apply_{obj_type.lower()}"
                if hasattr(context.scene, prop_name):
                    setattr(context.scene, prop_name, True)
            self.report({'INFO'}, f"Выбраны все объекты в категории {self.category}")
        return {'FINISHED'}

class AutoApplyDeselectCategoryOperator(bpy.types.Operator):
    """Снять выбор всех объектов в категории"""
    bl_idname = "object.auto_apply_deselect_category"
    bl_label = "Deselect Category"
    bl_options = {'REGISTER', 'UNDO'}
    
    category: bpy.props.StringProperty(
        name="Категория",
        description="Название категории для снятия выбора",
        default=""
    )
    
    def execute(self, context):
        if self.category in OBJECT_CATEGORIES:
            for obj_type in OBJECT_CATEGORIES[self.category]:
                prop_name = f"auto_apply_{obj_type.lower()}"
                if hasattr(context.scene, prop_name):
                    setattr(context.scene, prop_name, False)
            self.report({'INFO'}, f"Сняты все объекты в категории {self.category}")
        return {'FINISHED'}

class AutoApplyScaleOperator(bpy.types.Operator):
    """Автоматически применяет трансформации после подтверждения (только в Object Mode)"""
    bl_idname = "object.auto_apply_scale"
    bl_label = "Auto Apply Scale"
    bl_options = {'REGISTER'}

    _timer: Optional[bpy.types.Timer] = None
    _prev_transforms: Dict[str, Dict[str, Vector]] = {}
    _cached_objects: List[bpy.types.Object] = []
    _last_selection: Set[str] = set()
    _context_data: Dict = {}
    _is_object_mode: bool = False
    _last_selected_types: Set[str] = set()

    def _cleanup_old_data(self):
        """Очищает данные для несуществующих объектов"""
        existing_objects = {obj.name for obj in bpy.data.objects}
        self._prev_transforms = {k: v for k, v in self._prev_transforms.items() if k in existing_objects}

    def _get_objects_to_process(self, context) -> List[bpy.types.Object]:
        """Получает список объектов для обработки с кэшированием"""
        current_selection = {obj.name for obj in context.selected_objects}
        
        selected_types = {obj_type for obj_type, _, _ in OBJECT_TYPES 
                          if getattr(context.scene, f"auto_apply_{obj_type.lower()}", False)}

        if current_selection != self._last_selection or selected_types != self._last_selected_types:
            # Получаем список выбранных типов объектов
            # Фильтруем объекты по выбранным типам
            self._cached_objects = [obj for obj in context.selected_objects 
                                  if obj.type in selected_types]
            
            logger.debug(f"Выбранные типы объектов: {selected_types}")
            logger.debug(f"Отфильтровано объектов: {len(self._cached_objects)} из {len(context.selected_objects)}")
            
            self._last_selection = current_selection
            self._last_selected_types = selected_types
            self._cleanup_old_data()
            
        return self._cached_objects

    def _has_transform_changed(self, obj: bpy.types.Object, prev: Dict[str, Vector], context) -> bool:
        """Быстрая проверка изменений трансформаций"""
        prev_scale = prev.get('scale')
        if prev_scale is None:
            return False
        return any(abs(obj.scale[i] - prev_scale[i]) > 1e-4 for i in range(3))

    def _save_initial_state(self, context):
        """Сохраняет начальное состояние объектов"""
        for obj in self._get_objects_to_process(context):
            if obj.name not in self._prev_transforms:
                transforms = {'scale': obj.scale.copy()}
                self._prev_transforms[obj.name] = transforms

    def _get_changed_objects(self, context) -> List[bpy.types.Object]:
        """Возвращает список объектов, у которых изменились трансформации"""
        changed_objects = []
        
        for obj in self._get_objects_to_process(context):
            prev = self._prev_transforms.get(obj.name, None)
            if prev is not None and self._has_transform_changed(obj, prev, context):
                changed_objects.append(obj)
                transforms = {'scale': obj.scale.copy()}
                self._prev_transforms[obj.name] = transforms
                    
        return changed_objects

    def _apply_transforms(self, context, obj: bpy.types.Object):
        """Применяет трансформации к объекту"""
        try:
            view_layer = self._context_data['view_layer']
            
            if not context.scene.auto_apply_scale:
                return

            # Проверяем, что тип объекта включен в настройках
            obj_type = obj.type
            if not getattr(context.scene, f"auto_apply_{obj_type.lower()}", False):
                logger.debug(f"Пропускаем объект {obj.name} типа {obj_type}, т.к. этот тип отключен в настройках")
                return
            
            # Проверяем, что масштаб не равен (1.0, 1.0, 1.0)
            if all(abs(s - 1.0) < 1e-6 for s in obj.scale):
                logger.debug(f"Пропускаем объект {obj.name}, т.к. его масштаб уже равен (1.0, 1.0, 1.0)")
                return
            
            # Сохраняем текущий статус выделения всех объектов
            selected_objects = {o: o.select_get() for o in context.view_layer.objects}
            active_object = view_layer.objects.active
            
            # Сначала снимаем выделение со всех объектов
            for o in context.view_layer.objects:
                o.select_set(False)
            
            # Выбираем только текущий объект
            obj.select_set(True)
            view_layer.objects.active = obj
            
            # Применяем только масштаб
            bpy.ops.object.transform_apply(
                location=False,
                rotation=False,
                scale=True
            )
            
            # Восстанавливаем прежнее выделение
            for o, was_selected in selected_objects.items():
                o.select_set(was_selected)
            view_layer.objects.active = active_object
                
            logger.debug(f"Применен масштаб к объекту: {obj.name}")
        except Exception as e:
            logger.error(f"Ошибка при применении масштаба к объекту {obj.name}: {str(e)}")
            self.report({'ERROR'}, f"Ошибка применения масштаба: {str(e)}")

    def _restore_selection(self, context, original_selection, original_active):
        view_layer = self._context_data['view_layer']
        if original_active:
            view_layer.objects.active = original_active

    def _update_context_data(self, context):
        """Обновляет кэшированные данные контекста"""
        self._context_data = {
            'scene': context.scene,
            'view_layer': context.view_layer,
            'selected_objects': context.selected_objects
        }
        self._is_object_mode = context.mode == 'OBJECT'

    def modal(self, context, event):
        # Быстрая проверка на необходимость обработки события
        if event.type not in {'LEFTMOUSE', 'TIMER'}:
            return {'PASS_THROUGH'}

        self._update_context_data(context)
        
        if not self._is_object_mode:
            return {'PASS_THROUGH'}

        if not self._context_data['scene'].auto_apply_scale_enabled:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            try:
                original_active = self._context_data['view_layer'].objects.active
                
                changed_objects = self._get_changed_objects(context)
                
                if changed_objects:
                    logger.debug(f"Обнаружено {len(changed_objects)} объектов с измененным масштабом")
                    for obj in changed_objects:
                        self._apply_transforms(context, obj)
                
                self._restore_selection(context, [], original_active)
                    
                logger.info(f"Применен масштаб к {len(changed_objects)} объектам")
            except Exception as e:
                logger.error(f"Ошибка в modal: {str(e)}")
                self.report({'ERROR'}, f"Ошибка: {str(e)}")
            return {'PASS_THROUGH'}

        elif event.type == 'TIMER':
            self._save_initial_state(context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        try:
            self._update_context_data(context)
            wm = context.window_manager
            
            # Динамический интервал таймера
            interval = max(0.1, min(0.5, 0.5 / (len(context.selected_objects) or 1)))
            self._timer = wm.event_timer_add(interval, window=context.window)
            
            # Принудительная инициализация для всех выбранных объектов
            self._save_initial_state(context)
            
            wm.modal_handler_add(self)
            constants.auto_apply_scale_running = True
            logger.info("Auto Apply Scale запущен")
            return {'RUNNING_MODAL'}
        except Exception as e:
            logger.error(f"Ошибка при запуске Auto Apply Scale: {str(e)}")
            return {'CANCELLED'}

    def cancel(self, context):
        try:
            if self._timer is not None:
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
            constants.auto_apply_scale_running = False
            self._prev_transforms.clear()
            self._cached_objects.clear()
            self._last_selection.clear()
            self._context_data.clear()
            get_transform_key.cache_clear()
            logger.info("Auto Apply Scale остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке: {str(e)}")
        return {'CANCELLED'}
