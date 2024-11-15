from cadquery.occ_impl import shapes as occ_shapes
from pathlib import Path
import cadquery as cq
import numpy as np


def loft_faces(f1: occ_shapes.Face, f2: occ_shapes.Face) -> occ_shapes.Solid:
    solid = cq.Solid.makeLoft([f1.outerWire(), f2.outerWire()])

    for inner1, inner2 in zip(f1.innerWires(), f2.innerWires()):
        solid_inner = cq.Solid.makeLoft([inner1, inner2])
        solid = solid.cut(solid_inner)

    return solid


def container(
    width,
    depth,
    height,
    thickness,
    ledge,
    exterior_ledge,
    fillet,
    angle=15.0,
    tolerance: float = 0.0,
):
    outer = cq.Workplane("XY").rect(width, depth).extrude(height)
    inner = (
        outer.faces("<Z")
        .workplane(thickness, True)
        .rect(width - thickness * 2, depth - thickness * 2)
        .extrude(height, combine=False)
    )
    box = outer.cut(inner)

    side_cut = (
        outer.faces(">X")
        .workplane()
        .moveTo(depth / 2, height)
        .lineTo(-depth / 2, height - depth * np.arctan(np.deg2rad(angle)))
        .lineTo(-depth / 2, height)
        .close()
        .extrude(-width, combine=False)
    )
    box = box.cut(side_cut)

    step_cut = box.faces(">Z").val()

    outer_wire = step_cut.outerWire()
    inner_wire = step_cut.innerWires()[0]

    if exterior_ledge:
        tolerance_thickness = thickness - tolerance
    else:
        tolerance_thickness = thickness + tolerance

    offset_wire = inner_wire.offset2D(tolerance_thickness / 2)[0]

    if exterior_ledge:
        cut_face = occ_shapes.Face.makeFromWires(outer_wire, [offset_wire])
    else:
        cut_face = occ_shapes.Face.makeFromWires(offset_wire, [inner_wire])

    cut_solid = loft_faces(cut_face, cut_face.translate([0, 0, -ledge]))
    box = box.cut(cq.Workplane(obj=cut_solid)).edges("|Z").fillet(fillet)
    box = box.cut(cq.Workplane(obj=cut_solid)).edges("<Z").fillet(fillet)

    return box.val()


def container_with_lid(
    width: float = 100,
    depth: float = 100,
    height: float = 100,
    thickness: float = 5,
    ledge: float = 10,
    fillet: float = 3,
    angle: float = 15.0,
    tolerance: float = 0.2,
) -> Path:
    width = 20 + thickness
    depth = 20 + thickness
    lower_height = height * 0.80 + thickness
    upper_height = height * 0.20 + thickness
    ledge = ledge
    fillet = fillet
    angle = angle
    tolerance = tolerance

    lower = container(
        width,
        depth,
        lower_height,
        thickness,
        ledge,
        True,
        fillet,
        angle,
        tolerance,
    )

    higher = (
        container(
            width,
            depth,
            upper_height,
            thickness,
            ledge,
            False,
            fillet,
            angle,
            tolerance,
        )
        .rotate([0, 0, 0], [0, 0, 1], 180)
        .translate([width * 1.2, 0, 0])
    )

    compound = cq.Compound.makeCompound([lower, higher])
    compound_path = "container_with_lid.stl"
    compound.exportStl(compound_path)

    return Path(compound_path)
