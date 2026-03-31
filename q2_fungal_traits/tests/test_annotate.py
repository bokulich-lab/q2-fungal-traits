# ----------------------------------------------------------------------------
# Copyright (c) 2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
from importlib.resources import files

import numpy as np
import pandas as pd
import rachis
from q2_types.feature_data import TSVTaxonomyDirectoryFormat
from rachis.plugin.testing import TestPluginBase

from q2_fungal_traits.annotate import (
    add_fungal_traits,
    add_spore_volume,
    annotate,
    ensure_species_key_has_genus,
    load_spore_data,
    load_taxonomy,
    normalize_taxon_key,
)


class TestAnnotate(TestPluginBase):
    package = "q2_fungal_traits.tests"

    def test_load_taxonomy(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_add_spore_volume.tsv"))
        exp = pd.read_csv(self.get_data_path("load_taxonomy_exp.tsv"), sep="\t")
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_missing_ranks(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_missing_ranks.tsv"))
        exp = pd.read_csv(
            self.get_data_path("load_taxonomy_missing_ranks_exp.tsv"), sep="\t"
        )
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_whitespaces(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_whitespaces.tsv"))
        exp = pd.read_csv(
            self.get_data_path("load_taxonomy_whitespaces_exp.tsv"), sep="\t"
        )
        pd.testing.assert_frame_equal(obs, exp)

    def test_normalize_taxon_key(self):
        self.assertEqual(
            normalize_taxon_key("  Amanita_citrina-var  "), "amanita citrina var"
        )
        self.assertTrue(pd.isna(normalize_taxon_key("")))
        self.assertTrue(pd.isna(normalize_taxon_key("   ")))

    def test_ensure_species_key_has_genus(self):
        taxonomy = pd.read_csv(
            self.get_data_path("ensure_species_key_has_genus_input.tsv"),
            sep="\t",
        )
        obs = ensure_species_key_has_genus(taxonomy)
        exp = pd.read_csv(
            self.get_data_path("ensure_species_key_has_genus_exp.tsv"),
            sep="\t",
        )
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_normalizes_species_separators(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_normalize_species.tsv"))
        exp = pd.read_csv(
            self.get_data_path("load_taxonomy_normalize_species_exp.tsv"), sep="\t"
        )
        pd.testing.assert_frame_equal(obs, exp)

    def test_load_taxonomy_prepends_genus_to_species(self):
        obs = load_taxonomy(self.get_data_path("taxonomy_species_needs_genus.tsv"))
        exp = pd.read_csv(
            self.get_data_path("load_taxonomy_species_needs_genus_exp.tsv"), sep="\t"
        )
        pd.testing.assert_frame_equal(obs, exp)

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

    def test_add_spore_volume_requires_kingdom_match(self):
        taxonomy = pd.read_csv(
            self.get_data_path("add_spore_volume_requires_kingdom_match_taxonomy.tsv"),
            sep="\t",
        )
        spore_data = pd.read_csv(
            self.get_data_path("add_spore_volume_requires_kingdom_match_spore.tsv"),
            sep="\t",
        )
        obs = add_spore_volume(taxonomy, spore_data)
        exp = pd.read_csv(
            self.get_data_path("add_spore_volume_requires_kingdom_match_exp.tsv"),
            sep="\t",
        )
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_add_spore_volume_without_species_tax_key(self):
        taxonomy = pd.read_csv(
            self.get_data_path("add_spore_volume_without_species_tax_key_taxonomy.tsv"),
            sep="\t",
        )
        spore_data = pd.read_csv(
            self.get_data_path("add_spore_volume_without_species_tax_key_spore.tsv"),
            sep="\t",
        )
        obs = add_spore_volume(taxonomy, spore_data)
        exp = pd.read_csv(
            self.get_data_path("add_spore_volume_without_species_tax_key_exp.tsv"),
            sep="\t",
        )
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_add_spore_volume_without_family_tax_key(self):
        taxonomy = pd.read_csv(
            self.get_data_path("add_spore_volume_without_family_tax_key_taxonomy.tsv"),
            sep="\t",
        )
        spore_data = pd.read_csv(
            self.get_data_path("add_spore_volume_without_family_tax_key_spore.tsv"),
            sep="\t",
        )
        obs = add_spore_volume(taxonomy, spore_data)
        exp = pd.read_csv(
            self.get_data_path("add_spore_volume_without_family_tax_key_exp.tsv"),
            sep="\t",
        )
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))

    def test_add_spore_volume_manual_calculation(self):
        taxonomy = load_taxonomy(
            self.get_data_path("taxonomy_spore_volume_species_genus_family.tsv")
        )
        spore_data = load_spore_data(
            str(files("q2_fungal_traits.assets").joinpath("Spore_data_12Nov21.tsv"))
        )

        obs = add_spore_volume(taxonomy, spore_data)

        meiospores = spore_data[spore_data["SporeType"] == "Meiospores"]

        species_expected = meiospores.loc[
            meiospores["species_spd_key"].eq("datroniella minuta"), "SporeVolume"
        ].iloc[0]
        genus_expected = 10 ** np.mean(
            np.log10(
                meiospores.loc[
                    meiospores["genus_spd_key"].eq("datronia"), "SporeVolume"
                ]
            )
        )
        family_expected = 10 ** np.mean(
            np.log10(
                meiospores.loc[
                    meiospores["family_spd_key"].eq("polyporaceae"), "SporeVolume"
                ]
            )
        )

        species_row = obs.set_index("Feature ID").loc["species-hit"]
        self.assertEqual(species_row["meiospores_matching_level"], "species")
        self.assertEqual(species_row["meiospores_taxon"], "Datroniella_minuta")
        self.assertAlmostEqual(species_row["meiospores_volume"], species_expected)

        genus_row = obs.set_index("Feature ID").loc["genus-hit"]
        self.assertEqual(genus_row["meiospores_matching_level"], "genus")
        self.assertEqual(genus_row["meiospores_taxon"], "Datronia")
        self.assertAlmostEqual(genus_row["meiospores_volume"], genus_expected)

        family_row = obs.set_index("Feature ID").loc["family-hit"]
        self.assertEqual(family_row["meiospores_matching_level"], "family")
        self.assertEqual(family_row["meiospores_taxon"], "Polyporaceae")
        self.assertAlmostEqual(family_row["meiospores_volume"], family_expected)

    def test_annotate(self):
        obs = annotate(
            TSVTaxonomyDirectoryFormat(self.get_data_path("taxonomy_dir_fmt"), mode="r")
        )
        self.assertIsInstance(obs, rachis.Metadata)
        exp = pd.read_csv(self.get_data_path("metadata_out.tsv"), sep="\t", index_col=0)
        pd.testing.assert_frame_equal(obs.to_dataframe().astype(str), exp.astype(str))

    def test_annotate_value_error(self):
        with self.assertRaisesRegex(ValueError, "Annotation could not be performed"):
            annotate(
                TSVTaxonomyDirectoryFormat(
                    self.get_data_path("taxonomy_missing_ranks_dir"), mode="r"
                )
            )

    def test_add_fungal_traits_requires_phylum_match(self):
        taxonomy = pd.read_csv(
            self.get_data_path("add_fungal_traits_requires_phylum_match_taxonomy.tsv"),
            sep="\t",
        )
        fungal_traits = pd.read_csv(
            self.get_data_path("add_fungal_traits_requires_phylum_match_traits.tsv"),
            sep="\t",
        )
        obs = add_fungal_traits(taxonomy, fungal_traits)
        exp = pd.read_csv(
            self.get_data_path("add_fungal_traits_requires_phylum_match_exp.tsv"),
            sep="\t",
        )
        pd.testing.assert_frame_equal(obs.astype(str), exp.astype(str))
