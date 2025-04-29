bl_info = {
    "name": "Quick Backup",
    "author": "@zorinel",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "description": "Automatic .blend file backup with settings and toggle",
    "category": "System"
}

import bpy
import os
import time
from datetime import datetime

# Get settings from the scene
def get_preferences():
    prefs = bpy.context.scene.quick_backup
    return prefs.backup_interval, prefs.max_backups, prefs.enable_auto_backup

# Default values
backup_interval = 300  # 5 minutes
max_backups = 5

last_backup_time = 0

# UI Panel in the N-panel
class QuickBackupPanel(bpy.types.Panel):
    bl_label = "Quick Backup"
    bl_idname = "VIEW3D_PT_quick_backup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Quick Backup'

    def draw(self, context):
        layout = self.layout
        prefs = context.scene.quick_backup

        layout.label(text="Auto-save settings:")

        layout.prop(prefs, "enable_auto_backup", text="Enable Auto Backup")
        layout.prop(prefs, "backup_interval", text="Interval (sec)")
        layout.prop(prefs, "max_backups", text="Max Backups")

        layout.operator("quick_backup.save", text="Save Backup Now")


# Settings stored in the Scene
class QuickBackupSettings(bpy.types.PropertyGroup):
    enable_auto_backup: bpy.props.BoolProperty(
        name="Enable Auto Backup",
        description="Enable or disable automatic backup",
        default=True
    )

    backup_interval: bpy.props.IntProperty(
        name="Interval (sec)",
        description="Interval between automatic backups",
        default=300,
        min=60,
        max=3600,
    )

    max_backups: bpy.props.IntProperty(
        name="Max Backups",
        description="Maximum number of backup files to keep",
        default=5,
        min=1,
        max=20,
    )


# Manual backup operator
class QUICKBACKUP_OT_save(bpy.types.Operator):
    bl_idname = "quick_backup.save"
    bl_label = "Save Quick Backup"

    def execute(self, context):
        make_backup()
        return {'FINISHED'}


def make_backup():
    global last_backup_time
    backup_interval, max_backups, enabled = get_preferences()

    if not enabled:
        return

    if bpy.data.is_saved:
        current_time = time.time()
        if current_time - last_backup_time < backup_interval:
            return
        last_backup_time = current_time

        filepath = bpy.data.filepath
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

        backup_dir = os.path.join(directory, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_name)

        bpy.ops.wm.save_as_mainfile(filepath=backup_path, copy=True)
        print(f"[Quick Backup] Backup saved: {backup_path}")

        # Remove old backups
        backups = sorted(os.listdir(backup_dir), reverse=True)
        for old_backup in backups[max_backups:]:
            old_backup_path = os.path.join(backup_dir, old_backup)
            os.remove(old_backup_path)
            print(f"[Quick Backup] Old backup removed: {old_backup_path}")
    else:
        print("[Quick Backup] File is not yet saved. Backup skipped.")


def backup_timer():
    make_backup()
    return 300.0  # This will run every 5 minutes


def register():
    bpy.utils.register_class(QuickBackupPanel)
    bpy.utils.register_class(QuickBackupSettings)
    bpy.utils.register_class(QUICKBACKUP_OT_save)
    bpy.types.Scene.quick_backup = bpy.props.PointerProperty(type=QuickBackupSettings)

    bpy.app.timers.register(backup_timer)
    print("[Quick Backup] Addon enabled.")


def unregister():
    bpy.utils.unregister_class(QuickBackupPanel)
    bpy.utils.unregister_class(QuickBackupSettings)
    bpy.utils.unregister_class(QUICKBACKUP_OT_save)
    del bpy.types.Scene.quick_backup

    print("[Quick Backup] Addon disabled.")
