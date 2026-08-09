# Clone Fields

Clone Fields is a free Blender extension for procedural grid cloning using
Geometry Nodes.

## Install

Download the installable extension zip:

```text
dist/clone_fields.zip
```

In Blender 4.2 or newer:

1. Open `Edit > Preferences > Extensions`.
2. Choose `Install from Disk...`.
3. Select `clone_fields.zip`.
4. Enable `Clone Fields` if Blender does not enable it automatically.

To use it, select a source object and choose:

```text
Add > Clone Fields > Cloner
```

The created `Cloner` object contains the live Geometry Nodes modifier. The
source object is parented under the cloner and hidden while the modifier is
enabled.

## Build the Zip

From the repository root:

```bash
python3 scripts/package_extension.py
```

This writes:

```text
dist/clone_fields.zip
```

It also copies the same zip to your Desktop when a Desktop folder exists.
