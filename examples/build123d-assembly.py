# %reset -f
from cadquery_massembly.build123d import BuildAssembly, Mates, Part, Mate, Assemble
from build123d import *
from cq_vscode import show, show_object

# %%

with BuildPart() as b:
    Box(1, 2, 3)
    Chamfer(*b.edges(), length=0.2)
    # Fillet(*b.edges(), radius=0.2)

with BuildPart() as s:
    Sphere(1.2)

with BuildPart() as c:
    Cylinder(0.3, 2)
    Fillet(*c.edges(), radius=0.1)

fs = b.faces().sort_by(Axis.Z)
c1 = fs[-2].center().Z
c2 = fs[-8].center().Z

print(c1, c2)
# %%

top = Mate(b.faces().sort_by(Axis.Z)[-1], name="top")
edge = Mate(b.edges().sort_by()[-1], name="edge")
pole = Mate(s.edges()[0], name="pole").rotated((0, -45, 0))
center = Mate(s.faces()[0], name="center", center_of=CenterOf.BOUNDING_BOX).rotated((30, 0, 0))
circle = Mate(c.faces().sort_by()[-1], name="circle").translated((0, 0, -0.7))

# %%

with BuildAssembly("top") as a:

    with Mates(top, edge):
        Part(b, name="box", loc=Location((0, 3, 0)))

    with Mates(pole, center):
        Part(s, name="sphere", loc=Location((0, -3, 0)))

    with BuildAssembly("sub"):
        with Mates(circle):
            Part(c, name="cylinder")

show(a, render_mates=True, mate_scale=0.2, transparent=True)

# %%

with BuildAssembly("top") as a:

    with Mates(top):
        Part(b, name="box")

    with Mates(pole, center):
        Part(s, name="sphere")

    with BuildAssembly("sub"):
        with Mates(circle):
            Part(c, name="cylinder")

    Assemble("center", "top")
    Assemble("circle", "pole")

# %%

show(a, render_mates=True, mate_scale=0.2, transparent=True)

# %%

mates = []
for i in range(10):
    mates.append(Mate(b.faces().sort_by()[-i], name=f"m{i}", center_of=CenterOf.GEOMETRY))

with BuildAssembly(name="assy") as t:
    with Mates(*mates):
        Part(b, name="box")

show(t, render_mates=True, mate_scale=0.1)
# %%
