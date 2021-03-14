from collections import OrderedDict as odict
import cadquery as cq
from cadquery_massembly import Mate, MAssembly
from cadquery_massembly.cq_editor import show_mates

r_disk = 100
dist_pivot = 200


def angle_arm(angle_disk):
    ra = np.deg2rad(angle_disk)
    v = np.array((dist_pivot, 0)) - r_disk * np.array((cos(ra), sin(ra)))
    return np.rad2deg(np.arctan2(*v[::-1]))


thickness = 5
nr = 5

disk = cq.Workplane().circle(r_disk + 2 * nr).extrude(thickness)
nipple = cq.Workplane().circle(nr).extrude(thickness)
disk = disk.cut(nipple).union(nipple.translate((r_disk, 0, thickness)))

pivot_base = cq.Workplane().circle(2 * nr).extrude(thickness)
base = (
    cq.Workplane()
    .rect(6 * nr + dist_pivot, 6 * nr)
    .extrude(thickness)
    .translate((dist_pivot / 2, 0, 0))
    .union(nipple.translate((dist_pivot, 0, thickness)))
    .union(pivot_base.translate((0, 0, thickness)))
    .union(nipple.translate((0, 0, 2 * thickness)))
    .edges("|Z")
    .fillet(3)
)
base.faces(">Z[-2]").wires(cq.NearestToPointSelector((dist_pivot + r_disk, 0))).tag("mate")

slot = (
    cq.Workplane()
    .rect(2 * r_disk, 2 * nr)
    .extrude(thickness)
    .union(nipple.translate((-r_disk, 0, 0)))
    .union(nipple.translate((r_disk - 1e-9, 0, 0)))
    .translate((dist_pivot, 0, 0))
)

arm = (
    cq.Workplane()
    .rect(4 * nr + (r_disk + dist_pivot), 4 * nr)
    .extrude(thickness)
    .edges("|Z")
    .fillet(3)
    .translate(((r_disk + dist_pivot) / 2, 0, 0))
    .cut(nipple)
    .cut(slot)
)
arm.faces(">Z").wires(cq.NearestToPointSelector((0, 0))).tag("mate")


def create_disk_arm():
    L = lambda *args: cq.Location(cq.Vector(*args))
    C = lambda *args: cq.Color(*args)

    return (
        MAssembly(base, name="base", color=C("gray"), loc=L(-dist_pivot / 2, 0, 0))
        .add(disk, name="disk", color=C("MediumAquaMarine"), loc=L(r_disk, -1.5 * r_disk, 0))
        .add(arm, name="arm", color=C("orange"), loc=L(0, 10 * nr, 0))
    )


disk_arm = create_disk_arm()

disk_arm.mate("base?mate", name="disk_pivot", origin=True, transforms=odict(rz=180))
disk_arm.mate("base@faces@>Z", name="arm_pivot")
disk_arm.mate("disk@faces@>Z[-2]", name="disk", origin=True)
disk_arm.mate("arm?mate", name="arm", origin=True)

check_mates = True
if check_mates:
    show_object(disk_arm, name="disk_arm")
    show_mates(disk_arm, show_object)
else:
    # Assemble the parts
    disk_arm.assemble("arm", "arm_pivot")
    disk_arm.assemble("disk", "disk_pivot")

    show_object(disk_arm, name="disk_arm")
