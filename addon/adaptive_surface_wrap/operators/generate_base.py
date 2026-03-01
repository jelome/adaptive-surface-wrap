"""Operator to generate a volumetric base mesh around the active object."""

import bpy
import bmesh
from mathutils import Vector


class ASW_OT_GenerateBaseMesh(bpy.types.Operator):
    bl_idname = "asw.generate_base_mesh"
    bl_label = "Generate Base Mesh"
    bl_description = "Generate a volumetric base mesh matching the active object's bounds"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        density = getattr(scene, "asw_base_density", 3)
        use_symmetry = getattr(scene, "asw_use_symmetry", True)

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
        center = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, (min_z + max_z) * 0.5)

        if width <= 0 or depth <= 0 or height <= 0:
            self.report({"ERROR"}, "Active mesh has zero dimensions")
            return {"CANCELLED"}

        # Force an odd density when symmetry is enabled to keep a central loop.
        if use_symmetry and density % 2 == 0:
            density += 1

        cuts = max(density, 0)

        mean_dim = (width + depth + height) / 3.0
        if mean_dim == 0:
            factor = 0.0
        else:
            deviation = (
                abs(width - mean_dim)
                + abs(depth - mean_dim)
                + abs(height - mean_dim)
            ) / 3.0
            normalized_deviation = deviation / mean_dim
            normalized_deviation = max(0.0, min(1.0, normalized_deviation))
            factor = 1.0 - normalized_deviation

        bm = bmesh.new()

        # Always start from a cube, then adapt.
        bmesh.ops.create_cube(bm, size=1.0)
        if cuts > 0:
            bmesh.ops.subdivide_edges(
                bm,
                edges=bm.edges,
                cuts=cuts,
                use_grid_fill=True,
            )

        if factor > 0.0:
            center_vec = Vector((0.0, 0.0, 0.0))
            radius = 0.5
            for vert in bm.verts:
                direction = vert.co - center_vec
                if direction.length > 1e-6:
                    spherical = direction.normalized() * radius
                    vert.co = vert.co.lerp(spherical, factor)

        for vert in bm.verts:
            vert.co.x *= width
            vert.co.y *= depth
            vert.co.z *= height

        bm.normal_update()

        mesh = bpy.data.meshes.new(name="ASW_BaseMesh")
        bm.to_mesh(mesh)
        bm.free()

        base_obj = bpy.data.objects.new("ASW_Base", mesh)
        base_obj.location = center
        if context.collection:
            context.collection.objects.link(base_obj)
        else:
            context.scene.collection.objects.link(base_obj)

        # Apply shrinkwrap to conform to the original mesh.
        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        mod = base_obj.modifiers.new(name="ASW_Shrinkwrap", type="SHRINKWRAP")
        mod.target = original_obj
        mod.wrap_method = "NEAREST_SURFACEPOINT"

        try:
            with context.temp_override(object=base_obj, active_object=base_obj):
                bpy.ops.object.modifier_apply(modifier=mod.name)
        except Exception as exc:  # noqa: BLE001
            self.report({"WARNING"}, f"Shrinkwrap apply failed: {exc}")

        # Ensure smooth shading and blueprint-style display with solid surface + wire overlay.
        view_layer = context.view_layer
        for obj in view_layer.objects:
            obj.select_set(False)
        base_obj.select_set(True)
        view_layer.objects.active = base_obj
        bpy.ops.object.shade_smooth()

        base_obj.color = (0.2, 0.6, 1.0, 1.0)
        base_obj.show_wire = True
        base_obj.show_all_edges = True

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.color_type = "OBJECT"

        if factor < 0.05:
            self.report({"INFO"}, "Using box base (no spherical adaptation)")
        else:
            self.report({"INFO"}, f"Using adaptive spherical base (factor={factor:.2f})")

        return {"FINISHED"}
