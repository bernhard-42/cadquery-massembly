from build123d import *

import numpy as np
from cq_vscode import show, show_object
from jupyter_cadquery.defaults import set_defaults

from cadquery_massembly.build123d import (
    BuildAssembly,
    Mates,
    Part,
    Mate,
    Assemble,
    Color,
)

from cadquery_massembly.build123d.animation import (
    Relocate,
    BuildAnimation,
    Track,
    Animate,
)


# %%

thickness = 2
height = 40
width = 65
length = 100
diam = 4
tol = 0.05

#
# Base and top
#


class Base:
    def __init__(self):
        x1, x2 = 0.63, 0.87
        self.base_hinges = {
            "right_front": (-x1 * length, -x1 * width),
            "right_middle": (0, -x2 * width),
            "right_back": (x1 * length, -x1 * width),
            "left_front": (-x1 * length, x1 * width),
            "left_middle": (0, x2 * width),
            "left_back": (x1 * length, x1 * width),
        }
        self.base_edges = {}

        self.stand_holes = {
            "front_stand": (-0.8 * length, 0),
            "back_stand": (0.75 * length, 0),
        }
        self.stand_edges = {}

        self.obj = None

    def create(self):
        with BuildPart(Plane.YX) as base:
            with BuildSketch():
                Ellipse(length, width)
            Extrude(amount=thickness)

            with Locations((-length + 5, 0, 0)):
                Box(20, 2 * width, 3 * thickness, mode=Mode.SUBTRACT)

            for name, pos in self.base_hinges.items():
                with Locations(pos):
                    Cylinder(
                        diam / 2 + tol,
                        thickness,
                        centered=(True, True, False),
                        mode=Mode.SUBTRACT,
                    )
                self.base_edges[name] = base.edges(Select.LAST).sort_by()[0]

            for name, pos in self.stand_holes.items():
                with Locations(pos):
                    Box(
                        thickness + 2 * tol,
                        width / 2 + 2 * tol,
                        5 * thickness,
                        mode=Mode.SUBTRACT,
                    )
                self.stand_edges[name] = base.edges(Select.LAST).group_by()[0]

        self.obj = base
        return base

    def mates(self):
        m = {name: Mate(edge, name=name) for name, edge in self.base_edges.items()}
        m2 = {name: Mate(edge, name=name) for name, edge in self.stand_edges.items()}
        m.update(m2)
        m["base"] = Mate(self.obj.faces().sort_by()[-1], name="base").translated(
            (0, 0, height + 2 * tol)
        )
        m["top"] = Mate(self.obj.faces().sort_by()[0], name="top")
        return m


#
# Stands
#


class Stand:
    def __init__(self):
        self.h = 5

    def create(self):
        with BuildPart(Plane.YX) as stand:
            b = Box(width / 2 + 10, height + 2 * tol, thickness)
            faces = b.faces().sort_by(Axis.X)

            t2 = thickness / 2
            w = height / 2 + tol - self.h / 2
            with Locations((0, -w, t2), (0, w, t2)):
                with BuildSketch():
                    Rectangle(thickness, self.h)
                Extrude(amount=self.h)

            Chamfer(
                *stand.edges().group_by()[0].sort_by(Axis.X)[3:5],
                length=self.h - 2 * tol,
            )

            with Workplanes(faces[0], faces[-1]):
                Box(thickness, width / 2, thickness, centered=(True, True, False))

        self.obj = stand
        return stand

    def mates(self):
        return {"bottom": Mate(self.obj.faces().sort_by(Axis.X)[0], name="bottom")}


#
# Legs
#


class UpperLeg:
    def __init__(self):
        self.l1 = 50
        self.l2 = 80
        self.obj = None

    def create(self):
        points = [(0, 0), (0, height / 2), (self.l1, height / 2 - 5), (self.l2, 0)]
        upper_leg_hole = (self.l2 - 10, 0)

        with BuildPart(Plane.YX) as upper_leg:
            with BuildSketch():
                with BuildLine():
                    Polyline(*points)
                    Mirror(about=Plane.XZ)
                MakeFace()
            Extrude(amount=thickness)
            Fillet(upper_leg.edges().sort_by(Axis.Y)[-1], radius=4)

            with Locations(upper_leg_hole):
                Hole(diam / 2 + tol)

            with Workplanes(Plane((0, 0, -thickness / 2), (0, 1, 0), ((1, 0, 0)))):
                Cylinder(
                    diam / 2,
                    2 * (height / 2 + thickness + tol),
                    centered=(True, True, True),
                )
        self.obj = upper_leg
        return upper_leg

    def mates(self):
        m = {
            f"knee_{suffix}": Mate(
                self.obj.edges().group_by(Axis.Y)[-3].sort_by()[ind],
                name=f"knee_{suffix[ind]}",
            )
            for ind, suffix in enumerate(["top", "bottom"])
        }
        m["hinge"] = Mate(self.obj.faces().sort_by(Axis.X)[0], name=f"hinge")
        return m


