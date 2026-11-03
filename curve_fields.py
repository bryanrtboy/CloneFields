"""Native 2D Curve cloner. Kept independent of the mesh/GN cloner evaluator."""

import hashlib
from pathlib import Path
import time
import uuid

import bpy
import numpy as np
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from mathutils import Euler, Matrix, Vector
from bpy_extras.io_utils import ImportHelper

from . import effectors, panels, properties
from .curve_images import open_dem, sample

OWNER = "clone_curve_fields_owner"
CONTROLLER = "clone_curve_fields_controller"
MASK = "clone_curve_fields_mask"
_cache = {}
_images = {}
_busy = False


def _redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {"VIEW_3D", "PROPERTIES"}:
                area.tag_redraw()


def _safe_evaluate(controller, force=False):
    try:
        before = _cache.get(controller.as_pointer())
        evaluate(controller, force=force)
        if before != _cache.get(controller.as_pointer()):
            _redraw()
    except Exception as error:
        # A bad source/image must not unregister Blender's repeating timer.
        message = f"{type(error).__name__}: {error}"
        if controller.clone_curve_fields.status != message:
            print(f"Curve Cloner: {message}")
            controller.clone_curve_fields.status = message


def request_update(controller=None, effector=None):
    """Property edits update immediately; polling also covers source/transform edits."""
    global _busy
    if not bpy.app.timers.is_registered(refresh):
        bpy.app.timers.register(refresh, first_interval=0.15, persistent=True)
    if _busy:
        return
    _busy = True
    try:
        controllers = [controller] if controller else [
            obj for obj in bpy.data.objects
            if obj.get(CONTROLLER) and (obj.clone_curve_fields.effector == effector
                or any(entry.effector == effector for entry in obj.clone_curve_fields.effects))
        ]
        for obj in controllers:
            if obj and obj.get(CONTROLLER):
                _safe_evaluate(obj)
    finally:
        _busy = False


def valid_source(obj):
    return bool(obj and obj.type == "CURVE" and obj.data.dimensions == "2D"
                and obj.data.splines and not obj.get(OWNER))


def _poll_source(self, obj):
    return valid_source(obj) and obj != self.id_data


def _poll_effector(self, obj):
    return bool(obj and obj.get(properties.PROP_EFFECTOR_TYPE) == "SHADER")


def _changed(self, context):
    request_update(controller=self.id_data)


def _poll_transform_effector(self, obj):
    return bool(obj and obj.get(properties.PROP_EFFECTOR_TYPE) in {"SHADER", "BASIC", "RANDOM", "STEP"})


AFFECT_ITEMS = (("OBJECTS", "Objects", "Transform whole clones, preserving their native curve geometry"),
                ("POINTS", "Points", "Deform source control points within local XY"))


def _link_changed(self, context):
    global _busy
    previous = _busy
    _busy = True
    try:
        if self.effector:
            self.affect = "POINTS" if self.effector.clone_fields_effector.type == "SHADER" else "OBJECTS"
    finally:
        _busy = previous
    _changed(self, context)


class CurveEffectorLink(bpy.types.PropertyGroup):
    effector: PointerProperty(name="Effector", type=bpy.types.Object, poll=_poll_transform_effector, update=_link_changed)
    affect: EnumProperty(name="Affect", items=AFFECT_ITEMS, default="OBJECTS", update=_changed)
    enabled: BoolProperty(name="Enable This Entry", description="Include this entry when evaluating the stack", default=True, update=_changed)
    influence: IntProperty(name="Strength Here", description="Strength of this stack entry only. Multiplies the shared Effector Strength; 50% here × 50% shared = 25%", default=100, min=0, max=100, subtype="PERCENTAGE", update=_changed)
    show_controls: BoolProperty(name="Show Controls", default=True)
    normalize: BoolProperty(name="Normalize Image", description="Map the valid image or elevation range to 0–1 before applying strength", default=False, update=_changed)
    dem_path: StringProperty(name="DEM TIFF", description="Optional numeric DEM for this entry; overrides the shared Effector image", subtype="FILE_PATH", update=_changed)
    show_input: BoolProperty(name="Image / Elevation", default=True)
    show_projection: BoolProperty(name="Projection", default=False)
    show_transforms: BoolProperty(name="Transform", default=True)
    show_field: BoolProperty(name="Field / Falloff", default=False)
    show_shared: BoolProperty(name="Shared Effector Settings", default=False)


def migrate_stack(settings):
    """Preserve saved Shader-first scenes as a single ordered stack."""
    owner = settings.id_data
    if owner.get("curve_stack_version", 0) >= 2:
        return
    global _busy
    previous = _busy
    _busy = True
    try:
        owner["curve_stack_version"] = 2
        if settings.effector:
            entry = settings.effects.add()
            entry.effector = settings.effector
            entry.affect = settings.shader_affect
            entry.normalize = settings.normalize
            entry.dem_path = settings.dem_path
            settings.effects.move(len(settings.effects) - 1, 0)
    finally:
        _busy = previous


def shader_link(settings, index=-1):
    migrate_stack(settings)
    if index >= 0:
        entry = settings.effects[index] if index < len(settings.effects) else None
        return entry if entry and entry.effector and entry.effector.clone_fields_effector.type == "SHADER" else None
    return next((entry for entry in settings.effects if entry.effector
                 and entry.effector.clone_fields_effector.type == "SHADER"), None)


def _spacing_changed(self, context):
    owner = self.id_data
    old = owner.get("curve_spacing_mode", "PER_STEP")
    new = self.spacing_mode
    if old != new:
        # Convert the displayed values without moving the existing grid.
        owner["curve_spacing_mode"] = new
        global _busy
        previous_busy = _busy
        _busy = True
        try:
            for axis in "xyz":
                steps = max(1, getattr(self, "count_" + axis) - 1)
                value = getattr(self, "spacing_" + axis)
                setattr(self, "spacing_" + axis, value * steps if new == "ENDPOINT" else value / steps)
        finally:
            _busy = previous_busy
    _changed(self, context)


def grid_steps(settings):
    return tuple(getattr(settings, "spacing_" + axis) /
                 (max(1, getattr(settings, "count_" + axis) - 1) if settings.spacing_mode == "ENDPOINT" else 1)
                 for axis in "xyz")


