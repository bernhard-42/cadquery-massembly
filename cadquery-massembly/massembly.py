from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Dict, List, overload

from cadquery import Workplane, Location, Assembly, Shape
from cadquery.assembly import _grammar
from .mate import Mate

Selector = Tuple[str, Union[str, Tuple[float, float]]]


@dataclass
class MateDef:
    mate: Mate
    assembly: "MAssembly"
    origin: bool


class MAssembly(Assembly):
    def __init__(self, *args, **kwargs):
        self.mates: Dict[str, MateDef] = {}
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"MAssembly('{self.name}', objects: {len(self.objects)}, children: {len(self.children)})"

    def dump(self):
        def fqpath(assy):
            result = assy.name
            p = assy.parent
            while p:
                result = f"{p.name}>{result}"
                p = p.parent
            return result

        def to_string(assy, matelist, ind="") -> str:
            fq = fqpath(assy)
            result = f"{ind}MAssembly(name: '{assy.name}', 'fq: '{fq}', obj_hash: {assy.obj.__hash__()})\n"
            result += f"{ind}    mates: {matelist[fq]}\n"
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

    def assemble(self, object_name: str, target: Union[str, Location]) -> Optional["MAssembly"]:
        """
        Translate and rotate a mate onto a target mate
        :param mate: name of the mate to be assembled
        :param target: name of the target mate or a Location object to assemble the mate to
        :return: self
        """
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
        return self
