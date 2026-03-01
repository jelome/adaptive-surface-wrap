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
        center = (
            (min_x + max_x) * 0.5,
            (min_y + max_y) * 0.5,
            (min_z + max_z) * 0.5,
        )

        if width <= 0 or depth <= 0 or height <= 0:
            self.report({"ERROR"}, "Active mesh has zero dimensions")
            return {"CANCELLED"}

        if use_symmetry and density % 2 == 0:
            density += 1

        cuts = max(density - 1, 0)

        # Build cube via bmesh to control subdivision.
        bm = bmesh.new()
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

        mesh = bpy.data.meshes.new(name="ASW_BaseMeshMesh")
        bm.to_mesh(mesh)
        bm.free()

        new_obj = bpy.data.objects.new("ASW_BaseMesh", mesh)
        new_obj.location = center
        context.collection.objects.link(new_obj)

        bpy.ops.object.select_all(action="DESELECT")
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj

        modifier = new_obj.modifiers.new(
            name="ASW_Shrinkwrap",
            type="SHRINKWRAP"
        )

        modifier.target = original_obj
        modifier.wrap_method = "NEAREST_SURFACEPOINT"
        modifier.offset = 0.001

        bpy.ops.object.modifier_apply(modifier=modifier.name)

        bpy.ops.object.shade_smooth()

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
