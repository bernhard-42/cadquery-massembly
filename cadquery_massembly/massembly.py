from math import pi
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Dict, List, overload

from cadquery import Workplane, Location, Assembly
from .mate import Mate
from .geom import Circle

Selector = Tuple[str, Union[str, Tuple[float, float]]]


@dataclass
class MateDef:
    mate: Mate
    assembly: "MAssembly"
    origin: bool

    @property
    def world_mate(self):
        mate = self.mate
        assembly = self.assembly

        while assembly is not None:
            mate = mate.moved(assembly.loc)
            assembly = assembly.parent

        return mate


@dataclass
class DOF:
    mate_name: str
    target_mate_name: str
    dof: str


class MAssembly(Assembly):
    def __init__(self, *args, **kwargs):
        self.mates: Dict[str, MateDef] = {}
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"MAssembly('{self.name}', objects: {len(self.objects)}, children: {len(self.children)})"

    @classmethod
    def from_assembly(cls, assembly):
        def _from_assembly(assembly):
            massembly = cls(obj=assembly.obj, name=assembly.name, loc=assembly.loc, color=assembly.color)
            for child in assembly.children:
                massembly.add(_from_assembly(child), name=f"{child.name}")
            return massembly

        return _from_assembly(assembly)

    def dump(self):
        def fqpath(assy):
            result = assy.name
            p = assy.parent
            while p:
                result = f"{p.name}/{result}"
                p = p.parent
            return result

        def to_string(assy, matelist, ind="") -> str:
            fq = fqpath(assy)
            result = f"\n{ind}MAssembly(name: '{assy.name}', 'fq: '{fq}', loc: {assy.loc} obj_hash: {assy.obj.__hash__()})\n"
            for name in matelist.get(fq, []):
                result += f"{ind}  - {name:20s}: mate={self.mates[name].mate} origin={self.mates[name].origin}\n"
            for c in assy.children:
                result += to_string(c, matelist, ind + "    ")
            return result

        matelist: Dict[str, List[str]] = {}
        for k, v in ((k, fqpath(v.assembly)) for k, v in self.mates.items()):
            if matelist.get(v) is None:
                matelist[v] = [k]
            else:
                matelist[v].append(k)

        print(to_string(self, matelist, ""))

    @overload
    def mate(
        self, id: str, mate: Mate, name: str, origin: bool = False, transforms: Union[Dict, OrderedDict] = None
    ) -> "MAssembly":
        """
        Add a mate to an assembly
        :param id: id (path) to an assembly
        :param mate: mate to add to the assembly defined by path
        :param name: name of the new mate
        :param transforms: an ordered dict of rx, ry, rz, tx, ty, tz transformations
        :param origin Whether this mate is the origin of the assembly
        :return: Mate
        """
        ...

    @overload
    def mate(
        self, query: str, name: str, origin: bool = False, transforms: Union[Dict, OrderedDict] = None
    ) -> "MAssembly":
        """
        Add a mate to an assembly
        :param query: an object assembly
        :param name: name of the new mate
        :param transforms: an ordered dict of rx, ry, rz, tx, ty, tz transformations
        :param origin Whether this mate is the origin of the assembly
        :return: Mate
        """
        ...

    def mate(self, *args, name: str, origin: bool = False, transforms: Union[Dict, OrderedDict] = None) -> "MAssembly":
        if len(args) == 1:
            query = args[0]
            id, obj = self._query(query)
            mate = Mate(obj)
        elif len(args) == 2:
            id, mate = args
        else:
            raise RuntimeError("Wrong number of arguments, valid are 'id, mate' or 'query'")

        assembly = self.objects[id]
        if transforms is not None:
            for k, v in transforms.items():
                mate = getattr(mate, k)(v)
        self.mates[name] = MateDef(mate, assembly, origin)

        return self

    def assemble(
        self,
        object_name: str,
        target: Union[str, Location],
        joint1: DOF = None,
        joint2: DOF = None,
        solution: int = 0,
    ) -> Optional["MAssembly"]:
        """
        Translate and rotate a mate onto a target mate
        :param mate: name of the mate to be assembled
        :param target: name of the target mate or a Location object to assemble the mate to
        :return: self
        """

        def align_mates():
            v1 = self.mates[object_name].world_mate.x_dir
            v2 = self.mates[target].world_mate.x_dir
            z = self.mates[target].world_mate.z_dir

            angle = v1.wrapped.AngleWithRef(v2.wrapped, z.wrapped) / pi * 180
            self.mates[object_name].mate.rz(angle)

        if joint1 is None and joint2 is None:

            o_mate, o_assy = self.mates[object_name].mate, self.mates[object_name].assembly
            if isinstance(target, str):
                t_mate, t_assy = self.mates[target].mate, self.mates[target].assembly
                if o_assy.parent == t_assy.parent or o_assy.parent is None:
                    o_assy.loc = t_assy.loc
                else:
                    o_assy.loc = t_assy.loc * o_assy.parent.loc.inverse
                o_assy.loc = o_assy.loc * t_mate.loc * o_mate.loc.inverse
            else:
                o_assy.loc = target

        elif joint2 is None:
            self.assemble(joint1.mate_name, joint1.target_mate_name)

            w_mate1 = self.mates[object_name].world_mate
            w_mate2 = self.mates[target].world_mate

            joint_mate = self.mates[joint1.mate_name].mate
            w_joint_mate = self.mates[joint1.mate_name].world_mate

            if joint1.dof == "rz":
                proj_mate1 = (w_mate1.origin - w_joint_mate.origin).projectToLine(
                    w_joint_mate.z_dir
                ) + w_joint_mate.origin

                proj_mate2 = (w_mate2.origin - w_joint_mate.origin).projectToLine(
                    w_joint_mate.z_dir
                ) + w_joint_mate.origin

                v1 = proj_mate1 - w_mate1.origin
                v2 = proj_mate2 - w_mate2.origin
                z = w_joint_mate.z_dir
                angle = v2.wrapped.AngleWithRef(v1.wrapped, z.wrapped) / pi * 180
                joint_mate.rz(angle)

                self.assemble(joint1.mate_name, joint1.target_mate_name)

                # Finally align mates of object and target
                align_mates()

                if (self.mates[object_name].world_mate.origin - self.mates[target].world_mate.origin).Length > 1e-6:
                    print("Warning: Mates for target and object don't coincide")
                    print(self.mates[object_name].world_mate.origin)
                    print(self.mates[target].world_mate.origin)
            else:
                raise ValueError(f"DOF {joint1.dof} not supported")

        elif isinstance(target, str):

            self.assemble(joint1.mate_name, joint1.target_mate_name)
            self.assemble(joint2.mate_name, joint2.target_mate_name)

            w_mate1 = self.mates[object_name].world_mate
            joint_mate1 = self.mates[joint1.mate_name].mate
            w_joint_mate1 = self.mates[joint1.mate_name].world_mate

            w_mate2 = self.mates[target].world_mate
            joint_mate2 = self.mates[joint2.mate_name].mate
            w_joint_mate2 = self.mates[joint2.mate_name].world_mate

            # project the mate origin to the rotation axis z_dir
            if joint1.dof == "rz":
                center1 = (w_mate1.origin - w_joint_mate1.origin).projectToLine(
                    w_joint_mate1.z_dir
                ) + w_joint_mate1.origin
                radius1 = (center1 - w_mate1.origin).Length
                circle1 = Circle(radius1, center1, x_dir=w_joint_mate1.x_dir, normal=w_joint_mate1.z_dir)
            else:
                raise ValueError(f"DOF {joint1.dof} not supported")

            if joint2.dof == "rz":
                center2 = (w_mate2.origin - w_joint_mate2.origin).projectToLine(
                    w_joint_mate2.z_dir
                ) + w_joint_mate2.origin
                radius2 = (center2 - w_mate2.origin).Length
                circle2 = Circle(radius2, center2, x_dir=w_joint_mate2.x_dir, normal=w_joint_mate2.z_dir)
            else:
                raise ValueError(f"DOF {joint2.dof} not supported")

            if joint1.dof == "rz" and joint2.dof == "rz":
                points = circle1.intersect(circle2)

                if len(points) > solution:
                    point = points[solution]

                    angle1 = circle1.local_angle(point, w_mate1.origin)
                    angle2 = circle2.local_angle(point, w_mate2.origin)
                    joint_mate1.rz(angle1)
                    joint_mate2.rz(angle2)
                else:
                    raise RuntimeError("Cannot assemble parts")

            self.assemble(joint1.mate_name, joint1.target_mate_name)
            self.assemble(joint2.mate_name, joint2.target_mate_name)

            # Finally alignm mates of object and target
            align_mates()

        else:
            raise ValueError("Wrong parameters")

        return self

    def relocate(self):
        """Relocate the assembly so that all its shapes have their origin at the assembly origin"""

        def _relocate(self, origins):
            origin_mate = origins.get(self.name)
            if origin_mate is not None:
                self.obj = None if self.obj is None else Workplane(self.obj.val().moved(origin_mate.loc.inverse))
                self.loc = Location()
            for c in self.children:
                _relocate(c, origins)

        origins = {mate_def.assembly.name: mate_def.mate for mate_def in self.mates.values() if mate_def.origin}

        # relocate all CadQuery objects
        _relocate(self, origins)

        # relocate all mates
        for mate_def in self.mates.values():
            origin_mate = origins.get(mate_def.assembly.name)
            if origin_mate is not None:
                mate_def.mate = mate_def.mate.moved(origin_mate.loc.inverse)

    def export_mates(self, mate_names):
        """
        Take an existing mates and export them to the top level
        All intermediate locations will be applied
        All non exported mates will be deleted
        :param mate_names: list names of mates to be exported
        :return: self
        """
        new_mates = []
        for name, mate_def in self.mates.items():
            if mate_names.get(name) is not None:
                new_mates.append((self.name, mate_def.world_mate, mate_names.get(name)))

        self.mates = {}
        for mate_def in new_mates:
            self.mate(mate_def[0], mate_def[1], name=mate_def[2])

        return self

    def import_mate(self, assembly, mate_name, target_assembly_name, target_mate_name, transforms=None, origin=False):
        """
        Import mates from an import Massembly
        :param assembly: the imported assembly
        :param mate_name: name of the mate to be imported
        :param target_assembly_name: name of the target assembly to attach the imported mate
        :param target_mate_name: unique name of the target mate
        :param transforms: an ordered dict of rx, ry, rz, tx, ty, tz transformations
        :param origin Whether this mate is the origin of the assembly
        :return: self
        """
        if target_mate_name in list(self.mates):
            raise ValueError("Mate name already exists")

        mate_def = assembly.mates[mate_name]
        self.mate(
            target_assembly_name,
            mate_def.mate.copy(),
            name=target_mate_name,
            origin=origin,
            transforms=transforms,
        )
