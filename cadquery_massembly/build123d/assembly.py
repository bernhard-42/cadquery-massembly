from typing import Union, Dict, List

from build123d.direct_api import Location, Compound


class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: float = 1):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def to_tuple(self, percentage=False):
        if percentage:
            return (self.r / 255, self.g / 255, self.b / 255, self.a)
        else:
            return (self.r, self.g, self.b, self.a)

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"


class MAssembly:
    def __init__(
        self,
        obj: Union["MAssembly", Compound] = None,
        name: str = None,
        color: Color = None,
        loc: Location = None,
    ):
        self.obj: Union["MAssembly", Compound] = obj
        self.name: str = name
        self.color: Color = color
        self.loc: Location = loc
        self.children = []
        self.parent = None
        self.mates = {}

    def _dump(self):
        def to_string(assy, matelist, ind="") -> str:
            result = f"\n{ind}{assy}\n"
            for name in matelist.get(assy.fq_name, []):
                result += f"{ind}  - {name:15s}: mate={self.mates[name].mate} origin={self.mates[name].mate.is_origin}\n"
            for c in assy.children:
                result += to_string(c, matelist, ind + "    ")
            return result

        matelist: Dict[str, List[str]] = {}
        for k, v in ((k, v.assembly.fq_name) for k, v in self.mates.items()):
            if matelist.get(v) is None:
                matelist[v] = [k]
            else:
                matelist[v].append(k)

        print(to_string(self, matelist, ""))

    def add(
        self,
        obj: Union["MAssembly", Compound],
        name: str = None,
        color: Color = Color(),
        loc: Location = Location(),
    ):
        if isinstance(obj, Compound):
            assembly = MAssembly(obj, name, color, loc)
            assembly.parent = self
            self.add(assembly)
        elif isinstance(obj, MAssembly):
            obj.parent = self
            self.children.append(obj)
        else:
            raise ValueError(f"Type {obj} not supported")

    def traverse(self):
        for ch in self.children:
            for el in ch.traverse():
                yield el
        yield (self.name, self)

    # for compatibility reasons apply the strange keys of cadquery
    @property
    def cq_name(self):
        return self.name if self.parent is None else self.fq_name[1:].partition("/")[2]

    @property
    def objects(self):
        return {assy.cq_name: assy for _, assy in self.traverse()}

    # proper key path across the assembly
    @property
    def fq_name(self):
        return (
            f"/{self.name}"
            if self.parent is None
            else f"{self.parent.fq_name}/{self.name}"
        )

    @property
    def objs(self):
        return {assy.fq_name: assy for _, assy in self.traverse()}

    @property
    def list(self):
        return [(assy.fq_name, assy) for _, assy in self.traverse()]

    def __repr__(self):
        hash = None if self.obj is None else self.obj.hash_code()
        parent = None if self.parent is None else self.parent.name
        object = (
            None if self.obj is None else f"{self.obj.__class__.__name__}(hash:{hash})"
        )
        return f"MAssembly(name={self.name}, parent={parent}, color={self.color}, loc={self.loc.__repr__()}, obj={object}"
