import build123d as bd
from cq_vscode import show_object, show, reset_show, set_defaults

# %%
from OCP.gp import gp_Vec, gp_Pnt
from OCP.BRepGProp import BRepGProp_Face, BRepGProp
from OCP.GProp import GProp_GProps


def eq(v1, v2, tol=1e-3):
    return all([abs(bd.Vector(v1) - bd.Vector(v2)) <= tol])


def vx(v):
    return bd.Vertex(*v.to_tuple())


def center(obj: bd.Face, center_of=bd.CenterOf.MASS):
    if center_of == bd.CenterOf.MASS:
        properties = GProp_GProps()
        BRepGProp.SurfaceProperties_s(obj.wrapped, properties)
        return bd.Vector(properties.CentreOfMass())
    elif center_of == bd.CenterOf.BOUNDING_BOX:
        bb = obj.bounding_box()
        return bb.center
    elif center_of == bd.CenterOf.GEOMETRY:
        if obj.geom_type() in [
            "PLANE",
            "CONE",
            "CYLINDER",
            "SPHERE",
            "TORUS",
            "REVOLUTION",
        ]:
            print("UV")
            u0, u1, v0, v1 = obj._uv_bounds()
            u = 0.5 * (u0 + u1)
            v = 0.5 * (v0 + v1)

            p = gp_Pnt()
            vn = gp_Vec()
            BRepGProp_Face(obj.wrapped).Normal(u, v, p, vn)
            return bd.Vector(p)
        else:

            print("MASS")
            return obj.center_of_mass


COM = bd.CenterOf.MASS
COB = bd.CenterOf.BOUNDING_BOX
COG = bd.CenterOf.GEOMETRY

# %%
with bd.BuildPart() as cyl:
    bd.Cylinder(1, 2)

with bd.BuildPart() as box:
    bd.Box(1, 2, 3)

with bd.BuildPart() as sphere:
    bd.Sphere(1)

with bd.BuildPart() as cone:
    bd.Cone(1, 0, 1)

with bd.BuildPart() as torus:
    bd.Torus(3, 0.75)

with bd.BuildPart() as revolv:
    with bd.BuildSketch():
        with bd.BuildLine():
            bd.Polyline(
                (0, 0), (2, 0), (1, 1), (1, 2), (2, 3), (3, 4.5), (0, 5), close=True
            )
        bd.MakeFace()
    bd.Revolve(axis=bd.Axis.Y)

with bd.BuildPart() as revolv2:
    with bd.BuildSketch() as s:
        with bd.BuildLine() as l:
            bd.Spline(
                (0, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (2, 3),
                (3, 5),
                (0, 4),
            )

            bd.Line((0, 0), (0, 4))
        bd.MakeFace()
    bd.Revolve(axis=bd.Axis.Y)

with bd.BuildPart() as revolv3:
    with bd.BuildSketch() as s:
        with bd.BuildLine() as l:
            bd.Spline(
                (0, 0),
                (2, 0),
                (1, 1),
                (1, 2),
                (2, 3),
                (3, 5),
                (0, 7),
            )

            bd.Line((0, 0), (0, 7))
        bd.MakeFace()
    bd.Revolve(axis=bd.Axis.Y)

# %%
f = cyl.faces()[0]
show(f, vx(center(f, COG))No)

# %%
f = box.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = sphere.faces()[0]
show(f, vx(center(f, COG)))

# %%

f = cone.faces()[0]
show(cone, vx(center(f, COG)))

# %%

f = torus.faces()[0]
show(torus, vx(center(f, COG)))

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

reset_show()
set_defaults(reset_camera=False)

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
        self, group_by: Union[Axis, SortBy] = Axis.Z, center_of=None, reverse=False, tol_digits=6
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

# monkey patch fpor the sake of the argument:
ShapeList.group_by = group_by
Face.get_center = center

boxes = []
for y in [-1.2,0,1.2]:
    with bd.BuildPart() as box:
        with Locations((0,y,0)):
            bd.Box(1,1,1)
            bd.Chamfer(*box.edges(), length=0.2)
    boxes.append(box)

for i in range(3):
    print(boxes[i])
    show_object(boxes[i], "box", reset_camera=True)
show_object(boxes[0].faces().group_by(bd.Axis.Z, center_of=CenterOf.MASS)[-2], "mass")
show_object(boxes[1].faces().group_by(bd.Axis.Z, center_of=CenterOf.GEOMETRY)[-2], "geometry")
show_object(boxes[2].faces().group_by(bd.Axis.Z, center_of=CenterOf.BOUNDING_BOX)[-2], "bb")

# %%