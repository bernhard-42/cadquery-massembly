from .mate import Mate
from .massembly import MAssembly
from ._version import __version_info__, __version__


def relocate(assy):
    """Relocate the assembly so that all its shapes have their origin at the assembly origin"""

    from cadquery import Workplane, Location

    def _relocate(assy, origins):
        origin_mate = origins.get(assy.name)
        if origin_mate is not None:
            assy.obj = Workplane(assy.obj.val().moved(origin_mate.loc.inverse))
            assy.loc = Location()
        for c in assy.children:
            _relocate(c, origins)

    origins = {mate_def.assembly.name: mate_def.mate for mate_def in assy.mates.values() if mate_def.origin}

    # relocate all CadQuery objects
    _relocate(assy, origins)

    # relocate all mates
    for mate_def in assy.mates.values():
        origin_mate = origins.get(mate_def.assembly.name)
        if origin_mate is not None:
            mate_def.mate = mate_def.mate.moved(origin_mate.loc.inverse)
