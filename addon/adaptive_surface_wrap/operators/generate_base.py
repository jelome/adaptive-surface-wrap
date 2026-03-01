"""Operator to generate a base grid mesh around the active object."""

import bpy
from mathutils import Vector


class ASW_OT_GenerateBaseMesh(bpy.types.Operator):
	bl_idname = "asw.generate_base_mesh"
	bl_label = "Generate Base Mesh"
	bl_description = "Generate a grid that matches the active object's footprint"
	bl_options = {"REGISTER", "UNDO"}

	def execute(self, context):
		obj = context.view_layer.objects.active
		if obj is None or obj.type != "MESH":
			self.report({"ERROR"}, "Select a mesh object first")
			return {"CANCELLED"}

		# Compute world-space bounding box corners.
		world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
		xs = [v.x for v in world_corners]
		ys = [v.y for v in world_corners]
		zs = [v.z for v in world_corners]

		min_x, max_x = min(xs), max(xs)
		min_y, max_y = min(ys), max(ys)
		min_z, max_z = min(zs), max(zs)

		width = max_x - min_x
		depth = max_y - min_y
		center = (
			(min_x + max_x) * 0.5,
			(min_y + max_y) * 0.5,
			(min_z + max_z) * 0.5,
		)

		size = max(width, depth)
		if size <= 0:
			self.report({"ERROR"}, "Active mesh has zero footprint")
			return {"CANCELLED"}

		bpy.ops.mesh.primitive_grid_add(
			size=size,
			x_subdivisions=20,
			y_subdivisions=20,
			location=center,
		)

		new_obj = context.view_layer.objects.active
		if new_obj:
			new_obj.name = "ASW_BaseMesh"
			context.view_layer.objects.active = new_obj

		self.report(
			{"INFO"},
			f"Generated base mesh: width={width:.3f}, depth={depth:.3f}, size={size:.3f}",
		)

		return {"FINISHED"}
