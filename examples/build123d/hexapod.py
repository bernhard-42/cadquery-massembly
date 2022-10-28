from cadquery_massembly.build123d import BuildAssembly, Mates, Part, Mate, Assemble
from build123d import *
from cq_vscode import show, show_object

thickness = 2
height = 40
width = 65
length = 100
diam = 4
tol = 0.05


class Base:
    def __init__(self):
        x1, x2 = 0.63, 0.87
        self.base_hinges = {
            "right_back": {"pos": (-x1 * length, -x1 * width), "angle": -105},
            "right_middle": {"pos": (0, -x2 * width), "angle": -90},
            "right_front": {"pos": (x1 * length, -x1 * width), "angle": -75},
            "left_back": {"pos": (-x1 * length, x1 * width), "angle": 105},
            "left_middle": {"pos": (0, x2 * width), "angle": 90},
            "left_front": {"pos": (x1 * length, x1 * width), "angle": 75},
        }
        self.base_edges = {}

        self.stand_holes = {
            "front_stand": (0.75 * length, 0),
            "back_stand": (-0.8 * length, 0),
        }
        self.stand_edges = {}
        self.obj = None

    def create(self):
        with BuildPart() as base:
            with BuildSketch():
                Ellipse(length, width)
            Extrude(amount=thickness)

            with Locations((length - 5, 0, 0)):
                Box(20, 2 * width, 3 * thickness, mode=Mode.SUBTRACT)

            for name, pos in self.base_hinges.items():
                with Locations(pos["pos"]):
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
                self.stand_edges[name] = base.edges(Select.LAST).sort_by()[0]

        self.obj = base
        return base

    def mates(self, names):
        m = []
        if "holes" in names:
            m += [
                Mate(edge, name=name).rotated((0, 0, self.base_hinges[name]["angle"]))
                for name, edge in self.base_edges.items()
            ]
        if "base" in names:
            m += [
                Mate(self.obj.faces().sort_by()[-1], name="base").translated(
                    (0, 0, height + 2 * tol)
                )
            ]
        if "top" in names:
            m += [Mate(self.obj.faces().sort_by()[-1], name="top")]
        return m


class Stand:
    def __init__(self):
        self.h = 5

    def create(self):
        with BuildPart() as stand:
            b = Box(height, width / 2 + 10, thickness)
            faces = b.faces().sort_by(Axis.Y)

            t2 = thickness / 2
            w = height / 2 - self.h / 4
            with Locations((0, -w, t2), (0, w, t2)):
                with BuildSketch():
                    Rectangle(thickness, self.h)
                Extrude(amount=self.h)

            Chamfer(
                *stand.edges().group_by()[-1].group_by(Axis.Y)[-3], length=self.h - tol
            )
            Chamfer(
                *stand.edges().group_by()[-1].group_by(Axis.Y)[-4],
                length=self.h - 2 * tol,
            )

            with Workplanes(faces[0], faces[-1]):
                Box(thickness, width / 2, thickness, centered=(True, True, False))

        return stand


class UpperLeg:
    def __init__(self):
        self.l1 = 50
        self.l2 = 80
        self.obj = None

    def create(self):
        points = [(0, 0), (0, height / 2), (self.l1, height / 2 - 5), (self.l2, 0)]
        upper_leg_hole = (self.l2 - 10, 0)

        with BuildPart() as upper_leg:
            with BuildSketch():
                with BuildLine():
                    Polyline(*points)
                    Mirror(about=Plane.XZ)
                BuildFace()
            Extrude(amount=thickness)
            Fillet(upper_leg.edges().sort_by(Axis.X)[-1], radius=4)

            with Locations(upper_leg_hole):
                Hole(diam / 2 + tol)

            with Workplanes(Plane((0, 0, thickness / 2), (1, 0, 0), ((0, 1, 0)))):
                Cylinder(
                    diam / 2,
                    2 * (height / 2 + thickness + tol),
                    centered=(True, True, True),
                )
        self.obj = upper_leg
        return upper_leg

    def mates(self, prefix):
        o = -1 if "left" in prefix else 0
        return [
            Mate(upper_leg.faces().sort_by(Axis.Y)[0], name=f"{prefix}_hinge"),
            Mate(
                upper_leg.faces().sort_by()[o].edges().sort_by(Axis.X)[-2],
                name=f"{prefix}_knee",
            ),
        ]


class LowerLeg:
    def __init__(self):
        self.w = 15
        self.l1 = 20
        self.l2 = 120
        self.obj = None

    def create(self):
        points = [(0, 0), (self.l1, self.w), (self.l2, 0)]
        upper_leg_hole = (self.l1 - 10, 0)

        with BuildPart() as lower_leg:
            with BuildSketch():
                with BuildLine():
                    Polyline(*points)
                    Mirror(about=Plane.XZ)
                BuildFace()
            Extrude(amount=thickness)
            Fillet(*lower_leg.edges().filter_by_axis(Axis.Z), radius=4)

            with Locations(upper_leg_hole):
                Hole(diam / 2 + tol)

        self.obj = lower_leg
        return lower_leg

    def mates(self, prefix):
        o = 0 if "left" in prefix else -1
        return [
            Mate(
                self.obj.faces().sort_by()[o].edges().sort_by(Axis.X)[3],
                name=f"{prefix}_lower_knee",
            ).rotated((0, 0, -75))
        ]


_base = Base()
base = _base.create()
show_object(base, name="base", clear=True)

_stand = Stand()
stand = _stand.create()
show_object(stand.part.translate((0, 100, 0)), name="stand")

_upper_leg = UpperLeg()
upper_leg = _upper_leg.create()
show_object(upper_leg.part.translate((20, -100, 0)), name="upper_leg")

_lower_leg = LowerLeg()
lower_leg = _lower_leg.create()
show_object(lower_leg.part.translate((-100, -100, 0)), name="lower_leg")


# %%
with BuildAssembly(name="hexapod") as a:

    with Mates(*_base.mates(["holes", "base"])):
        Part(base, name="base")

    with Mates(*_base.mates(["top"])):
        Part(base, name="top")

    for name in _base.base_hinges.keys():
        with BuildAssembly(name=f"{name}_leg"):
            with Mates(*_upper_leg.mates(name)):
                Part(upper_leg, name=f"{name}_upper")

            with Mates(*_lower_leg.mates(name)):
                Part(lower_leg, name=f"{name}_lower")

        Assemble(f"{name}_hinge", name)
        Assemble(f"{name}_lower_knee", f"{name}_knee")
    Assemble("top", "base")

show(a, render_mates=True, mate_scale=5, reset_camera=True)
# %%