class CurveClonerSettings(bpy.types.PropertyGroup):
    source: PointerProperty(name="Source Curve", type=bpy.types.Object, poll=_poll_source, update=_changed)
    count_x: IntProperty(name="X", default=1, min=1, max=1000, update=_changed)
    count_y: IntProperty(name="Y", default=1, min=1, max=1000, update=_changed)
    count_z: IntProperty(name="Z", default=10, min=1, max=1000, update=_changed)
    spacing_x: FloatProperty(name="X", default=2, subtype="DISTANCE", update=_changed)
    spacing_y: FloatProperty(name="Y", default=2, subtype="DISTANCE", update=_changed)
    spacing_z: FloatProperty(name="Z", default=0.2, subtype="DISTANCE", update=_changed)
    spacing_mode: EnumProperty(name="Spacing Mode", items=(("PER_STEP", "Per Step", "Distance between adjacent clones"),
        ("ENDPOINT", "Endpoint", "Total distance from first clone to last clone")), default="PER_STEP", update=_spacing_changed)
    effector: PointerProperty(name="Shader Effector", type=bpy.types.Object, poll=_poll_effector, update=_changed)
    shader_affect: EnumProperty(name="Affect", items=AFFECT_ITEMS, default="POINTS", update=_changed)
    effects: CollectionProperty(type=CurveEffectorLink)
    points: EnumProperty(name="Affect Points", items=(("ALL", "All", "Deform all source control points"),
        ("MASK", "Stored Selection", "Use the selection stored from the source curve")), update=_changed)
    enabled: BoolProperty(name="Live Update", default=True, update=_changed)
    normalize: BoolProperty(name="Normalize Image", description="Map the valid image range to 0–1; useful for elevation rasters", default=False, update=_changed)
    dem_path: StringProperty(name="DEM TIFF", subtype="FILE_PATH", description="Optional numeric float32 TIFF, instead of the Effector image", update=_changed)
    status: StringProperty(name="Status", default="")


def _source_data(source):
    coordinates, handles, selections = [], [], []
    signature = []
    for spline in source.data.splines:
        points = spline.bezier_points if spline.type == "BEZIER" else spline.points
        co = np.array([tuple(p.co)[:3] for p in points], dtype=np.float32)
        if not np.isfinite(co).all() or np.any(np.abs(co[:, 2]) > 1e-5):
            raise ValueError("Source control points must lie in local XY")
        coordinates.append(co)
        if spline.type == "BEZIER":
            left = np.array([tuple(p.handle_left) for p in points], dtype=np.float32)
            right = np.array([tuple(p.handle_right) for p in points], dtype=np.float32)
            handles.append((left, right))
            signature.append((spline.type, spline.use_cyclic_u, co.tobytes(), left.tobytes(), right.tobytes(),
                              tuple((p.handle_left_type, p.handle_right_type) for p in points)))
        else:
            handles.append(None)
            signature.append((spline.type, spline.use_cyclic_u, co.tobytes(), tuple(p.co.w for p in points),
                              spline.order_u, spline.use_endpoint_u))
        signature.append(tuple((p.radius, p.tilt) for p in points))
        signature.append((spline.use_smooth, spline.resolution_u))
        selections.extend([p.select_control_point if spline.type == "BEZIER" else p.select for p in points])
    # Copy the full Curve datablock when its settings change. This preserves
    # Blender's native bevel profiles, taper, fill, materials, and resolution.
    settings = []
    for prop in source.data.bl_rna.properties:
        if prop.is_readonly or prop.identifier in {"name", "name_full"}:
            continue
        value = getattr(source.data, prop.identifier)
        if prop.type in {"BOOLEAN", "INT", "FLOAT", "ENUM", "STRING"}:
            settings.append((prop.identifier, tuple(value) if getattr(prop, "is_array", False) else value))
        elif prop.type == "POINTER":
            settings.append((prop.identifier, value.as_pointer() if value else 0))
    profile = source.data.bevel_profile
    if profile:
        settings.append(("profile", tuple((tuple(p.location), p.handle_type_1, p.handle_type_2) for p in profile.points)))
    settings.append(("materials", tuple(m.as_pointer() if m else 0 for m in source.data.materials)))
    return coordinates, handles, selections, hashlib.sha256(repr((signature, settings)).encode()).hexdigest()


def _image_data(settings):
    if settings.dem_path:
        path = Path(bpy.path.abspath(settings.dem_path))
        stat = path.stat()
        key = (str(path), stat.st_mtime_ns, stat.st_size)
        if key not in _images:
            # The prototype reader accepts the supplied uncompressed float DEM.
            data, nodata = open_dem(path)
            low, high = float("inf"), float("-inf")
            for row in range(0, data.shape[0], 128):
                block = np.asarray(data[row:row + 128])
                valid = np.isfinite(block)
                if nodata is not None:
                    valid &= block != nodata
                if valid.any():
                    low = min(low, float(block[valid].min()))
                    high = max(high, float(block[valid].max()))
            if not np.isfinite(low):
                raise ValueError("DEM contains no valid elevations")
            _images[key] = (data, nodata, low, high, True)
            # Create a small numeric preview once, outside the GPU draw callback.
            ys = np.linspace(0, data.shape[0] - 1, min(512, data.shape[0])).astype(int)
            xs = np.linspace(0, data.shape[1] - 1, min(512, data.shape[1])).astype(int)
            values = np.array(data[np.ix_(ys, xs)], dtype=np.float32)
            valid = np.isfinite(values)
            if nodata is not None:
                valid &= values != nodata
            values = np.where(valid, np.clip((values - low) / max(high - low, 1e-8), 0, 1), 0)
            values = np.flipud(values)
            name = _dem_preview_name(path)
            preview = bpy.data.images.get(name)
            if preview is None:
                preview = bpy.data.images.new(name, width=len(xs), height=len(ys), float_buffer=True)
            elif tuple(preview.size) != (len(xs), len(ys)):
                preview.scale(len(xs), len(ys))
            rgba = np.ones((len(ys), len(xs), 4), dtype=np.float32)
            rgba[:, :, :3] = values[:, :, None]
            preview.colorspace_settings.name = "Non-Color"
            preview.pixels.foreach_set(rgba.ravel())
            preview.update()
            # Generated-image pixel buffers and ID thumbnails are separate.
            # Persist the former and explicitly populate the latter; otherwise
            # template_preview can display a black thumbnail after reload.
            preview.pack()
            thumbnail = preview.preview_ensure()
            thumbnail.image_size = (len(xs), len(ys))
            thumbnail.image_pixels_float = rgba.ravel()
            thumbnail.is_image_custom = True
        return key, _images[key]
    image = settings.effector.clone_fields_effector.shader_image if settings.effector else None
    if image is None:
        return None, None
    key = (image.as_pointer(), tuple(image.size), image.is_dirty, image.filepath)
    if key not in _images:
        pixels = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(pixels)
        width, height = image.size
        if not width or not height:
            raise ValueError("Image has no pixel data")
        pixels = pixels.reshape(height, width, image.channels)
        data = pixels[:, :, :min(3, image.channels)].mean(axis=2)
        finite = data[np.isfinite(data)]
        if not finite.size:
            raise ValueError("Image contains no valid samples")
        _images[key] = (data, None, float(finite.min()), float(finite.max()), False)
    return key, _images[key]


