import cadquery as cq


def show_mates(assembly, show_object, length=10):
    radius = length / 10

    for name, mate in assembly.mates.items():
        coord = cq.Assembly(name=name)
        coord.add(cq.Workplane("YZ").circle(radius).extrude(length), color=cq.Color(1, 0, 0))
        coord.add(cq.Workplane("ZX").circle(radius).extrude(length), color=cq.Color(0, 0.5, 0))
        coord.add(cq.Workplane("XY").circle(radius).extrude(length), color=cq.Color(0, 0, 1))
        mloc = mate.mate.loc
        a = mate.assembly
        aloc = a.loc
        while a.parent is not None:
            aloc = a.parent.loc * aloc
            a = a.parent
        coord.loc = aloc * mloc

        show_object(coord, name=f"mate:{name}")
