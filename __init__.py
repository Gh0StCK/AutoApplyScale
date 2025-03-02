bl_info = {
    "name": "Auto Apply Scale",
    "blender": (4, 3, 2),
    "category": "Object",
    "author": "Stanislav Kolesnikov",
    "version": (1, 1, 0),
    "description": "Automatically applies scale after confirming a scale transformation with left mouse click via a checkbox toggle. Starts enabled by default.",
    "location": "View 3D > Sidebar > FastTools",
}

import bpy

# Глобальная переменная для отслеживания состояния modal-оператора
auto_apply_scale_running = False

def update_auto_apply_scale(self, context):
    global auto_apply_scale_running
    if self.auto_apply_scale_enabled:
        if not auto_apply_scale_running:
            bpy.ops.object.auto_apply_scale('INVOKE_DEFAULT')
    else:
        # Если чекбокс выключен, modal-оператор сам завершится при следующем событии
        pass

class AutoApplyScaleOperator(bpy.types.Operator):
    """Автоматически применяет масштаб после изменения и подтверждения левой кнопкой мыши"""
    bl_idname = "object.auto_apply_scale"
    bl_label = "Auto Apply Scale"
    bl_options = {'REGISTER'}

    _timer = None
    _prev_scales = {}

    def modal(self, context, event):
        # Если чекбокс выключен, завершаем modal-оператор
        if not context.scene.auto_apply_scale_enabled:
            self.cancel(context)
            return {'CANCELLED'}

        # При отпускании левой кнопки мыши проверяем изменения масштаба
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            # Сохраняем исходное выделение и активный объект
            original_selection = [obj for obj in context.selected_objects if obj.type == 'MESH']
            original_active = context.view_layer.objects.active

            changed_objects = []
            for obj in original_selection:
                prev_scale = self._prev_scales.get(obj.name, None)
                if prev_scale is not None and obj.scale != prev_scale:
                    changed_objects.append(obj)
                    self._prev_scales[obj.name] = obj.scale.copy()

            # Применяем трансформацию для каждого изменённого объекта
            for obj in changed_objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            # Восстанавливаем исходное выделение и активный объект
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                obj.select_set(True)
            if original_active in original_selection:
                context.view_layer.objects.active = original_active
            elif original_selection:
                context.view_layer.objects.active = original_selection[0]
            return {'PASS_THROUGH'}

        # На событии таймера сохраняем начальные масштабы для выбранных объектов
        elif event.type == 'TIMER':
            for obj in context.selected_objects:
                if obj.type == 'MESH' and obj.name not in self._prev_scales:
                    self._prev_scales[obj.name] = obj.scale.copy()
        return {'PASS_THROUGH'}

    def execute(self, context):
        global auto_apply_scale_running
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        auto_apply_scale_running = True
        self.report({'INFO'}, "Auto Apply Scale запущен")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        global auto_apply_scale_running
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        auto_apply_scale_running = False
        self.report({'INFO'}, "Auto Apply Scale остановлен")
        return {'CANCELLED'}

class AutoApplyScalePanel(bpy.types.Panel):
    """Панель управления авто-применением масштаба"""
    bl_label = "Auto Apply Scale"
    bl_idname = "OBJECT_PT_auto_apply_scale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FastTools'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "auto_apply_scale_enabled", text="Auto Apply Scale")

classes = [AutoApplyScaleOperator, AutoApplyScalePanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.auto_apply_scale_enabled = bpy.props.BoolProperty(
        name="Auto Apply Scale",
        description="Если включено, автоматически применять масштаб после трансформации",
        default=True,  # Чекбокс по умолчанию включен
        update=update_auto_apply_scale
    )
    # Планируем запуск оператора через 1 секунду после регистрации,
    # чтобы контекст был полноценным и имел атрибут scene.
    def auto_start():
        update_auto_apply_scale(bpy.context.scene, bpy.context)
        return None
    bpy.app.timers.register(auto_start, first_interval=1.0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.auto_apply_scale_enabled

if __name__ == "__main__":
    register()