def _dem_preview_name(path):
    return ".Curve DEM " + hashlib.sha256(str(path).encode()).hexdigest()[:12]


def preview_image(controller, index=-1):
    settings = shader_link(controller.clone_curve_fields, index)
    if settings is None:
        return None
    if settings.dem_path:
        return bpy.data.images.get(_dem_preview_name(Path(bpy.path.abspath(settings.dem_path))))
    effector = settings.effector
    return effector.clone_fields_effector.shader_image if effector else None


def _field_weight(local, eff):
    absolute = np.abs(local)
    if eff.shape == "NONE":
        return np.ones(len(local))
    if eff.shape == "SPHERE":
        distance = np.linalg.norm(local, axis=1) / max(eff.radius, 1e-8)
    elif eff.shape == "CUBE":
        distance = np.max(absolute / np.maximum(np.array((eff.box_x, eff.box_y, eff.box_z)) / 2, 1e-8), axis=1)
    elif eff.shape == "CYLINDER":
        distance = np.maximum(np.linalg.norm(local[:, :2], axis=1) / max(eff.radius, 1e-8), absolute[:, 2] / max(eff.height / 2, 1e-8))
    else:
        distance = np.clip(local[:, 2] / max(eff.length / 2, 1e-8), -1, 1)
    return np.clip((1 - distance) / max(1 - eff.falloff / 100, 1e-8), 0, 1)


def _transform(co, matrix):
    matrix = np.array(matrix, dtype=np.float64)
    return co @ matrix[:3, :3].T + matrix[:3, 3]


def _weights(world, settings, image_data):
    effector = settings.effector
    if effector and effector.clone_fields_effector.type != "SHADER":
        return np.zeros(len(world))
    if effector is None or image_data is None:
        return np.zeros(len(world))
    eff = effector.clone_fields_effector
    local = _transform(world, effector.matrix_world.inverted_safe())
    uv = local[:, :2] / np.maximum((eff.shader_width, eff.shader_height), 1e-8) + 0.5
    # Fitted edge points can drift a few ulps outside the image after rotating
    # a parent hierarchy. Do not turn their displacement abruptly off.
    inside = ((uv >= -1e-6) & (uv <= 1 + 1e-6)).all(axis=1)
    uv = np.clip(uv, 0, 1)
    tiled = uv * (eff.shader_tiles_x, eff.shader_tiles_y)
    uv = np.mod(tiled, 1)
    # Keep the outer edge at the last pixel rather than wrapping to the first.
    uv[np.isclose(tiled, (eff.shader_tiles_x, eff.shader_tiles_y), rtol=0, atol=1e-8)] = 1
    data, nodata, low, high, top_down = image_data
    values = sample(data, nodata, uv[:, 0], 1 - uv[:, 1] if top_down else uv[:, 1])
    valid = np.isfinite(values)
    if settings.normalize:
        values = (values - low) / max(high - low, 1e-8)
    if eff.invert:
        values = 1 - values
    return np.where(valid & inside, values, 0) * _field_weight(local, eff) * eff.strength / 100


def _children(controller):
    identity = controller.get(CONTROLLER)
    return sorted((o for o in controller.children if o.get(OWNER) == identity), key=lambda o: int(o.get("curve_index", 0)))


def _delete_output(obj):
    curve = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if curve.users == 0:
        bpy.data.curves.remove(curve)


def _effector_signature(obj):
    if obj is None:
        return None
    eff = obj.clone_fields_effector
    names = ("type", "shape", "seed", "radius", "box_x", "box_y", "box_z", "height", "length", "falloff", "strength", "invert",
             "shader_width", "shader_height", "shader_tiles_x", "shader_tiles_y", "use_position", "position_x", "position_y", "position_z",
             "use_rotation", "rotation_x", "rotation_y", "rotation_z", "use_scale", "scale_x", "scale_y", "scale_z", "scale_uniform", "scale_absolute")
    return (obj.as_pointer(), tuple(tuple(r) for r in obj.matrix_world), tuple(getattr(eff, name) for name in names))


def _effect_weights(obj, world, index, total, point_domain=False):
    eff = obj.clone_fields_effector
    local = _transform(world, obj.matrix_world.inverted_safe())
    weight = _field_weight(local, eff)
    if eff.type == "STEP":
        progression = np.linspace(0, 1, len(world)) if point_domain and len(world) > 1 else index / max(1, total - 1)
        weight *= 1 - progression if eff.invert else progression
    elif eff.invert and eff.shape != "NONE":
        weight = 1 - weight
    return weight * eff.strength / 100


