# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import pandas as pd
from qiime2.core.exceptions import ValidationError
from qiime2.plugin import model


class FungalTraitsFormat(model.TextFileFormat):
    def _validate(self):
        header = [
            "jrk_template",
            "Phylum",
            "Class",
            "Order",
            "Family",
            "GENUS",
            "COMMENT on genus",
            "primary_lifestyle",
            "Secondary_lifestyle",
            "Comment_on_lifestyle_template",
            "Endophytic_interaction_capability_template",
            "Plant_pathogenic_capacity_template",
            "Decay_substrate_template",
            "Decay_type_template",
            "Aquatic_habitat_template",
            "Animal_biotrophic_capacity_template",
            "Specific_hosts",
            "Growth_form_template",
            "Fruitbody_type_template",
            "Hymenium_type_template",
            "Ectomycorrhiza_exploration_type_template",
            "Ectomycorrhiza_lineage_template",
            "primary_photobiont",
            "secondary_photobiont",
        ]
        header_obs = pd.read_csv(str(self), sep="\t", nrows=0).columns.tolist()
        if set(header) != set(header_obs):
            raise ValidationError(
                "Header line does not match FungalTraitsFormat. It must "
                "consist of the following values: "
                + ", ".join(header)
                + "\n\nFound instead: "
                + ", ".join(header_obs)
            )

    def _validate_(self, level):
        self._validate()


FungalTraitsDirFmt = model.SingleFileDirectoryFormat(
    "FungalTraitsDirFmt", "fungal_traits.tsv", FungalTraitsFormat
)
