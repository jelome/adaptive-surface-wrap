"""Property definitions for Adaptive Surface Wrap."""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty


def register():
	bpy.types.Scene.asw_base_density = IntProperty(
		name="Base Density",
		description="Subdivision level for the generated base mesh",
		default=3,
		min=1,
	)

	bpy.types.Scene.asw_use_symmetry = BoolProperty(
		name="Symmetry Mode",
		description="Enable symmetry-friendly subdivision (forces odd density)",
		default=True,
	)

	bpy.types.Scene.asw_base_shape = EnumProperty(
		name="Base Shape",
		description="Initial volume shape for shrinkwrap",
		items=[
			("CUBE", "Cube", "Use cube as base"),
			("SPHERE", "Sphere", "Use UV sphere as base"),
			("CYLINDER", "Cylinder", "Use cylinder as base"),
		],
		default="CUBE",
	)


def unregister():
	for attr in ("asw_base_density", "asw_use_symmetry", "asw_base_shape"):
		if hasattr(bpy.types.Scene, attr):
			delattr(bpy.types.Scene, attr)
