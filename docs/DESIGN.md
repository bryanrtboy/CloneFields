# Clone Fields

Clone Fields is a free Blender extension providing a simple procedural
cloning and field-effector workflow for modeling.

The intended user experience is inspired by procedural modeling systems
such as Cinema 4D's Cloner/Effectors, but this is an independent
implementation using Blender Geometry Nodes and Python.

The user should normally NOT need to open Geometry Nodes.

## Design principles

1. Geometry Nodes performs procedural geometry generation.
2. Python provides installation, Add menus, object creation and UI.
3. Parameters should appear in normal Blender modifier/object interfaces.
4. Operations must remain live and nondestructive.
5. The system is intended primarily for modeling and 3D printing,
   not animation or motion graphics.
6. Keep the interface simple enough for beginner Blender users.

## Cloner

Add > Clone Fields > Cloner

Cloner distribution modes:

- Linear
- Grid
- Radial
- Object
- Curve

Source:
- Object
- Collection

### Object mode

A target Blender object determines clone positions.

If target is a Mesh:
- Vertices
- Face Centers

If target is a Curve:
- distribute clones along the curve
- Count or Spacing mode
- optional alignment to curve tangent

## Effectors

Initial implementation:

### Transform Effector
Controls:
- Position X/Y/Z
- Rotation X/Y/Z
- Scale X/Y/Z
- Strength

### Random Effector
Controls:
- Position range
- Rotation range
- Scale range
- Seed
- Strength

Multiple effectors should eventually be stackable.

## Fields / Falloff

Initial field types:

- Infinite
- Sphere
- Box
- Linear

Field produces a 0-1 influence value for every clone.

Controls:
- Size/radius
- Falloff distance
- Invert
- Strength

Moving the field/effector object in the Blender viewport should update
the clones interactively.

## Non-goals for version 1

Do not implement:
- Fracture
- dynamics
- PolyFX
- audio effectors
- animation systems
- procedural spline generation
- MoSpline-like tools

Procedural spline generation will be a separate project.

## First milestone

Build only:

1. Add > Clone Fields > Cloner
2. Grid distribution
3. Source Object
4. Count X/Y/Z
5. Spacing X/Y/Z
6. Instances remain instances
7. Parameters editable after creation
8. Geometry Nodes hidden from normal workflow

Once that is solid, expand incrementally.