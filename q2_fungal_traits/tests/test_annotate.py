# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from importlib.resources import files
from unittest.mock import patch

import pandas as pd
import qiime2
from q2_types.feature_data import TSVTaxonomyDirectoryFormat
from qiime2.plugin.testing import TestPluginBase

from q2_fungal_traits.annotate import (
    add_fungal_traits,
    add_spore_volume,
    annotate,
    load_spore_data,
    load_taxonomy,
)


class TestAnnotate(TestPluginBase):
    package = "q2_fungal_traits.tests"

    def setUp(self):
        super().setUp()
        self.taxonomy_data = {
            "feature-id": ["abc123"],
            "family": ["Saccharomycetales_fam_Incertae_sedis"],
            "genus": ["Candida"],
            "species": ["Candida_sp"],
        }
        self.loaded_taxonomy = pd.DataFrame(self.taxonomy_data).set_index("feature-id")

    def test_load_taxonomy(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_add_spore_volume.tsv"))
        exp = pd.read_csv(self.get_data_path("load_taxonomy_exp.tsv"), sep="\t")
        exp = exp.set_index("feature-id")
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_value_error(self):
        with self.assertRaisesRegex(ValueError, "None of the taxonomy levels"):
            load_taxonomy(self.get_data_path("taxonomy_missing_ranks.tsv"))

    def test_load_spore_data(self):
        obs = load_spore_data(self.get_data_path("Spore_data_12Nov21_test.tsv"))
        exp = pd.read_csv(self.get_data_path("load_spore_data_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs, exp)

    def test_add_fungal_traits(self):
        fungal_traits = pd.read_csv(
            str(
                files("q2_fungal_traits.assets").joinpath(
                    "FungalTraits_1.2_ver_16Dec_2020_V.1.2.tsv"
                )
            ),
            sep="\t",
        )
        obs = add_fungal_traits(self.loaded_taxonomy, fungal_traits)
        exp = pd.read_csv(self.get_data_path("add_fungal_traits_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_add_spore_volume(self):
        taxonomy_df = load_taxonomy(self.get_data_path("taxonomy_add_spore_volume.tsv"))
        spore_data = load_spore_data(
            str(files("q2_fungal_traits.assets").joinpath("Spore_data_12Nov21.tsv"))
        )
        obs = add_spore_volume(taxonomy_df, spore_data)
        exp = pd.read_csv(self.get_data_path("add_spore_volume_exp.tsv"), sep="\t")
        exp = exp.set_index("feature-id")
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    @patch("q2_fungal_traits.annotate.add_fungal_traits")
    @patch("q2_fungal_traits.annotate.add_spore_volume")
    @patch("q2_fungal_traits.annotate.load_spore_data")
    @patch("q2_fungal_traits.annotate.load_taxonomy")
    def test_annotate(
        self,
        mock_load_taxonomy,
        mock_load_spore_data,
        mock_add_spore_volume,
        mock_add_fungal_traits,
    ):
        df = pd.DataFrame({"genus": ["Datroniella"]}, index=["1"])
        df.index.name = "feature-id"
        df.index = df.index.astype(str)
        df.index = df.index.astype(str)

        mock_add_fungal_traits.return_value = df

        obs = annotate(
            TSVTaxonomyDirectoryFormat(self.get_data_path("taxonomy.tsv"), mode="r")
        )
        self.assertIsInstance(obs, qiime2.Metadata)
