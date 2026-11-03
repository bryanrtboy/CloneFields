"""Numeric raster utilities for Curve Cloner displacement."""

import struct
import numpy as np


def open_dem(path):
    """Memory-map contiguous, uncompressed single-band float32 classic TIFF."""
    with path.open("rb") as stream:
        header = stream.read(8)
        if header[:2] not in {b"II", b"MM"}:
            raise ValueError("Not a TIFF file")
        endian = {b"II": "<", b"MM": ">"}[header[:2]]
        magic, directory = struct.unpack(endian + "HI", header[2:])
        if magic != 42:
            raise ValueError("Expected classic TIFF")
        stream.seek(directory)
        count = struct.unpack(endian + "H", stream.read(2))[0]
        entries = [stream.read(12) for _ in range(count)]
        tags = {}
        for entry in entries:
            tag, kind, length = struct.unpack(endian + "HHI", entry[:8])
            if tag not in {256, 257, 258, 259, 273, 274, 277, 278, 339, 42113}:
                continue
            formats = {2: "c", 3: "H", 4: "I", 11: "f"}
            if kind not in formats:
                continue
            fmt = endian + str(length) + formats[kind]
            size = struct.calcsize(fmt)
            raw = entry[8:]
            if size > 4:
                stream.seek(struct.unpack(endian + "I", raw)[0])
                raw = stream.read(size)
            tags[tag] = struct.unpack(fmt, raw[:size])
    scalar = lambda tag, default: tags.get(tag, (default,))[0]
    if (scalar(258, 0), scalar(259, 1), scalar(277, 1), scalar(339, 1)) != (32, 1, 1, 3):
        raise ValueError("Expected uncompressed single-channel float32 TIFF")
    if scalar(274, 1) != 1 or 273 not in tags:
        raise ValueError("Expected top-left strip-based TIFF")
    width, height = scalar(256, 0), scalar(257, 0)
    rows = scalar(278, height)
    if width < 1 or height < 1 or rows < 1:
        raise ValueError("Invalid TIFF dimensions")
    offsets = np.array(tags[273], dtype=np.int64)
    expected = offsets[0] + np.arange(len(offsets)) * rows * width * 4
    if len(offsets) != (height + rows - 1) // rows or not np.array_equal(offsets, expected):
        raise ValueError("Expected contiguous TIFF strips")
    nodata = float(b"".join(tags[42113]).rstrip(b"\0")) if 42113 in tags else None
    data = np.memmap(path, dtype=endian + "f4", mode="r", offset=int(offsets[0]), shape=(height, width))
    return data, nodata


def sample(data, nodata, u, v):
    """Bilinear normalized-coordinate samples, excluding invalid neighbors."""
    x = np.clip(u, 0, 1) * (data.shape[1] - 1)
    y = np.clip(v, 0, 1) * (data.shape[0] - 1)
    ix, iy = x.astype(np.int64), y.astype(np.int64)
    jx, jy = np.minimum(ix + 1, data.shape[1] - 1), np.minimum(iy + 1, data.shape[0] - 1)
    fx, fy = x - ix, y - iy
    result, weights = np.zeros_like(x), np.zeros_like(x)
    for values, weight in (
        (data[iy, ix], (1 - fx) * (1 - fy)),
        (data[iy, jx], fx * (1 - fy)),
        (data[jy, ix], (1 - fx) * fy),
        (data[jy, jx], fx * fy),
    ):
        valid = np.isfinite(values)
        if nodata is not None:
            valid &= values != nodata
        weight = weight * valid
        result += np.where(valid, values, 0) * weight
        weights += weight
    return np.divide(result, weights, out=np.full_like(result, np.nan), where=weights > 0)
