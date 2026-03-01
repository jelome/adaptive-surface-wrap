"""UI panel for Adaptive Surface Wrap."""

import bpy


class ASW_PT_MainPanel(bpy.types.Panel):
	bl_label = "Adaptive Surface Wrap"
	bl_idname = "ASW_PT_main_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Adaptive Wrap"

	def draw(self, context):
		layout = self.layout
		scene = context.scene
		layout.prop(scene, "asw_use_symmetry")
		layout.prop(scene, "asw_base_density")
		if scene.asw_use_symmetry and scene.asw_base_density % 2 == 0:
			layout.label(text="Symmetry mode requires odd density", icon="ERROR")
		layout.operator(
			"asw.generate_base_mesh",
			text="Generate Base Mesh",
			icon="MESH_GRID",
		)
