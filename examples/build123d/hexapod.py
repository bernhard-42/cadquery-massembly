from build123d import *
from cadquery_massembly.build123d import BuildAssembly, Mates, Part, Mate, Assemble
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
        self.base_holes = {
            "right_back": (-x1 * length, -x1 * width),
            "right_middle": (0, -x2 * width),
            "right_front": (x1 * length, -x1 * width),
            "left_back": (-x1 * length, x1 * width),
            "left_middle": (0, x2 * width),
            "left_front": (x1 * length, x1 * width),
        }
        self.base_edges = {}

        self.stand_holes = {"front_stand": (0.75 * length, 0), "back_stand": (-0.8 * length, 0)}
        self.stand_edges = {}

    def create(self):
        with BuildPart() as base:
            with BuildSketch():
                Ellipse(length, width)
            Extrude(amount=thickness)

            with Locations((length - 5, 0, 0)):
                Box(20, 2 * width, 3 * thickness, mode=Mode.SUBTRACT)

            for name, pos in self.base_holes.items():
                with Locations(pos):
                    Cylinder(diam / 2 + tol, thickness, centered=(True, True, False), mode=Mode.SUBTRACT)
                    self.base_edges[name] = base.edges(Select.LAST).sort_by()[0]

            for name, pos in self.stand_holes.items():
                with Locations(pos):
                    Box(thickness + 2 * tol, width / 2 + 2 * tol, 5 * thickness, mode=Mode.SUBTRACT)
                    self.stand_edges[name] = base.edges(Select.LAST).sort_by()[0]

        return base


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

            Chamfer(*stand.edges().group_by()[-1].group_by(Axis.Y)[-3], length=self.h - tol)
            Chamfer(*stand.edges().group_by()[-1].group_by(Axis.Y)[-4], length=self.h - 2 * tol)

            with Workplanes(faces[0], faces[-1]):
                Box(thickness, width / 2, thickness, centered=(True, True, False))

        return stand


class UpperLeg:
    def __init__(self):
        self.l1 = 50
        self.l2 = 80

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
                Cylinder(diam / 2, 2 * (height / 2 + thickness + tol), centered=(True, True, True))

        return upper_leg


class LowerLeg:
    def __init__(self):
        self.w = 15
        self.l1 = 20
        self.l2 = 120

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

        return lower_leg


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


angles = {
    "right_back": -105,
    "right_middle": -90,
    "right_front": -75,
    "left_back": 105,
    "left_middle": 90,
    "left_front": 75,
}
# %%
with BuildAssembly(name="hexapod") as a:
    mates = [Mate(edge, name=name).rotated((0, 0, angles[name])) for name, edge in _base.base_edges.items()]
    bottom_mate = Mate(base.faces().sort_by()[-1], "top") # .translated(0, 0, height)
    with Mates(*mates, bottom_mate):
        Part(base, name="bottom")

    with Mates(Mate(base.faces().sort_by()[0], "bottom")):
        Part(base, name="bottom")

    for name in _base.base_holes.keys():
        mates = [
            Mate(upper_leg.faces().sort_by(Axis.Y)[0], name=f"{name}_base"),
            Mate(upper_leg.faces().sort_by()[-1].edges().sort_by(Axis.X)[-2], name=f"{name}_knee"),
        ]
        with Mates(*mates):
            Part(upper_leg, name=f"upper_{name}")

        Assemble(f"{name}_base", name)


show(a, render_mates=True, mate_scale=5, reset_camera=False)
# %%
