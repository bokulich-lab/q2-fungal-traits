# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from q2_types.feature_data import FeatureData
from qiime2.plugin import Citations, Plugin

from q2_fungal_traits import __version__
from q2_fungal_traits.types import FungalTraits, FungalTraitsDirFmt, FungalTraitsFormat

citations = Citations.load("citations.bib", package="q2_fungal_traits")

plugin = Plugin(
    name="fungal-traits",
    version=__version__,
    website="https://github.com/bokulich-lab/q2-fugal-traits",
    package="q2_fungal_traits",
    description="A QIIME 2 plugin to annotate fungal sequences with lifestyle traits.",
    short_description="Lifestyle traits annotation of fungal sequences.",
    citations=[citations["Caporaso-Bolyen-2024"]],
)

plugin.register_semantic_type_to_format(
    FeatureData[FungalTraits],
    artifact_format=FungalTraitsDirFmt,
)

plugin.register_formats(
    FungalTraitsFormat,
    FungalTraitsDirFmt,
)
