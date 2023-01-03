import contextvars

from jupyter_cadquery.animation import Animation

from build123d import Location
from .build_assembly import BuildAssembly


class Relocate:
    def __init__(self):
        """Relocate the assembly so that all its shapes have their origin at the assembly origin"""

        def _relocate(assembly, origins):
            origin_mate = origins.get(assembly.name)
            if origin_mate is not None:
                assembly.obj = (
                    None
                    if assembly.obj is None
                    else assembly.obj.moved(origin_mate.loc.inverse())
                )
                assembly.loc = Location()
            for c in assembly.children:
                _relocate(c, origins)

        context = BuildAssembly._get_context()

        origins = {
            mate_def.assembly.name: mate_def.mate
            for mate_def in context.assembly.mates.values()
            if mate_def.mate.is_origin
        }

        # relocate all objects
        _relocate(context.assembly, origins)

        # relocate all mates
        for mate_def in context.assembly.mates.values():
            origin_mate = origins.get(mate_def.assembly.name)
            if origin_mate is not None:
                mate_def.mate = mate_def.mate.moved(origin_mate.loc.inverse())


class BuildAnimation:
    # Context variable used to store Mates for the Part objects
    _current: contextvars.ContextVar["BuildAnimation"] = contextvars.ContextVar(
        "BuildAnimation._current"
    )

    @property
    def _obj(self):
        return self.animation

    @property
    def _obj_name(self):
        return "animation"

    def __enter__(self):
        """Upon entering record the parent and a token to restore contextvars"""

        self._parent = BuildAnimation._get_context()
        self._reset_tok = self._current.set(self)

        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Upon exiting restore context and send object to parent"""

        self._current.reset(self._reset_tok)

    def __init__(self, assembly):
        self.assembly = assembly
        self.animation = Animation()

    def _add_to_context(self, path, action, times, values):
        self.animation.add_track(path, action, times, values)

    @classmethod
    def _get_context(cls) -> "BuildAnimation":
        """Return the instance of the current builder"""
        return cls._current.get(None)


class Track:
    def __init__(self, path, action, times, values):
        context = BuildAnimation._get_context()

        if path not in context.assembly.paths:
            raise ValueError(f"Path {path} does not exist in assembly")
        context._add_to_context(path, action, times, values)


class Animate:
    def __init__(self, speed=1):
        context = BuildAnimation._get_context()
        context.animation.animate(speed=speed)
