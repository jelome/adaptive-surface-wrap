"""Adaptive Surface Wrap Blender addon entry point."""

bl_info = {
	"name": "Adaptive Surface Wrap",
	"author": "Adaptive Surface Wrap Team",
	"version": (0, 1, 0),
	"blender": (5, 0, 0),
	"location": "View3D > Sidebar > Adaptive Wrap",
	"description": "Adaptive surface wrapping tools",
	"warning": "",
	"doc_url": "",
	"tracker_url": "",
	"category": "Object",
}

import bpy

from .operators.generate_base import ASW_OT_GenerateBaseMesh
from .ui.panel import ASW_PT_MainPanel


classes = (
	ASW_OT_GenerateBaseMesh,
	ASW_PT_MainPanel,
)


def register() -> None:
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister() -> None:
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
