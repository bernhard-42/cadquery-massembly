import contextvars
from dataclasses import dataclass
from typing import Union, List

from build123d import (
    Location,
    BuildPart,
    Face,
    Wire,
    Edge,
)

from .assembly import MAssembly, Color
from .mate import Mate

# %%


@dataclass
class MateDef:
    mate: Mate
    assembly: MAssembly

    @property
    def world_mate(self):
        mate = self.mate
        assembly = self.assembly

        while assembly is not None:
            mate = mate.moved(assembly.loc)
            assembly = assembly.parent

        return mate


class BuildAssembly:
    # Context variable used by Parts to link to current builder instance
    _current: contextvars.ContextVar["BuildAssembly"] = contextvars.ContextVar(
        "BuildAssembly._current"
    )

    @property
    def _obj(self):
        return self.assembly

    @property
    def _obj_name(self):
        return "assembly"

    def __enter__(self):
        """Upon entering record the parent and a token to restore contextvars"""

        self._parent = BuildAssembly._get_context()
        self._reset_tok = self._current.set(self)

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Upon exiting restore context and send object to parent"""

        self._current.reset(self._reset_tok)

        if self._parent is not None:
            self._parent._add_to_context(self._obj)

    def __init__(
        self,
        name: str,
        loc: Location = Location(),
    ):
        self.assembly = MAssembly(name=name, loc=loc)
        self.assembly.mates = {}

    def _add_to_context(self, obj: MAssembly):
        self.assembly.add(obj)
        for name, mate_def in obj.mates.items():
            if self.assembly.mates.get(name) is not None:
                raise ValueError("Unique mate names required:", name)

            self.assembly.mates[name] = mate_def

    @classmethod
    def _get_context(cls) -> "BuildAssembly":
        """Return the instance of the current builder"""
        return cls._current.get(None)


class Mates:
    # Context variable used to store Mates for the Part objects
    _current: contextvars.ContextVar["Mates"] = contextvars.ContextVar("Mates._current")

    @property
    def _obj(self):
        return self.mates

    @property
    def _obj_name(self):
        return "mates"

    def __enter__(self):
        """Upon entering record the parent and a token to restore contextvars"""

        self._parent = Mates._get_context()
        self._reset_tok = self._current.set(self)

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Upon exiting restore context and send object to parent"""

        self._current.reset(self._reset_tok)

    def __init__(self, *objs: Mate):
        self.mates = objs

    @classmethod
    def _get_context(cls) -> "Mates":
        """Return the instance of the current builder"""
        return cls._current.get(None)


class Part:
    def __init__(
        self,
        object: BuildPart,
        name: str = None,
        color: Color = None,
        loc: Location = Location(),
    ):
        self.object = object

        context = BuildAssembly._get_context()
        assembly = MAssembly(object.part, name=name, color=color, loc=loc)

        m_context = Mates._get_context()
        if m_context is not None:
            for mate in m_context.mates:
                assembly.mates[mate.name] = MateDef(mate, assembly)

        context._add_to_context(assembly)


class Assemble:
    def __init__(self, mate: str, target: Union[str, Location]):
        """
        Translate and rotate a mate onto a target mate
        :param mate: name of the mate to be assembled
        :param target: name of the target mate or a Location object to assemble the mate to
        """
        context = BuildAssembly._get_context()

        o_mate = context.assembly.mates[mate].mate
        o_assy = context.assembly.mates[mate].assembly

        if isinstance(target, str):
            t_mate = context.assembly.mates[target].mate
            t_assy = context.assembly.mates[target].assembly

            if o_assy.parent == t_assy.parent or o_assy.parent is None:
                o_assy.loc = t_assy.loc
            else:
                o_assy.loc = t_assy.loc * o_assy.parent.loc.inverse
            o_assy.loc = o_assy.loc * t_mate.loc * o_mate.loc.inverse
        else:
            o_assy.loc = target
