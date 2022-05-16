from math import pi

from cadquery import Plane, Vector, Workplane, Edge, Wire
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Ax1
from OCP.Geom import Geom_Circle, Geom_Line
from OCP.GeomAPI import GeomAPI_ExtremaCurveCurve


def _geom_circle(radius, origin, x_dir, z_dir):
    p = gp_Pnt(origin.x, origin.y, origin.z)
    n = gp_Dir(z_dir.x, z_dir.y, z_dir.z)
    x = gp_Dir(x_dir.x, x_dir.y, x_dir.z)
    a = gp_Ax2(p, n, x)
    return Geom_Circle(a, radius)


def _geom_line(origin, direction):
    a = gp_Ax1(origin.toPnt(), direction.toDir())
    return Geom_Line(a)


class Intersector:
    def __init__(self, c1, c2, tol=1e-6):
        self.intersector = GeomAPI_ExtremaCurveCurve(c1.wrapped, c2.wrapped)
        self.tol = tol

    def get_points(self):
        result = []
        for i in range(self.intersector.NbExtrema()):
            if self.intersector.Distance(i + 1) < self.tol:
                p = gp_Pnt()
                self.intersector.Points(i + 1, p, p)  # p1 == p2 in this case
                result.append(Vector(p))
        return result

    def get_point(self):
        points = self.get_points()
        return None if len(points) == 0 else points[0]


class Line:
    def __init__(self, origin, direction):
        self.origin = Vector(origin)
        self.direction = Vector(direction).normalized()
        self.wrapped = _geom_line(self.origin, self.direction)

    def intersect(self, line, tol=1e-6):
        if isinstance(line, Line):
            intersector = Intersector(self, line, tol)
            return intersector.get_point()
        else:
            raise ValueError("Only Line allowed")

    def shape(self, scale=5):
        return Edge.makeLine(self.origin + scale * self.direction, self.origin - scale * self.direction)


class Circle(Plane):
    def __init__(self, radius, origin, x_dir=None, normal=(0, 0, 1)):
        super().__init__(origin, xDir=x_dir, normal=normal)

        self.radius = radius
        self.wrapped = _geom_circle(radius, self.origin, self.xDir, self.zDir)

    @classmethod
    def from_points(cls, point1, point2, point3):
        v1 = Vector(point1)
        v2 = Vector(point2)
        v3 = Vector(point3)

        normal = (v2 - v1).cross(v3 - v1).normalized()

        p2 = (v1 + v2) / 2
        d2 = normal.cross((v2 - v1).normalized())
        l2 = Line(p2, d2)

        p3 = (v1 + v3) / 2
        d3 = normal.cross((v3 - v1).normalized())
        l3 = Line(p3, d3)

        origin = l2.intersect(l3)
        return cls((origin - v1).Length, origin, normal=normal)

    @classmethod
    def through_point(cls, origin, point, xDir):
        origin = Vector(origin)
        point = Vector(point)
        xDir = Vector(xDir).normalized()
        normal = xDir.cross((origin - point).normalized())
        return cls((origin - point).Length, origin, xDir=xDir, normal=normal)

    def on_plane(self, point):
        projected_point = point.projectToPlane(self)
        return (point - projected_point).Length < self._eq_tolerance_origin

    def same_plane(self, circle):
        return abs(abs(abs(self.zDir.dot(circle.zDir))) - 1) < self._eq_tolerance_origin and self.on_plane(
            circle.origin
        )

    def intersect(self, obj, tol=1e-6):
        if isinstance(obj, (Circle, Line)):
            intersector = Intersector(self, obj, tol)
            return intersector.get_points()
        else:
            raise ValueError("Only Circle and Line allowed")

    def local_angle(self, p1, p2):
        return (p1 - self.origin).wrapped.AngleWithRef((p2 - self.origin).wrapped, self.zDir.wrapped) / pi * 180

    def shape(self):
        return Workplane(Wire.makeCircle(self.radius, self.origin, self.zDir))
