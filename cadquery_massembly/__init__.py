import warnings

from .mate import Mate
from .massembly import MAssembly, DOF
from ._version import __version_info__, __version__


def relocate(assy):
    warnings.simplefilter("once", DeprecationWarning)
    warnings.warn(
        "relocate(assy) is deprecated. Use assy.relocate() instead",
        DeprecationWarning,
    )
    warnings.simplefilter("ignore", DeprecationWarning)

    assy.relocate()
