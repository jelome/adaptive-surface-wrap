"""Property definitions for Adaptive Surface Wrap."""

import bpy
from bpy.props import BoolProperty, IntProperty


def register():
	bpy.types.Scene.asw_base_density = IntProperty(
		name="Base Density",
		description="Subdivision level of the initial cube",
		default=3,
		min=1,
	)

	bpy.types.Scene.asw_use_symmetry = BoolProperty(
		name="Symmetry Mode",
		description="Enable symmetry-friendly subdivision (forces odd density)",
		default=True,
	)


def unregister():
	for attr in ("asw_base_density", "asw_use_symmetry"):
		if hasattr(bpy.types.Scene, attr):
			delattr(bpy.types.Scene, attr)
