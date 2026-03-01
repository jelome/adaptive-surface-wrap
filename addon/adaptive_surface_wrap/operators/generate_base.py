"""Operator to generate a simple grid base mesh."""

import bpy


class ASW_OT_GenerateBaseMesh(bpy.types.Operator):
	bl_idname = "asw.generate_base_mesh"
	bl_label = "Generate Base Mesh"
	bl_description = "Generate a simple grid base mesh"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		bpy.ops.mesh.primitive_grid_add(
			size=2.0,
			x_subdivisions=10,
			y_subdivisions=10,
		)
		return {"FINISHED"}
