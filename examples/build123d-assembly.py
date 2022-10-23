from build123d import *
from cadquery_massembly.build123d import BuildAssembly, Mates, Part, Mate, Assemble
from cq_vscode import show, show_object

# %%

with BuildPart() as b:
    Box(1, 2, 3)
    Fillet(*b.edges(), radius=0.2)

with BuildPart() as s:
    Sphere(1.2)

with BuildPart() as c:
    Cylinder(0.3, 2)
    Fillet(*c.edges(), radius=0.1)

# %%

top = Mate(b.faces().sort_by(Axis.Z)[-1], name="top")
pole = Mate(s.edges()[0], name="pole").rotated((0, -45, 0))
center = Mate(s.faces()[0], name="center", center_of=CenterOf.BOUNDING_BOX).rotated((30, 0, 0))
circle = Mate(c.faces().sort_by()[-1], name="circle").translated((0, 0, -0.7))

# %%

with BuildAssembly("top") as a:

    with Mates(top):
        Part(b, name="box")

    with Mates(pole, center):
        Part(s, name="sphere")

    with BuildAssembly("sub"):
        with Mates(circle):
            Part(c, name="cylinder")

# %%

show(a, render_mates=True, mate_scale=0.2, transparent=True)

# %%
