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
        shape = getattr(scene, "asw_base_shape", "CUBE")

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

        cuts = max(density - 1, 0)

        bm = bmesh.new()

        if shape == "SPHERE":
            bmesh.ops.create_uvsphere(
                bm,
                u_segments=max(density * 4, 8),
                v_segments=max(density * 2, 4),
                radius=0.5,
            )
            bmesh.ops.scale(bm, vec=(width, depth, height), verts=bm.verts)
        elif shape == "CYLINDER":
            # Quad-only capsule: subdivided cube projected to a sphere and scaled to bounds.
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.subdivide_edges(
                bm,
                edges=bm.edges,
                cuts=density,
                use_grid_fill=True,
            )
            for vert in bm.verts:
                vert.co = vert.co.normalized() * 0.5
                vert.co.x *= width
                vert.co.y *= depth
                vert.co.z *= height
        else:  # CUBE
            half_w = width * 0.5
            half_d = depth * 0.5
            half_h = height * 0.5

            verts = [
                bm.verts.new((-half_w, -half_d, -half_h)),
                bm.verts.new((half_w, -half_d, -half_h)),
                bm.verts.new((half_w, half_d, -half_h)),
                bm.verts.new((-half_w, half_d, -half_h)),
                bm.verts.new((-half_w, -half_d, half_h)),
                bm.verts.new((half_w, -half_d, half_h)),
                bm.verts.new((half_w, half_d, half_h)),
                bm.verts.new((-half_w, half_d, half_h)),
            ]

            faces = [
                (0, 1, 2, 3),
                (4, 5, 6, 7),
                (0, 1, 5, 4),
                (1, 2, 6, 5),
                (2, 3, 7, 6),
                (3, 0, 4, 7),
            ]

            for idxs in faces:
                bm.faces.new([verts[i] for i in idxs])

            bm.normal_update()

            if cuts > 0:
                bmesh.ops.subdivide_edges(
                    bm,
                    edges=bm.edges[:],
                    cuts=cuts,
                    use_grid_fill=True,
                )

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

        return {"FINISHED"}
