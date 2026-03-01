"""Operator to generate a volumetric base mesh around the active object."""

import bpy
from mathutils import Vector


class ASW_OT_GenerateBaseMesh(bpy.types.Operator):
    bl_idname = "asw.generate_base_mesh"
    bl_label = "Generate Base Mesh"
    bl_description = "Generate a volumetric base mesh matching the active object's bounds"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        original_obj = context.view_layer.objects.active
        if original_obj is None or original_obj.type != "MESH":
            self.report({"ERROR"}, "Select a mesh object first")
            return {"CANCELLED"}

        # Compute world-space bounding box corners.
        world_corners = [original_obj.matrix_world @ Vector(corner) for corner in original_obj.bound_box]
        xs = [v.x for v in world_corners]
        ys = [v.y for v in world_corners]
        zs = [v.z for v in world_corners]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        width = max_x - min_x
        depth = max_y - min_y
        height = max_z - min_z
        center = (
            (min_x + max_x) * 0.5,
            (min_y + max_y) * 0.5,
            (min_z + max_z) * 0.5,
        )

        if width <= 0 or depth <= 0 or height <= 0:
            self.report({"ERROR"}, "Active mesh has zero dimensions")
            return {"CANCELLED"}

        bpy.ops.mesh.primitive_cube_add(location=center)

        new_obj = context.view_layer.objects.active
        if new_obj:
            # Scale to fit the bounding box.
            new_obj.scale = (width * 0.5, depth * 0.5, height * 0.5)

            # Apply scale in Object mode.
            bpy.ops.object.transform_apply(scale=True)

            # Subdivide the cube for better deformation.
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.subdivide(number_cuts=4)
            bpy.ops.object.mode_set(mode="OBJECT")

            new_obj.name = "ASW_BaseMesh"

            # Ensure selection for shading and modifier ops.
            bpy.ops.object.select_all(action="DESELECT")
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj

            # Add or reuse shrinkwrap modifier targeting the original object.
            modifier = new_obj.modifiers.get("ASW_Shrinkwrap")
            if modifier is None:
                modifier = new_obj.modifiers.new(name="ASW_Shrinkwrap", type="SHRINKWRAP")

            if modifier.type == "SHRINKWRAP":
                modifier.target = original_obj
                modifier.wrap_method = "NEAREST_SURFACEPOINT"
                modifier.offset = 0.001

            # Smooth shading for the generated mesh.
            bpy.ops.object.shade_smooth()

            # Blueprint-style viewport color and wire overlay (works in Solid with Color: Object).
            new_obj.color = (0.2, 0.6, 1.0, 1.0)
            new_obj.show_wire = True
            new_obj.show_all_edges = True

        self.report(
            {"INFO"},
            (
                f"Generated base mesh: width={width:.3f}, depth={depth:.3f}, "
                f"height={height:.3f}"
            ),
        )

        return {"FINISHED"}
