from build123d import *
from build123d.hull import (
    find_hull,
    convert_and_validate,
    select_lowest,
    Hull,
    Arc,
    Segment,
    get_angle,
    update_hull,
)
import build123d.build_part as bp
import build123d.build_sketch as bs
import build123d.build_line as bl
from cq_vscode import show_object, show, reset_show, set_defaults

from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection

# %%

with BuildSketch() as b:
    Rectangle(2, 4)
    with Locations((0.4, 2)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((0, 0)):
        Circle(0.9, mode=Mode.SUBTRACT)
    # with Locations((-0.4, -2)):
    #     Circle(0.9, mode=Mode.ADD)

hull_wire = qhull(b.edges())
show(b, hull_wire)

# %%

rv = convert_and_validate(b.edges())
hull = find_hull(b.edges())

# %%
from scipy.spatial import ConvexHull


def flatten(nested_list):
    return [y for x in nested_list for y in x]


def discretize_edge(edge, deflection=0.1):
    curve_adaptator = BRepAdaptor_Curve(edge)

    discretizer = GCPnts_QuasiUniformDeflection()
    discretizer.Initialize(
        curve_adaptator,
        deflection,
        curve_adaptator.FirstParameter(),
        curve_adaptator.LastParameter(),
    )

    if not discretizer.IsDone():
        raise AssertionError("Discretizer not done.")

    points = [
        curve_adaptator.Value(discretizer.Parameter(i)).Coord()
        for i in range(1, discretizer.NbPoints() + 1)
    ]

    return points


def qhull(edges, deflection=0.001):
    pts = flatten([discretize_edge(e.wrapped, deflection) for e in edges])
    pts2d = [pt[:2] for pt in pts]
    ch = ConvexHull(pts2d)

    polygon = [pts[v] for v in ch.vertices]
    return Wire.make_polygon(polygon)


pts = ((1, 0), (0, 0), (0.2, 2))

with BuildSketch() as s0:
    with BuildLine():
        Polyline(*pts, close=True)
    MakeFace()
    with Locations((0.4, 0.34)):
        Circle(0.35, mode=Mode.SUBTRACT)

hull_wire = qhull(s0.edges())

# %%

with BuildSketch() as b:
    Rectangle(2, 4)
    with Locations((0, 2)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((1, 1)):
        Circle(1.1, mode=Mode.SUBTRACT)
    with Locations((0, 0)):
        Circle(0.5, mode=Mode.SUBTRACT)
    with Locations((-0.51, -1)):
        Circle(0.5, mode=Mode.SUBTRACT)
    with Locations((-0.1, -1.5)):
        Circle(0.2, mode=Mode.SUBTRACT)
    with Locations((0.5, -1.5)):
        Circle(0.35, mode=Mode.SUBTRACT)
    with Locations((-0.7, -2)):
        Circle(0.5, mode=Mode.SUBTRACT)
    with Locations((-1, 0)):
        Circle(0.4, mode=Mode.SUBTRACT)
    with Locations((-1, 2)):
        Circle(0.5, mode=Mode.ADD)

hull_wire = qhull(b.edges(), 0.001)

show(b, hull_wire, reset_camera=False)

# %%
with BuildSketch() as b:
    Rectangle(2, 4)
    with Locations((0.4, 2)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((0, 0)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((-0.4, -2)):
        Circle(0.9, mode=Mode.ADD)
hull_wire = qhull(b.edges(), 0.001)
hull2 = find_hull(b.edges())
show_object(b, "b", clear=True, reset_camera=False)
show_object(hull_wire, "hull", reset_camera=False)
show_object(hull2, "hull2", reset_camera=False)

# %%
def vx(v):
    return Vertex(*v.to_tuple())


# %%
pts = ((1, 0), (0, 0), (0.2, 2))

with BuildSketch() as s0:
    with BuildLine():
        Polyline(*pts, close=True)
    MakeFace()
    with Locations((0.4, 0.34)):
        Circle(0.35, mode=Mode.SUBTRACT)

# %%

with BuildSketch() as s1:
    with BuildLine():
        Polyline(*pts, close=True)
    MakeFace()
    with Locations((0.4, 0.352)):
        Circle(0.35, mode=Mode.SUBTRACT)

h = s0.faces()[0]
h2 = Face.make_from_wires(h.outer_wire())
show_object(h, "h", reset_camera=False, clear=True)
show_object(vx(h2.center()), "center_h", reset_camera=False)

find_hull(s0.edges())

f = s1.faces()[0]
f2 = Face.make_from_wires(f.outer_wire())
show_object(f, "f", reset_camera=False)
show_object(vx(f2.center()), "center_g", reset_camera=False)


# %%
import math


def deg(rad):
    return rad / math.pi * 180.0


arcs, points = convert_and_validate(b.edges())
show(
    b,
    *[
        Edge.make_circle(
            arc.r,
            Plane(origin=(arc.c.x, arc.c.y, 0), x_dir=(1, 0, 0)),
            deg(arc.a1),
            deg(arc.a2),
        )
        for arc in arcs
    ],
    *[Vertex(v.x, v.y, 0) for v in points],
)


# %%

with BuildLine() as l:
    RadiusArc((0, 0), (1, 1), 2)

show(l)
# %%


# from OCP.gp import gp_Vec, gp_Pnt
# from OCP.BRepGProp import BRepGProp_Face, BRepGProp
# from OCP.GProp import GProp_GProps

# Compound Solid Shell Face Wire Edge Vertex


# def center(self, center_of=CenterOf.GEOMETRY):

#     if center_of == CenterOf.MASS:
#         properties = GProp_GProps()
#         BRepGProp.SurfaceProperties_s(obj.wrapped, properties)
#         p = properties.CentreOfMass()

#     elif center_of == CenterOf.BOUNDING_BOX:
#         p = self.bounding_box().center

#     elif center_of == CenterOf.GEOMETRY:
#         u0, u1, v0, v1 = self._uv_bounds()
#         u = 0.5 * (u0 + u1)
#         v = 0.5 * (v0 + v1)

#         p = gp_Pnt()
#         vn = gp_Vec()
#         BRepGProp_Face(self.wrapped).Normal(u, v, p, vn)

#     else:
#         raise ValueError(f"Unknown CenterOf value {center_of}")

#     return Vector(p)


COM = CenterOf.MASS
COB = CenterOf.BOUNDING_BOX
COG = CenterOf.GEOMETRY

# %%
with BuildPart() as cyl:
    Cylinder(1, 2)

with BuildPart() as box:
    Box(1, 2, 3)

with BuildPart() as sphere:
    Sphere(1)

with BuildPart() as cone:
    Cone(1, 0, 1)

with BuildPart() as torus:
    Torus(3, 0.75)

with BuildPart() as revolv:
    with BuildSketch():
        with BuildLine():
            Polyline(
                (0, 0), (2, 0), (1, 1), (1, 2), (2, 3), (3, 4.5), (0, 5), close=True
            )
        MakeFace()
    Revolve(axis=Axis.Y)

with BuildPart() as revolv2:
    with BuildSketch() as s:
        with BuildLine() as l:
            Spline(
                (0, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (2, 3),
                (3, 5),
                (0, 4),
            )

            Line((0, 0), (0, 4))
        MakeFace()
    Revolve(axis=Axis.Y)

with BuildPart() as revolv3:
    with BuildSketch() as s:
        with BuildLine() as l:
            Spline(
                (0, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (2, 3),
                (3, 5),
                (0, 7),
            )

            Line((0, 0), (0, 7))
        MakeFace()
    Revolve(axis=Axis.Y)

with BuildPart() as extrude:
    with BuildSketch() as s:
        Ellipse(1, 3)
    Extrude(amount=3)

with BuildPart() as extrude:
    with BuildSketch() as s:
        with BuildLine() as l:
            Spline(
                (0, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (2, 3),
                (3, 5),
                (-1, 2),
                (0, 0),
            )
        MakeFace()
    Extrude(amount=3)

with BuildSketch() as concav:
    with BuildLine():
        Polyline((0, 1), (0, 0), (1, 0))
        ThreePointArc((0, 1), (0.9, 0.2), (1, 0))
    MakeFace()

with BuildSketch() as convex:
    with BuildLine():
        Polyline((0, 1), (0, 0), (1, 0))
        ThreePointArc((0, 1), (0.3, 0.3), (1, 0))
    MakeFace()

with BuildSketch() as triangle:
    with BuildLine():
        Polyline((0, 1), (0, 0), (1, 0), close=True)
    MakeFace()

with BuildPart() as sph_hole:
    Sphere(2)
    with Locations((0, 1)):
        Box(4, 2, 4, mode=Mode.SUBTRACT)
    with Workplanes(sph_hole.faces().sort_by()[-1]):
        with Locations((3, 0)):
            Box(4, 4, 4, rotation=(0, 0, 45), mode=Mode.SUBTRACT)

# %%

with BuildPart() as obj:
    Sphere(1)
    with Locations((2.5, 0)):
        Sphere(2.2, mode=Mode.SUBTRACT)
    Fillet(obj.edges()[1], radius=0.3)

show(obj)


# %%

f = sph_hole.faces().sort_by(Axis.Y)[0]
show(sph_hole, f, vx(f.get_center(CenterOf.GEOMETRY)))


# %%

with BuildPart() as cyl_hole:
    Cylinder(2, 4)
    with Workplanes(Plane.YZ):
        Cylinder(1, 4, mode=Mode.SUBTRACT)

show(cyl_hole)

# %%
f = cyl_hole.faces()[0]
show(f, vx(center(f, COG)))

# %%
f = cyl.faces()[0]
show(f, vx(center(f, COG)))

# %%
f = box.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = sphere.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = cone.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = torus.faces()[0]
show(f, vx(center(f, COG)))

# %%

show_object(revolv, clear=True)
for i in range(1, 6):
    f = revolv.faces()[i]
    show_object(f, f"face{i}")
    show_object(vx(center(f, COG)), f"center{i}")

# %%

f = revolv2.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = revolv3.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = extrude.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = extrude.faces()[0]
show(f, vx(center(f, COG)))

# %%

reset_show()
set_defaults(reset_camera=False)

# %%

f = concav.faces()[0]
show(f, vx(center(f, COG)), reset_camera=False, transparent=True)

# %%

f = convex.faces()[0]
show(f, vx(center(f, COG)), reset_camera=False, transparent=True)

# %%

f = triangle.faces()[0]
show(f, vx(center(f, COG)), reset_camera=False, transparent=True)

# %%

f = o.faces().sort_by(Axis.Y)[-1]
show(f, vx(center(f, COG)))

# %%

from build123d import *
from build123d.direct_api import Shape

from typing import Union


def center(obj, center_of=None):
    if center_of is None:
        return obj.center
    elif center_of == CenterOf.MASS:
        return obj.center_of_mass
    elif center_of == CenterOf.GEOMETRY:
        return obj.center_of_geometry
    elif center_of == CenterOf.BOUNDING_BOX:
        bb = obj.bounding_box()
        return bb.center


def group_by(
    self,
    group_by: Union[Axis, SortBy] = Axis.Z,
    center_of=None,
    reverse=False,
    tol_digits=6,
):
    groups = {}
    for obj in self:
        if center_of is None:
            key = group_by.to_plane().to_local_coords(obj).center.Z
        else:
            key = group_by.to_plane().to_local_coords(obj).get_center(center_of).Z

        key = round(key, tol_digits)

        if groups.get(key) is None:
            groups[key] = [obj]
        else:
            groups[key].append(obj)

    return [
        ShapeList(el[1])
        for el in sorted(groups.items(), key=lambda o: o[0], reverse=reverse)
    ]


# monkey patch for the sake of the argument:
ShapeList.group_by = group_by
Face.get_center = center

boxes = []
for y in [-1.2, 0, 1.2]:
    with BuildPart() as box:
        with Locations((0, y, 0)):
            Box(1, 1, 1)
            Chamfer(*box.edges(), length=0.2)
    boxes.append(box)

for i in range(3):
    print(boxes[i])
    show_object(boxes[i], "box", reset_camera=True)
show_object(boxes[0].faces().group_by(Axis.Z, center_of=CenterOf.MASS)[-2], "mass")
show_object(
    boxes[1].faces().group_by(Axis.Z, center_of=CenterOf.GEOMETRY)[-2], "geometry"
)
show_object(
    boxes[2].faces().group_by(Axis.Z, center_of=CenterOf.BOUNDING_BOX)[-2], "bb"
)

# %%

import cadquery as cq

obj = cq.Workplane().box(2, 4, 0.1)
obj = obj.cut(cq.Workplane().cylinder(0.1, 0.9))
obj = obj.cut(cq.Workplane().cylinder(0.1, 0.9).translate((0.4, 2, 0)))
obj = obj.union(cq.Workplane().cylinder(0.1, 0.9).translate((-0.4, -2, 0)))

face = obj.faces(">Z")

hull = cq.hull.find_hull(face.edges().vals())
show(face, hull, show_parent=False)

# %%

with BuildSketch() as b:
    Rectangle(2, 4)
    with Locations((0.4, 2)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((0, 0)):
        Circle(0.9, mode=Mode.SUBTRACT)
    with Locations((-0.4, -2)):
        Circle(0.9, mode=Mode.ADD)

show(b)


# %%

rv = convert_and_validate(b.edges())

# %%