def _channels(eff, weights, index):
    """Generate deterministic per-clone/per-point position, rotation, scale."""
    n = len(weights)
    random = np.ones((n, 9))
    if eff.type == "RANDOM":
        random = np.random.default_rng(np.random.SeedSequence((eff.seed, index))).uniform(-1, 1, (n, 9))
    position = np.zeros((n, 3))
    rotation = np.zeros((n, 3))
    scale = np.ones((n, 3))
    if eff.use_position:
        position = random[:, :3] * (eff.position_x, eff.position_y, eff.position_z) * weights[:, None]
    if eff.use_rotation:
        rotation = random[:, 3:6] * (eff.rotation_x, eff.rotation_y, eff.rotation_z) * weights[:, None]
    if eff.use_scale:
        amount = np.array((eff.scale_x,) * 3 if eff.scale_uniform else (eff.scale_x, eff.scale_y, eff.scale_z))
        values = random[:, 6:9]
        if eff.scale_uniform:
            values = np.repeat(values[:, :1], 3, axis=1)
        if eff.type == "RANDOM" and eff.scale_absolute:
            values = (values + 1) / 2
        scale += values * amount * weights[:, None]
    return position, rotation, scale


def _point_transform(co, position, rotation, scale):
    # Only local XY scale, local Z rotation, and local XY translation may
    # deform point data. Whole-object transforms have unrestricted XYZ axes.
    angle = rotation[:, 2]
    cosine, sine = np.cos(angle), np.sin(angle)
    x, y = co[:, 0] * scale[:, 0], co[:, 1] * scale[:, 1]
    result = np.zeros_like(co)
    result[:, 0] = x * cosine - y * sine + position[:, 0]
    result[:, 1] = x * sine + y * cosine + position[:, 1]
    return result


