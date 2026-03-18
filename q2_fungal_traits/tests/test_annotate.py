# ----------------------------------------------------------------------------
# Copyright (c) 2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from importlib.resources import files
from unittest.mock import patch

import pandas as pd
import rachis
from q2_types.feature_data import TSVTaxonomyDirectoryFormat
from rachis.plugin.testing import TestPluginBase

from q2_fungal_traits.annotate import (
    add_fungal_traits,
    add_spore_volume,
    annotate,
    handle_duplicates,
    load_spore_data,
    load_taxonomy,
)


class TestAnnotate(TestPluginBase):
    package = "q2_fungal_traits.tests"

    def test_load_taxonomy(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_add_spore_volume.tsv"))
        exp = pd.read_csv(self.get_data_path("load_taxonomy_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_value_error(self):
        with self.assertRaisesRegex(ValueError, "None of the taxonomy levels"):
            load_taxonomy(self.get_data_path("taxonomy_missing_ranks.tsv"))

    def test_load_taxonomy_normalizes_species_separators(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_normalize_species.tsv"))
        self.assertEqual(obs.loc[0, "species"], "Amanita muscaria var")

    def test_load_taxonomy_prepends_genus_to_species(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_species_needs_genus.tsv"))
        self.assertEqual(obs.loc[0, "species"], "Amanita muscaria")

    def test_load_spore_data(self):
        obs = load_spore_data(self.get_data_path("Spore_data_12Nov21_test.tsv"))
        exp = pd.read_csv(self.get_data_path("load_spore_data_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs, exp)

    @patch("q2_fungal_traits.annotate.handle_duplicates")
    def test_add_fungal_traits(self, mock_drop_duplicates):
        mock_drop_duplicates.side_effect = lambda x: x
        fungal_traits = pd.read_csv(
            str(
                files("q2_fungal_traits.assets").joinpath(
                    "FungalTraits_1.2_ver_16Dec_2020_V.1.2.tsv"
                )
            ),
            sep="\t",
        )
        taxonomy = pd.read_csv(self.get_data_path("load_taxonomy_exp.tsv"), sep="\t")
        obs = add_fungal_traits(taxonomy, fungal_traits)
        exp = pd.read_csv(self.get_data_path("add_fungal_traits_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_add_spore_volume(self):
        taxonomy_df = load_taxonomy(self.get_data_path("taxonomy_add_spore_volume.tsv"))
        spore_data = load_spore_data(
            str(files("q2_fungal_traits.assets").joinpath("Spore_data_12Nov21.tsv"))
        )
        obs = add_spore_volume(taxonomy_df, spore_data)
        exp = pd.read_csv(self.get_data_path("add_spore_volume_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_annotate(self):
        obs = annotate(
            TSVTaxonomyDirectoryFormat(self.get_data_path("taxonomy_dir_fmt"), mode="r")
        )
        self.assertIsInstance(obs, rachis.Metadata)
        exp = pd.read_csv(self.get_data_path("metadata_out.tsv"), sep="\t", index_col=0)
        pd.testing.assert_frame_equal(obs.to_dataframe().astype(str), exp.astype(str))

    def test_drop_duplicates(self):
        df = pd.read_csv(self.get_data_path("drop_duplicates_input.tsv"), sep="\t")
        obs = handle_duplicates(df)
        obs.reset_index(drop=True, inplace=True)
        exp = pd.read_csv(self.get_data_path("drop_duplicates_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))
