import bpy
from .constants import OBJECT_TYPES
from .operators import OBJECT_CATEGORIES

class AutoApplyScalePanel(bpy.types.Panel):
    """Панель управления авто-применением трансформаций"""
    bl_label = "Auto Apply Scale"
    bl_idname = "OBJECT_PT_auto_apply_scale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FastTools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Основной переключатель
        layout.prop(scene, "auto_apply_scale_enabled", text="Auto Apply Scale")
        
        if scene.auto_apply_scale_enabled:
            # Настройки трансформаций
            box = layout.box()
            box.label(text="Настройки применения масштаба:")
            row = box.row()
            row.prop(scene, "auto_apply_scale", text="Применять масштаб")
            
            # Типы объектов в виде выпадающего меню
            obj_box = layout.box()
            
            # Верхняя строка с заголовком и счетчиком
            header_row = obj_box.row()
            header_row.alignment = 'LEFT'
            
            # Добавляем кнопку для раскрытия/скрытия списка
            if not hasattr(scene, "auto_apply_show_object_types"):
                scene.auto_apply_show_object_types = True
                
            icon = 'TRIA_DOWN' if scene.auto_apply_show_object_types else 'TRIA_RIGHT'
            header_row.prop(scene, "auto_apply_show_object_types", 
                      text="Типы объектов", 
                      icon=icon, 
                      emboss=False)
            
            # Показываем количество выбранных типов
            selected_count = sum(1 for obj_type, _, _ in OBJECT_TYPES 
                               if getattr(scene, f"auto_apply_{obj_type.lower()}"))
            header_row.label(text=f"Выбрано: {selected_count}")
            
            # Показываем список только если он раскрыт
            if scene.auto_apply_show_object_types:
                # Создаем колонки для более компактного отображения
                for category, types in OBJECT_CATEGORIES.items():
                    box = obj_box.box()
                    
                    # Заголовок категории с кнопками
                    cat_row = box.row()
                    
                    # Разделяем строку на две части: 70% для текста, 30% для кнопок
                    split = cat_row.split(factor=0.7)
                    
                    # Текст категории слева
                    row = split.row()
                    row.alignment = 'LEFT'
                    row.label(text=category)
                    
                    # Кнопки справа
                    buttons_row = split.row(align=True)
                    buttons_row.alignment = 'RIGHT'
                    
                    # Кнопка "Все" с иконкой галочек
                    select_all = buttons_row.operator("object.auto_apply_select_category", text="", icon='CHECKMARK')
                    select_all.category = category
                    
                    # Кнопка "Ничего" с иконкой запрета
                    select_none = buttons_row.operator("object.auto_apply_deselect_category", text="", icon='X')
                    select_none.category = category
                    
                    # Создаем сетку для отображения типов
                    grid = box.grid_flow(row_major=True, columns=2, even_columns=True)
                    
                    for obj_type in types:
                        # Находим соответствующую метку
                        label = next((label for t, label, _ in OBJECT_TYPES if t == obj_type), obj_type)
                        grid.prop(scene, f"auto_apply_{obj_type.lower()}", text=label) 