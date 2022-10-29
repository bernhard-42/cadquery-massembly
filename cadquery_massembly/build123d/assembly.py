from typing import Union, Dict, List, overload
from webcolors import name_to_rgb
from build123d.direct_api import Location, Compound


class Color:
    @overload
    def __init__(self):
        ...

    @overload
    def __init__(self, color: str, a=1):
        ...

    @overload
    def __init__(self, r: int, g: int, b: int, a: float = 1):
        ...

    def __init__(self, *args):
        if len(args) == 0:
            self.r = 0
            self.g = 0
            self.b = 0
            self.a = 1.0

        elif len(args) >= 1 and isinstance(args[0], str):
            rgb = name_to_rgb(args[0])
            self.r = rgb.red
            self.g = rgb.green
            self.b = rgb.blue
            if len(args) == 2:
                self.a = args[1]
            else:
                self.a = 1.0

        elif (
            len(args) >= 3
            and isinstance(args[0], int)
            and isinstance(args[1], int)
            and isinstance(args[2], int)
        ):
            self.r = args[0]
            self.g = args[1]
            self.b = args[2]
            if len(args) == 4 and args[3] < 1.0:
                self.a = args[3]
            else:
                self.a = 1.0

        else:
            raise ValueError(f"Cannot define color from {args}")

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