def evaluate(controller, force=False):
    settings = controller.clone_curve_fields
    migrate_stack(settings)
    if not settings.enabled and not force:
        return
    if not valid_source(settings.source):
        settings.status = "Choose a 2D Curve source"
        return
    source = settings.source
    if source.mode == "EDIT":
        settings.status = "Editing source: store selection or exit Edit Mode to update"
        return
    if any(mod.show_viewport and mod.type != "NODES" for mod in source.modifiers):
        settings.status = "Source modifiers are not evaluated; deformation uses Curve Data"
        return
    coordinates, handles, _, data_signature = _source_data(source)
    links = [entry for entry in settings.effects if entry.enabled and entry.effector
             and entry.effector.clone_fields_effector.type in {"SHADER", "BASIC", "RANDOM", "STEP"}]
    has_point_effects = any(entry.affect == "POINTS" for entry in links)
    mask = tuple(source.data.get(MASK, [])) if settings.points == "MASK" and has_point_effects else ()
    count = settings.count_x * settings.count_y * settings.count_z
    if count > 10000:
        settings.status = "Maximum 10,000 native curve clones"
        return
    if settings.points == "MASK" and has_point_effects and len(mask) != sum(map(len, coordinates)):
        settings.status = "Store a point selection on the source curve first"
        return
    image_data = []
    errors = []
    link_signatures = []
    for entry in links:
        image_key, image = None, None
        if entry.effector.clone_fields_effector.type == "SHADER":
            try:
                image_key, image = _image_data(entry)
                if image is None:
                    errors.append("Choose an image for " + entry.effector.name)
            except (ValueError, OSError, RuntimeError, KeyError) as error:
                image_key = ("unavailable", entry.dem_path)
                errors.append(f"Image unavailable: {error}")
        image_data.append(image)
        link_signatures.append((entry.affect, entry.influence, entry.normalize, image_key, _effector_signature(entry.effector)))
    geometry_inputs = (source.as_pointer(), data_signature, mask, settings.points,
        settings.count_x, settings.count_y, settings.count_z, settings.spacing_x, settings.spacing_y, settings.spacing_z,
        settings.spacing_mode, tuple(tuple(r) for r in controller.matrix_world), tuple(tuple(r) for r in source.matrix_basis.to_3x3()))
    # Only the prefix through the last point effect can change point data.
    # Trailing object effects reuse coordinates, but an object effect BEFORE
    # a shader is included: its placement changes that shader's sampling.
    last_point = max((i for i, entry in enumerate(links) if entry.affect == "POINTS"), default=-1)
    point_stamp = hashlib.sha256(repr((geometry_inputs, link_signatures[:last_point + 1])).encode()).hexdigest()
    signature = (geometry_inputs, tuple(link_signatures))
    children = _children(controller)
    if not force and _cache.get(controller.as_pointer()) == signature and len(children) == count:
        if settings.status.startswith("Editing source:"):
            settings.status = "Up to date"
        return
    start = time.perf_counter()
    collection = controller.users_collection[0]
    while len(children) > count:
        _delete_output(children.pop())
    # Source rotation/scale are authored locally. Inherited parent transforms
    # already reach every output through the controller; applying them here
    # again rotates/scales the profile twice when the whole rig is grouped.
    source_matrix = source.matrix_basis.to_3x3().to_4x4()
    base = np.concatenate(coordinates)
    steps = grid_steps(settings)
    for index in range(count):
        x = index % settings.count_x
        y = (index // settings.count_x) % settings.count_y
        z = index // (settings.count_x * settings.count_y)
        position = ((x - (settings.count_x - 1) / 2) * steps[0],
                    (y - (settings.count_y - 1) / 2) * steps[1],
                    (z - (settings.count_z - 1) / 2) * steps[2])
        if index >= len(children):
            obj = bpy.data.objects.new(f"{controller.name} {index + 1:04}", source.data.copy())
            obj[OWNER] = controller[CONTROLLER]
            obj["curve_index"] = index
            obj["source_signature"] = data_signature
            collection.objects.link(obj)
            obj.parent = controller
            children.append(obj)
        obj = children[index]
        if obj.data.users > 1:
            obj.data = obj.data.copy()
        if obj.get("source_signature") != data_signature:
            old = obj.data
            obj.data = source.data.copy()
            if old.users == 0:
                bpy.data.curves.remove(old)
            obj["source_signature"] = data_signature
        obj.matrix_parent_inverse = Matrix.Identity(4)
        basis = Matrix.Translation(position) @ source_matrix
        update_points = force or obj.get("points_signature") != point_stamp
        transformed = base.copy() if update_points else None
        transformed_handles = [tuple(h.copy() for h in handle) if handle is not None else None for handle in handles] if update_points else None
        for entry, image in zip(links, image_data):
            point_domain = entry.affect == "POINTS"
            if point_domain and not update_points:
                continue
            local = transformed if point_domain else np.zeros((1, 3))
            world = _transform(local, controller.matrix_world @ basis)
            eff = entry.effector.clone_fields_effector
            weights = (_weights(world, entry, image) if eff.type == "SHADER" else
                       _effect_weights(entry.effector, world, index, count, point_domain=point_domain))
            weights *= entry.influence / 100
            if point_domain and mask:
                weights *= np.array(mask)
            delta_pos, delta_rot, delta_scale = _channels(eff, weights, index)
            if not point_domain:
                # Apply channels to the current object placement. The next
                # effect samples this updated placement.
                origin = basis.translation + Vector(delta_pos[0])
                linear = Euler(delta_rot[0], "XYZ").to_matrix().to_4x4() @ basis.to_3x3().to_4x4() @ Matrix.Diagonal((*delta_scale[0], 1))
                basis = Matrix.Translation(origin) @ linear
                continue
            transformed = _point_transform(transformed, delta_pos, delta_rot, delta_scale)
            offset = 0
            for spline_index, co in enumerate(coordinates):
                handle = transformed_handles[spline_index]
                if handle is not None:
                    indices = slice(offset, offset + len(co))
                    transformed_handles[spline_index] = tuple(_point_transform(h, delta_pos[indices], delta_rot[indices], delta_scale[indices]) for h in handle)
                offset += len(co)
        obj.matrix_basis = basis
        if not update_points:
            continue
        offset = 0
        for spline, co, handle in zip(obj.data.splines, coordinates, transformed_handles):
            deformed = transformed[offset:offset + len(co)].copy()
            deformed[:, 2] = 0
            if handle is None:
                homogeneous = np.ones((len(co), 4), dtype=np.float32)
                homogeneous[:, :3] = deformed
                homogeneous[:, 3] = [p.co.w for p in spline.points]
                spline.points.foreach_set("co", homogeneous.ravel())
            else:
                left, right = handle
                spline.bezier_points.foreach_set("co", deformed.ravel())
                left[:, 2] = right[:, 2] = 0
                spline.bezier_points.foreach_set("handle_left", left.ravel())
                spline.bezier_points.foreach_set("handle_right", right.ravel())
            offset += len(co)
        obj.data.update_tag()
        obj["points_signature"] = point_stamp
    _cache[controller.as_pointer()] = signature
    message = errors[0] if errors else f"{count} curves · {len(base):,} points each · {(time.perf_counter() - start) * 1000:.0f} ms"
    if settings.status != message:
        settings.status = message


def refresh():
    global _busy
    if _busy or not hasattr(bpy.data, "objects"):
        return 0.15
    _busy = True
    try:
        for obj in list(bpy.data.objects):
            if obj.get(CONTROLLER):
                # Preview loading is independent of live deformation and source
                # Edit Mode, so paused rigs still regain their DEM thumbnails.
                for entry in obj.clone_curve_fields.effects:
                    if entry.effector and entry.effector.clone_fields_effector.type == "SHADER" and entry.dem_path:
                        try:
                            _image_data(entry)
                        except (ValueError, OSError, RuntimeError, KeyError):
                            pass
                _safe_evaluate(obj)
    finally:
        _busy = False
    return 0.15


@persistent
def _load(_):
    _cache.clear()
    _images.clear()
    for obj in bpy.data.objects:
        if obj.get(CONTROLLER):
            migrate_stack(obj.clone_curve_fields)
    if not bpy.app.timers.is_registered(refresh):
        bpy.app.timers.register(refresh, first_interval=0.15, persistent=True)


@persistent
def _render(scene, *_args):
    for obj in scene.objects:
        if obj.get(CONTROLLER):
            evaluate(obj)


def controller_for(obj):
    if obj and obj.get(CONTROLLER):
        return obj
    if obj and obj.get(OWNER) and obj.parent and obj.parent.get(CONTROLLER):
        return obj.parent
    return None


class AddCurveCloner(bpy.types.Operator):
    bl_idname = "clone_fields.add_curve_cloner"
    bl_label = "Add Curve Cloner"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        source = context.object if valid_source(context.object) else None
        obj = bpy.data.objects.new("Curve Cloner", None)
        obj[CONTROLLER] = uuid.uuid4().hex
        obj.empty_display_type = "PLAIN_AXES"
        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        obj.clone_curve_fields.source = source
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        evaluate(obj)
        return {"FINISHED"}


class NewCurveShader(bpy.types.Operator):
    bl_idname = "clone_fields.curve_new_shader"
    bl_label = "New Shader Effector"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return bpy.ops.clone_fields.curve_add_effector(kind="SHADER")


class AddCurveEffector(bpy.types.Operator):
    bl_idname = "clone_fields.curve_add_effector"
    bl_label = "Add Curve Effector"
    bl_options = {"REGISTER", "UNDO"}
    kind: EnumProperty(items=(("SHADER", "Shader", "Deform points using an image"), ("BASIC", "Basic", "Offset all influenced clones"),
        ("RANDOM", "Random", "Randomize influenced clones"), ("STEP", "Step", "Progressive clone transforms"),
        ("LINK", "Link Existing", "Choose an existing Shader, Basic, Random, or Step Effector")))

    def execute(self, context):
        controller = controller_for(context.object)
        if controller is None:
            return {"CANCELLED"}
        settings = controller.clone_curve_fields
        migrate_stack(settings)
        entry = settings.effects.add()
        entry.enabled = False
        if self.kind != "LINK":
            obj = bpy.data.objects.new(effectors.EFFECTOR_TYPE_LABELS[self.kind] + " Effector", None)
            context.collection.objects.link(obj)
            eff = obj.clone_fields_effector
            eff.type = self.kind
            eff.shape = "NONE"
            eff.use_position = True
            eff.position_x = eff.position_y = 0
            eff.position_z = 1
            if self.kind == "SHADER":
                eff.position_z = 0
                eff.position_y = 1
                entry.affect = "POINTS"
            if self.kind == "RANDOM":
                eff.position_x = eff.position_y = eff.position_z = 0.2
            effectors.configure_effector_object(obj, "NONE", eff.radius, self.kind)
            # Share the controller's parent frame, not the generated curve
            # hierarchy. Copy its parent inverse so an already-rotated group
            # does not rotate a newly created Effector a second time.
            obj.parent = controller.parent
            obj.matrix_parent_inverse = controller.matrix_parent_inverse.copy()
            obj.matrix_basis = controller.matrix_basis.copy()
            entry.effector = obj
            if self.kind == "SHADER":
                _fit_projection(controller, len(settings.effects) - 1)
        entry.enabled = True
        request_update(controller)
        return {"FINISHED"}


class RemoveCurveEffector(bpy.types.Operator):
    bl_idname = "clone_fields.curve_remove_effector"
    bl_label = "Remove Effector from Stack"
    bl_description = "Remove this assignment, keeping the shared Effector object"
    bl_options = {"REGISTER", "UNDO"}
    index: IntProperty()

    def execute(self, context):
        controller = controller_for(context.object)
        if controller is None or not 0 <= self.index < len(controller.clone_curve_fields.effects):
            return {"CANCELLED"}
        controller.clone_curve_fields.effects.remove(self.index)
        request_update(controller)
        return {"FINISHED"}


class MoveCurveEffector(bpy.types.Operator):
    bl_idname = "clone_fields.curve_move_effector"
    bl_label = "Move Curve Effector"
    bl_options = {"REGISTER", "UNDO"}
    index: IntProperty()
    direction: IntProperty(default=1)

    def execute(self, context):
        controller = controller_for(context.object)
        if controller is None:
            return {"CANCELLED"}
        links = controller.clone_curve_fields.effects
        target = self.index + self.direction
        if 0 <= self.index < len(links) and 0 <= target < len(links):
            links.move(self.index, target)
            request_update(controller)
        return {"FINISHED"}


def _fit_projection(controller, index=-1):
    settings = controller.clone_curve_fields
    entry = shader_link(settings, index)
    obj = entry.effector if entry else None
    if obj is None or not valid_source(settings.source):
        return
    # A stack of XY profiles varies along X and Z. Align the existing shader's
    # XY projection with those axes; users can freely rotate it afterward.
    obj.matrix_world = controller.matrix_world @ Matrix.Rotation(np.pi / 2, 4, "X")
    inverse = obj.matrix_world.inverted_safe()
    base = np.concatenate(_source_data(settings.source)[0])
    rotation = settings.source.matrix_basis.to_3x3().to_4x4()
    steps = grid_steps(settings)
    corners = []
    for x in (-(settings.count_x - 1) / 2, (settings.count_x - 1) / 2):
        for y in (-(settings.count_y - 1) / 2, (settings.count_y - 1) / 2):
            for z in (-(settings.count_z - 1) / 2, (settings.count_z - 1) / 2):
                matrix = inverse @ controller.matrix_world @ Matrix.Translation(
                    (x * steps[0], y * steps[1], z * steps[2])) @ rotation
                corners.append(_transform(base, matrix))
    coordinates = np.concatenate(corners)
    minimum, maximum = coordinates.min(axis=0), coordinates.max(axis=0)
    center = (minimum + maximum) / 2
    obj.matrix_world.translation = obj.matrix_world @ Vector(center)
    eff = obj.clone_fields_effector
    eff.shader_preserve_aspect = False
    eff.shader_width = max(float(maximum[0] - minimum[0]), 0.001)
    eff.shader_height = max(float(maximum[1] - minimum[1]), 0.001)


class FitCurveProjection(bpy.types.Operator):
    bl_idname = "clone_fields.curve_fit_projection"
    bl_label = "Fit Projection Across Stack"
    bl_description = "Align the Shader Effector image with the cloner's X/Z plane and fit the source grid"
    bl_options = {"REGISTER", "UNDO"}
    index: IntProperty(default=-1)

    def execute(self, context):
        controller = controller_for(context.object)
        if controller is None:
            return {"CANCELLED"}
        _fit_projection(controller, self.index)
        return {"FINISHED"}


class LoadCurveImage(bpy.types.Operator, ImportHelper):
    bl_idname = "clone_fields.curve_load_image"
    bl_label = "Load Shader Image"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.exr;*.bmp", options={"HIDDEN"})
    index: IntProperty(default=-1)

    def execute(self, context):
        controller = controller_for(context.object)
        if controller is None:
            return {"CANCELLED"}
        settings = shader_link(controller.clone_curve_fields, self.index)
        if settings is None or settings.effector is None:
            return {"CANCELLED"}
        path = Path(self.filepath)
        if path.suffix.lower() in {".tif", ".tiff"}:
            try:
                open_dem(path)
            except (ValueError, KeyError, OSError):
                pass  # Ordinary/compressed TIFFs use Blender's image loader.
            else:
                settings.dem_path = str(path)
                settings.normalize = True
                _cache.clear()
                return {"FINISHED"}
        try:
            image = bpy.data.images.load(str(path), check_existing=True)
            image.colorspace_settings.name = "Non-Color"
        except RuntimeError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        settings.dem_path = ""
        settings.effector.clone_fields_effector.shader_image = image
        _images.clear()
        _cache.clear()
        return {"FINISHED"}


class StoreCurveSelection(bpy.types.Operator):
    bl_idname = "clone_fields.curve_store_selection"
    bl_label = "Store Deformation Selection"
    bl_description = "Store selected source control points as a persistent deformation mask"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return valid_source(context.object) and context.object.mode == "EDIT"

    def execute(self, context):
        source = context.object
        mask = []
        for spline in source.data.splines:
            points = spline.bezier_points if spline.type == "BEZIER" else spline.points
            mask.extend(int(p.select_control_point if spline.type == "BEZIER" else p.select) for p in points)
        source.data[MASK] = mask
        for obj in bpy.data.objects:
            if obj.get(CONTROLLER) and obj.clone_curve_fields.source == source:
                obj.clone_curve_fields.points = "MASK"
        self.report({"INFO"}, f"Stored {sum(mask)} of {len(mask)} points")
        return {"FINISHED"}


class ReloadCurveImage(bpy.types.Operator):
    bl_idname = "clone_fields.curve_reload_image"
    bl_label = "Refresh Image / Curves"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        _images.clear()
        _cache.clear()
        obj = controller_for(context.object)
        if obj:
            try:
                evaluate(obj, force=True)
            except (ValueError, OSError, RuntimeError, KeyError) as error:
                self.report({"ERROR"}, str(error))
                return {"CANCELLED"}
        return {"FINISHED"}


def _selection_controller(obj):
    if obj is None:
        return None
    controller = controller_for(obj)
    if controller:
        return controller
    return next((c for c in bpy.data.objects if c.get(CONTROLLER) and c.clone_curve_fields.source == obj), None)


class EditCurveSelection(bpy.types.Operator):
    bl_idname = "clone_fields.curve_edit_selection"
    bl_label = "Edit Source Point Selection"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        controller = _selection_controller(context.object)
        source = controller.clone_curve_fields.source if controller else context.object
        if not valid_source(source) or source.name not in context.view_layer.objects:
            self.report({"ERROR"}, "Make the source Curve available in this View Layer")
            return {"CANCELLED"}
        if context.object and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        if controller:
            controller["curve_selection_source_was_hidden"] = source.hide_get()
        source.hide_set(False)
        source.select_set(True)
        context.view_layer.objects.active = source
        bpy.ops.object.mode_set(mode="EDIT")
        return {"FINISHED"}


class FinishCurveSelection(bpy.types.Operator):
    bl_idname = "clone_fields.curve_finish_selection"
    bl_label = "Store Selection & Return to Cloner"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return StoreCurveSelection.poll(context)

    def execute(self, context):
        controller = _selection_controller(context.object)
        source = context.object
        bpy.ops.clone_fields.curve_store_selection()
        bpy.ops.object.mode_set(mode="OBJECT")
        if controller:
            bpy.ops.object.select_all(action="DESELECT")
            controller.select_set(True)
            context.view_layer.objects.active = controller
            if controller.pop("curve_selection_source_was_hidden", False):
                source.hide_set(True)
            request_update(controller)
        return {"FINISHED"}


def _draw_selection(layout, context, controller):
    box = layout.box()
    box.label(text="Point Selection")
    if controller:
        settings = controller.clone_curve_fields
        box.prop(settings, "points", text="Use Points")
        source = settings.source
    else:
        source = context.object
    if source and valid_source(source):
        mask = list(source.data.get(MASK, []))
        box.label(text=f"Stored: {sum(mask)} of {len(mask)} points" if mask else "No selection stored")
    if context.object and context.object.mode == "EDIT" and valid_source(context.object):
        box.operator("clone_fields.curve_finish_selection", icon="CHECKMARK")
        box.operator("clone_fields.curve_store_selection", text="Store Selection (Stay in Edit Mode)")
    else:
        box.operator("clone_fields.curve_edit_selection", icon="EDITMODE_HLT")


class CurveSelectionSidebar(bpy.types.Panel):
    bl_label = "Curve Point Selection"
    bl_idname = "CLONE_FIELDS_PT_curve_selection_sidebar"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Clone Fields"

    @classmethod
    def poll(cls, context):
        return valid_source(context.object) or _selection_controller(context.object) is not None

    def draw(self, context):
        _draw_selection(self.layout, context, _selection_controller(context.object))


class CurveSourceSelectionPanel(bpy.types.Panel):
    bl_label = "Curve Cloner Point Selection"
    bl_idname = "CLONE_FIELDS_PT_curve_source_selection"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return valid_source(context.object) and _selection_controller(context.object) is not None

    def draw(self, context):
        _draw_selection(self.layout, context, _selection_controller(context.object))


def _section(layout, entry, property_name, title):
    box = layout.box()
    header = box.row()
    header.use_property_split = False
    expanded = getattr(entry, property_name)
    header.prop(entry, property_name, text=title,
                icon="TRIA_DOWN" if expanded else "TRIA_RIGHT", emboss=False)
    if not expanded:
        return None
    body = box.column()
    body.use_property_split = True
    return body


def _axis_controls(layout, eff, prefix, axes):
    row = layout.row(align=True)
    row.use_property_split = False
    for axis in axes:
        row.prop(eff, prefix + "_" + axis, text=axis.upper())


def _draw_shader_controls(box, controller, entry, index):
    eff = entry.effector.clone_fields_effector
    image_box = _section(box, entry, "show_input", "Image / Elevation")
    if image_box is not None:
        image_box.prop(eff, "shader_image", text="Image")
        image_box.operator("clone_fields.curve_load_image", text="Load Image / DEM", icon="FILE_FOLDER").index = index
        preview = preview_image(controller, index)
        if preview:
            image_box.template_preview(preview, show_buttons=False)
        image_box.prop(eff, "shader_show_image")
        image_box.prop(entry, "normalize")
        image_box.prop(eff, "invert", text="Invert Image")
        image_box.separator()
        image_box.prop(entry, "dem_path", text="Numeric DEM")
    projection = _section(box, entry, "show_projection", "Projection")
    if projection is not None:
        projection.prop(eff, "shader_preserve_aspect")
        projection.prop(eff, "shader_width", text="Width")
        projection.prop(eff, "shader_height", text="Height")
        projection.operator("clone_fields.curve_fit_projection", text="Fit Across Stack", icon="FULLSCREEN_ENTER").index = index
        projection.prop(eff, "shader_tiles_x", text="Tiles X")
        projection.prop(eff, "shader_tiles_y", text="Tiles Y")
        projection.label(text="Image faces the Effector's local Z axis.", icon="INFO")


def _draw_transform_controls(layout, entry):
    body = _section(layout, entry, "show_transforms", "Transform")
    if body is None:
        return
    eff = entry.effector.clone_fields_effector
    point_mode = entry.affect == "POINTS"
    if eff.type == "RANDOM":
        body.prop(eff, "seed")
    elif eff.type == "STEP":
        body.prop(eff, "invert", text="Reverse Order")
    body.prop(eff, "use_position", text="Position")
    if eff.use_position:
        _axis_controls(body, eff, "position", "xy" if point_mode else "xyz")
    body.separator(factor=0.4)
    body.prop(eff, "use_rotation", text="Rotation")
    if eff.use_rotation:
        _axis_controls(body, eff, "rotation", "z" if point_mode else "xyz")
    body.separator(factor=0.4)
    body.prop(eff, "use_scale", text="Scale")
    if eff.use_scale:
        body.prop(eff, "scale_uniform")
        if eff.type == "RANDOM":
            body.prop(eff, "scale_absolute")
        if eff.scale_uniform:
            body.prop(eff, "scale_x", text="Amount")
        else:
            _axis_controls(body, eff, "scale", "xy" if point_mode else "xyz")
    if point_mode:
        body.label(text="Local XY plane; rotation about local Z.", icon="INFO")


def _draw_curve_effector(layout, controller, entry, index, count):
    box = layout.box()
    header = box.row(align=True)
    # Split property layouts squeezed the old pointer into a blank black
    # widget. Headers are ordinary full-width rows with explicit labels.
    header.use_property_split = False
    header.prop(entry, "show_controls", text="",
                icon="TRIA_DOWN" if entry.show_controls else "TRIA_RIGHT", emboss=False)
    header.prop(entry, "enabled", text="")
    obj = entry.effector
    label = obj.name if obj else "Choose an Effector"
    icon = "TEXTURE" if obj and obj.clone_fields_effector.type == "SHADER" else "OUTLINER_OB_EMPTY"
    header.label(text=f"{index + 1}. {label}", icon=icon)
    up = header.row(align=True)
    up.enabled = index > 0
    op = up.operator("clone_fields.curve_move_effector", text="", icon="TRIA_UP")
    op.index, op.direction = index, -1
    down = header.row(align=True)
    down.enabled = index < count - 1
    op = down.operator("clone_fields.curve_move_effector", text="", icon="TRIA_DOWN")
    op.index, op.direction = index, 1
    header.operator("clone_fields.curve_remove_effector", text="", icon="TRASH").index = index
    if not entry.show_controls:
        return
    body = box.column()
    body.enabled = entry.enabled
    if obj is None:
        body.prop(entry, "effector", text="Effector Object")
        return
    eff = obj.clone_fields_effector
    if eff.type not in {"SHADER", "BASIC", "RANDOM", "STEP"}:
        body.label(text="Target is unavailable for curves.", icon="ERROR")
        return
    body.prop(entry, "affect")
    body.prop(entry, "influence", text="Strength Here", slider=True)
    if eff.strength != 100:
        body.label(text=f"Combined strength: {entry.influence * eff.strength / 100:.0f}%", icon="INFO")
    if eff.type == "SHADER":
        _draw_shader_controls(body, controller, entry, index)
    _draw_transform_controls(body, entry)
    field = _section(body, entry, "show_field", "Field / Falloff · " + effectors.FIELD_SHAPE_LABELS.get(eff.shape, eff.shape))
    if field is not None:
        panels._draw_field_settings(field, eff)
    shared = _section(body, entry, "show_shared", "Shared Effector Settings")
    if shared is not None:
        picker = shared.column()
        picker.use_property_split = False
        picker.prop(entry, "effector", text="Effector Object")
        shared.prop(eff, "strength", text="Shared Strength", slider=True)
        shared.label(text="Changes every cloner using this Effector.", icon="INFO")


class CurveClonerPanel(bpy.types.Panel):
    bl_label = "Curve Cloner"
    bl_idname = "CLONE_FIELDS_PT_curve_cloner"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        return controller_for(context.object) is not None

    def draw(self, context):
        controller = controller_for(context.object)
        settings = controller.clone_curve_fields
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(settings, "source")
        if not valid_source(settings.source):
            layout.label(text="Choose a subdivided 2D Curve", icon="INFO")
            return
        panels._draw_xyz_row(layout, settings, "Count", "count_x", "count_y", "count_z")
        layout.prop(settings, "spacing_mode")
        panels._draw_xyz_row(layout, settings, "Endpoint" if settings.spacing_mode == "ENDPOINT" else "Spacing",
                            "spacing_x", "spacing_y", "spacing_z")
        _draw_selection(layout, context, controller)
        layout.separator()
        layout.label(text="Effector Stack · Top to Bottom")
        for index, entry in enumerate(settings.effects):
            _draw_curve_effector(layout, controller, entry, index, len(settings.effects))
        row = layout.row(align=True)
        for kind, label in (("SHADER", "Shader"), ("BASIC", "Basic"), ("RANDOM", "Random"), ("STEP", "Step")):
            row.operator("clone_fields.curve_add_effector", text=label).kind = kind
        layout.operator("clone_fields.curve_add_effector", text="Link Existing Effector", icon="LINKED").kind = "LINK"
        layout.prop(settings, "enabled")
        layout.operator("clone_fields.curve_reload_image", icon="FILE_REFRESH")
        layout.label(text=settings.status)


classes = (CurveEffectorLink, CurveClonerSettings, AddCurveCloner, NewCurveShader, AddCurveEffector,
           RemoveCurveEffector, MoveCurveEffector, FitCurveProjection, LoadCurveImage,
           StoreCurveSelection, EditCurveSelection, FinishCurveSelection, ReloadCurveImage,
           CurveSelectionSidebar, CurveSourceSelectionPanel, CurveClonerPanel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.clone_curve_fields = PointerProperty(type=CurveClonerSettings)
    # Blender enables add-ons under RestrictBlend: no scene access is allowed
    # here. The first timer tick migrates existing controllers via evaluate().
    bpy.app.handlers.load_post.append(_load)
    bpy.app.handlers.render_pre.append(_render)
    bpy.app.handlers.frame_change_post.append(_render)
    bpy.app.timers.register(refresh, first_interval=0.0, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(refresh):
        bpy.app.timers.unregister(refresh)
    for handlers, handler in ((bpy.app.handlers.load_post, _load), (bpy.app.handlers.render_pre, _render),
                              (bpy.app.handlers.frame_change_post, _render)):
        if handler in handlers:
            handlers.remove(handler)
    _cache.clear()
    _images.clear()
    del bpy.types.Object.clone_curve_fields
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
