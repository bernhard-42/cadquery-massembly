from typing import overload, Union, Tuple
from build123d import (
    Vector,
    VectorLike,
    RotationLike,
    Location,
    Plane,
    Edge,
    Face,
    Wire,
    ShapeList,
    CenterOf,
)


class Mate:
    @overload
    def __init__(
        self,
        name,
        origin: VectorLike = Vector(0, 0, 0),
        x_dir: VectorLike = Vector(1, 0, 0),
        z_dir: VectorLike = Vector(0, 0, 1),
        is_origin: bool = False,
        center_of: CenterOf = CenterOf.BOUNDING_BOX,
    ):
        ...

    @overload
    def __init__(
        self,
        shape: Union[Face, Wire, Edge, ShapeList],
        name: str = "",
        is_origin: bool = False,
        center_of: CenterOf = CenterOf.BOUNDING_BOX,
    ):
        ...

    @overload
    def __init__(
        self,
        plane: Plane,
        name: str = "",
        is_origin: bool = False,
        center_of: CenterOf = CenterOf.BOUNDING_BOX,
    ):
        ...

    def __init__(
        self,
        *args,
        name: str = "",
        is_origin: bool = False,
        center_of: CenterOf = CenterOf.BOUNDING_BOX,
    ):

        self.name = name
        self.is_origin = is_origin

        if len(args) == 1 and isinstance(args[0], Mate):
            val = args[0]

            self.name = val.name
            self.origin = val.origin
            self.x_dir = val.x_dir
            self.y_dir = val.y_dir
            self.z_dir = val.z_dir
            self.is_origin = val.is_origin

        elif len(args) == 1 and isinstance(args[0], Plane):
            val = args[0]

            self.origin = Vector(val.origin.to_tuple())
            self.x_dir = Vector(val.x_dir.to_tuple())
            self.z_dir = Vector(val.z_dir.to_tuple())

        elif len(args) == 1 and isinstance(args[0], Edge):
            val = args[0]

            self.z_dir = val.normal()

            vertices = val.vertices()
            if len(vertices) == 1:  # e.g. a single closed spline
                self.origin = val.center(center_of)
                # Use the vector defined by the vertex and the origin as x direction
                self.x_dir = Vector((vertices[0] - self.origin).to_tuple()).normalized()
            else:
                self.origin = Vector(vertices[0].to_tuple())
                # Use the vector defined by the first two vertices as x direction
                self.x_dir = Vector((vertices[0] - vertices[1]).to_tuple()).normalized()

            self.y_dir = self.z_dir.cross(self.x_dir)

        elif len(args) == 1 and isinstance(args[0], (Face, Wire, ShapeList)):
            val = args[0]

            if isinstance(val, Wire):
                if val.is_closed():
                    val = Face.make_from_wires(val)
                else:
                    raise ValueError("Only closed wires supported")

            elif isinstance(val, ShapeList):
                if all([isinstance(o, Edge) for o in val]):
                    val = Face.make_from_wires(Wire.make_wire(val, sequenced=True))
                else:
                    raise ValueError("Only ShapeLists of Edges supported")

            self.origin = val.center(center_of)

            # x_dir, y_dir will be derived from the local coord system of the underlying plane
            p = val._geom_adaptor().Position()
            xd = p.Ax2().XDirection()
            yd = p.Ax2().YDirection()
            self.x_dir = Vector(xd.X(), xd.Y(), xd.Z())
            self.y_dir = Vector(yd.X(), yd.Y(), yd.Z())
            self.z_dir = self.x_dir.cross(self.y_dir)

        elif len(args) <= 3 and all([isinstance(a, (Vector, tuple)) for a in args]):
            self.origin = Vector(args[0])
            self.x_dir = Vector(args[1]).normalized()
            self.z_dir = Vector(args[2]).normalized()
            self.y_dir = self.z_dir.cross(self.x_dir)

        else:
            raise ValueError(
                f"Needs a 1-3 Vectors or a single Mate, Plane, Face, Edge or Wire, not {args}"
            )

        if self.name == "":
            print(self)
            raise ValueError("name cannot be empty")

    def __repr__(self) -> str:
        c = lambda v: f"({v.X:.2f}, {v.Y:.2f}, {v.Z:.2f})"
        return f"Mate(name='{self.name}', origin={c(self.origin)}, x_dir={c(self.x_dir)}, z_dir={c(self.z_dir)}, is_origin={self.is_origin})"

    @property
    def loc(self) -> Location:
        return Location(self.to_plane())

    @classmethod
    def from_plane(cls, plane: Plane) -> "Mate":
        return cls(plane.origin, plane.x_dir, plane.z_dir)

    def to_plane(self) -> Plane:
        return Plane(self.origin, self.x_dir, self.z_dir)

    def rename(self, name):
        self.name = name
        return self

    def set_origin(self):
        self.is_origin = True
        return self

    def translate(self, vector: VectorLike):
        """
        Translate with a given direction scaled by dist
        :param axis: the direction to translate
        """
        self.origin = self.origin + Vector(vector)

    def translated(self, vector: VectorLike) -> "Mate":
        """
        Return a mate, translated with a given direction scaled by dist
        :param axis: the direction to translate
        """
        mate = Mate(self)  # copy mate
        mate.translate(vector)
        return mate

    def rotate(self, angles: RotationLike):
        """
        Rotate with a given angles in the order x, y, z
        :param angles: (x, y, z) angles to rotate (in degrees)
        """
        plane = self.to_plane().rotated(angles)
        self.origin = plane.origin
        self.x_dir = plane.x_dir
        self.z_dir = plane.z_dir
        self.y_dir = self.z_dir.cross(self.x_dir)

    def rotated(self, angles: RotationLike) -> "Mate":
        """
        Return a new mate, rotated with a given angles in the order x, y, z
        :param angles: (x, y, z) angles to rotate (in degrees)
        :return: self
        """
        mate = Mate(self)  # copy mate
        mate.rotate(angles)
        return mate

    def move(self, loc: Location):
        """
        Move by the given Location
        :param loc: The Location object to move the mate
        """

        def move(origin: Vector, vec: Vector, loc: Location) -> Tuple[Vector, Vector]:
            reloc = Edge.make_line(origin, origin + vec).moved(loc)
            v1, v2 = reloc.start_point(), reloc.end_point()
            return v1, v2 - v1

        origin, x_dir = move(self.origin, self.x_dir, loc)
        _, z_dir = move(self.origin, self.z_dir, loc)

        self.origin = origin
        self.x_dir = x_dir
        self.z_dir = z_dir
        self.y_dir = z_dir.cross(x_dir)

    def moved(self, loc: Location) -> "Mate":
        """
        Return a new mate moved by the given Location
        :param loc: The Location object to move the mate
        :return: Mate
        """
        mate = Mate(self)  # copy mate
        mate.move(loc)
        return mate
