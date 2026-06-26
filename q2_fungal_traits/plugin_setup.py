# ----------------------------------------------------------------------------
# Copyright (c) 2026, Bokulich Laboratories.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from q2_types.feature_data import FeatureData, Taxonomy
from q2_types.metadata import ImmutableMetadata
from rachis.plugin import Citations, Plugin

from q2_fungal_traits import __version__
from q2_fungal_traits.annotate import annotate

citations = Citations.load("citations.bib", package="q2_fungal_traits")

plugin = Plugin(
    name="fungal-traits",
    version=__version__,
    website="https://github.com/bokulich-lab/q2-fugal-traits",
    package="q2_fungal_traits",
    description=(
        "A QIIME 2 plugin that annotates taxonomy tables with fungal lifestyle "
        "traits and spore volume information."
    ),
    short_description="Lifestyle traits annotation of fungal taxonomies.",
    citations=[citations['Lavrinienko2026']],
)

plugin.methods.register_function(
    function=annotate,
    inputs={"taxonomy": FeatureData[Taxonomy]},
    parameters={},
    outputs=[("fungal_traits", ImmutableMetadata)],
    input_descriptions={"taxonomy": "Fungal taxonomy."},
    parameter_descriptions={},
    output_descriptions={"fungal_traits": "Fungal traits metadata."},
    name="Fungal traits annotation.",
    description=(
        "Annotate taxonomy data with fungal lifestyle traits and spore volume "
        "metadata. Fungal trait annotation is performed when both genus and phylum "
        "are present, because the trait table is matched by genus and then filtered "
        "so only rows with the same phylum are retained. Spore volume annotation is "
        "performed when kingdom is present together with at least one of species, "
        "genus, or family. Spore matching is done in a simple fallback order: first "
        "try an exact species match, if that is not available try genus, and if that "
        "is still not available try family. Species matches use the direct spore "
        "volume from the source table. Genus and family matches summarize the "
        "available values for that rank with a geometric mean and record which rank "
        "was used, so it is clear whether a value came from a species, genus, or "
        "family-level match."
    ),
    citations=[
        citations["polme2020fungaltraits"],
        citations["abrego2024airborne"],
        citations["aguilar2023symbiotic"],
    ],
)