class LowerLeg:
    def __init__(self):
        self.w = 15
        self.l1 = 20
        self.l2 = 120
        self.obj = None

    def create(self):
        points = [(0, 0), (self.l1, self.w), (self.l2, 0)]
        upper_leg_hole = (self.l1 - 10, 0)

        with BuildPart(Plane.YX) as lower_leg:
            with BuildSketch():
                with BuildLine():
                    Polyline(*points)
                    Mirror(about=Plane.XZ)
                MakeFace()
            Extrude(amount=thickness)
            Fillet(*lower_leg.edges().filter_by(Axis.Z), radius=4)

            with Locations(upper_leg_hole):
                Hole(diam / 2 + tol)

        self.obj = lower_leg
        return lower_leg

    def mates(self):
        return {
            f"knee_{suffix}": Mate(
                self.obj.edges().group_by(Axis.Y)[4].sort_by()[ind],
                name=f"knee_{suffix}",
            )
            for ind, suffix in enumerate(["top", "bottom"])
        }


set_defaults(mate_scale=3)

# %%

_base = Base()
base = _base.create()
show_object(base, name="base", mates=_base.mates(), clear=True, transparent=True)

# %%

_stand = Stand()
stand = _stand.create()
show_object(stand, name="stand", mates=_stand.mates(), clear=True, transparent=True)

# %%

_upper_leg = UpperLeg()
upper_leg = _upper_leg.create()
show_object(
    upper_leg.part,
    name="upper_leg",
    mates=_upper_leg.mates(),
    clear=True,
    transparent=True,
)

# %%

_lower_leg = LowerLeg()
lower_leg = _lower_leg.create()
show_object(
    lower_leg.part,
    name="lower_leg",
    mates=_lower_leg.mates(),
    clear=True,
    transparent=True,
)


# %%

#
# Assembly
#


def base_rot(mate):
    angles = {
        "right_back": -105,
        "right_middle": -90,
        "right_front": -75,
        "left_back": 105,
        "left_middle": 90,
        "left_front": 75,
    }
    angle = angles.get(mate.name, 0)
    if angle == 0:
        return mate
    else:
        return mate.rotated((0, 180, angle))


with BuildAssembly(name="hexapod") as a:

    with Mates(*[base_rot(v) for k, v in _base.mates().items() if k != "top"]):
        Part(base, name="base", color=Color("gray"))

    with Mates(_base.mates()["top"]):
        Part(base, name="top", color=Color(204, 204, 204))

    for name in _base.stand_holes.keys():
        with Mates(_stand.mates()["bottom"].renamed(f"{name}_bottom")):
            Part(stand, name=name, color=Color(128, 204, 230))

    for name in _base.base_hinges.keys():
        with BuildAssembly():

            m = _upper_leg.mates()
            suffix = "bottom" if "left" in name else "top"
            with Mates(
                m["knee_" + suffix].renamed(f"{name}_knee"),
                m["hinge"].renamed(f"{name}_hinge").set_origin(),
            ):
                Part(upper_leg, name=f"{name}_leg")

            with BuildAssembly():
                m = _lower_leg.mates()
                suffix = "top" if "left" in name else "bottom"
                with Mates(
                    m["knee_" + suffix]
                    .renamed(f"{name}_lower_knee")
                    .rotated((0, 0, -75))
                    .set_origin()
                ):
                    Part(lower_leg, name=f"{name}_lower")

    Relocate()

    for name in _base.base_hinges.keys():
        Assemble(f"{name}_hinge", name)
        Assemble(f"{name}_lower_knee", f"{name}_knee")

    for pos in ["front", "back"]:
        Assemble(f"{pos}_stand_bottom", f"{pos}_stand")

    Assemble("top", "base")

show(a, render_mates=True, mate_scale=5, reset_camera=True)

print("\nAssembled objects:")
for p in sorted(a.assembly.objs.keys()):
    print("  ", p)

# %%

#
# Animation
#


def time_range(end, count):
    return np.linspace(0, end, count + 1)


def vertical(count, end, offset):
    ints = [min(180, (90 + i * (360 // count)) % 360) for i in range(count)]
    heights = [round(20 * np.sin(np.deg2rad(x) - 15), 1) for x in ints]
    heights.append(heights[0])
    return time_range(end, count), heights[offset:] + heights[1 : offset + 1]


def horizontal(end, reverse):
    horizontal_angle = 25
    angle = horizontal_angle if reverse else -horizontal_angle
    return time_range(end, 4), [0, angle, 0, -angle, 0]


with BuildAnimation():
    leg_group = ("left_front", "right_middle", "left_back")

    for name in _base.base_hinges.keys():
        times, values = horizontal(4, "middle" in name)
        Track(f"/hexapod/{name}_leg", "rz", times, values)

        times, values = vertical(8, 4, 0 if name in leg_group else 4)
        Track(f"/hexapod/{name}_leg/{name}_lower", "rz", times, values)

    Animate(2)

# %%
