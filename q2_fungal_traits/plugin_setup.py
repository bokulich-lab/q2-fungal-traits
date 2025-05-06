# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from q2_types.feature_data import FeatureData, Taxonomy
from q2_types.metadata import ImmutableMetadata
from qiime2.plugin import Citations, Plugin

from q2_fungal_traits import __version__
from q2_fungal_traits.annotate import annotate

citations = Citations.load("citations.bib", package="q2_fungal_traits")

plugin = Plugin(
    name="fungal-traits",
    version=__version__,
    website="https://github.com/bokulich-lab/q2-fugal-traits",
    package="q2_fungal_traits",
    description=(
        "A QIIME 2 plugin to annotate fungal taxonomy data with lifestyle traits."
    ),
    short_description="Lifestyle traits annotation of fungal taxonomies.",
    citations=[citations["Caporaso-Bolyen-2024"]],
)

plugin.methods.register_function(
    function=annotate,
    inputs={"taxonomy": FeatureData[Taxonomy]},
    parameters={},
    outputs=[("fungal_traits_metadata", ImmutableMetadata)],
    input_descriptions={"taxonomy": "Fungal taxonomy."},
    parameter_descriptions={},
    output_descriptions={"fungal_traits_metadata": "Fungal traits metadata."},
    name="Fungal traits annotation.",
    description=(
        "Annotate fungal taxonomy data with lifestyle traits and spore volume data."
    ),
    citations=[citations["polme2020fungaltraits"], citations["abrego2024airborne"]],
)
