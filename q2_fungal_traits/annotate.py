# ----------------------------------------------------------------------------
# Copyright (c) 2025, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import os
from importlib.resources import files

import numpy as np
import pandas as pd
import qiime2
from q2_types.feature_data import TSVTaxonomyDirectoryFormat


def load_taxonomy(taxonomy_path: str) -> pd.DataFrame:
    taxonomy = pd.read_csv(os.path.join(taxonomy_path, "taxonomy.tsv"), sep="\t")

    # Split the taxon string into separate columns
    taxonomy_split = taxonomy["Taxon"].str.split(";", expand=True)

    # Extract taxonomic prefixes from a fully annotated row
    for _, row in taxonomy_split.iterrows():
        if row.notna().all() and row.map(lambda x: isinstance(x, str)).all():
            prefixes = row.map(lambda x: x.split("__")[0])
            break

    # Name the columns with the appropriate taxonomic levels
    taxonomy_split.columns = prefixes
    taxonomy_split = taxonomy_split.rename(
        columns={"s": "species", "g": "genus", "f": "family"}
    )

    # Remove the prefixes from the taxon strings
    taxonomy_split = taxonomy_split.applymap(
        lambda x: x.split("__")[-1] if isinstance(x, str) else x
    )
    cols_to_add = [
        col for col in ["family", "genus", "species"] if col in taxonomy_split.columns
    ]

    if not cols_to_add:
        raise ValueError(
            'None of the taxonomy levels "family", "genus", or "species" are present. '
            "Please check your taxonomy file."
        )

    return taxonomy[["Feature ID"]].join(taxonomy_split[cols_to_add])


def load_spore_data() -> pd.DataFrame:
    spore_data = pd.read_csv(
        str(files("q2_fungal_traits.assets").joinpath("Spore_data_12Nov21.tsv")),
        sep="\t",
    )
    spore_data["names_to_use"] = spore_data["names_to_use"].str.replace(
        " ", "_", regex=False
    )
    spore_data["SporeType"] = spore_data["SporeType"].str.replace(" ", "_", regex=False)
    spore_data = spore_data[spore_data["SporeVolume"] > 0].copy()
    spore_data["log10_spore_volume"] = np.log10(spore_data["SporeVolume"])
    return spore_data


def add_spore_volume(taxonomy: pd.DataFrame, spore_data: pd.DataFrame) -> pd.DataFrame:
    for spore_type in [
        "Mitospores",
        "Meiospores",
        "Multinucleate_sexual_spores",
        "Multinucleate_asexual_spores",
    ]:
        volume_col = f"{spore_type.lower()}_spore_volume"
        info_col = f"{spore_type.lower()}_spore_volume_information"

        taxonomy[volume_col] = np.nan
        taxonomy[info_col] = "no hit"

        spore_type_filtered = spore_data[spore_data["SporeType"] == spore_type]

        # Species-level exact match
        if "species" in taxonomy.columns:
            species_map = spore_type_filtered.set_index("names_to_use")["SporeVolume"]
            species_hits = taxonomy["species"].map(species_map)
            mask = species_hits.notna()
            taxonomy.loc[mask, volume_col] = species_hits[mask]
            taxonomy.loc[mask, info_col] = "species"

        for rank in ["genus", "family"]:
            # Genus-level fallback
            if rank in taxonomy.columns:
                missing = taxonomy[volume_col].isna()
                missing_genera = taxonomy.loc[missing, rank].dropna().unique()
                rank_means = spore_type_filtered[
                    spore_type_filtered[rank].isin(missing_genera)
                ]
                rank_means = (
                    rank_means.groupby(rank)["log10_spore_volume"]
                    .mean()
                    .apply(lambda x: 10**x)
                )
                rank_hits = taxonomy.loc[missing, rank].map(rank_means)
                mask = rank_hits.notna()
                taxonomy.loc[missing[missing].index[mask], volume_col] = rank_hits[mask]
                taxonomy.loc[missing[missing].index[mask], info_col] = rank

    return taxonomy.drop(columns=["family", "species"], errors="ignore")


def add_fungal_traits(taxonomy, fungal_traits):
    result = pd.merge(
        taxonomy, fungal_traits, left_on="genus", right_on="GENUS", how="left"
    )
    return result.drop(
        columns=[
            "GENUS",
            "COMMENT on genus",
            "jrk_template",
            "Phylum",
            "Class",
            "Order",
            "Family",
        ]
    )


def annotate(taxonomy: TSVTaxonomyDirectoryFormat) -> qiime2.Metadata:
    taxonomy = load_taxonomy(str(taxonomy))
    spore_data = load_spore_data()
    fungal_traits = pd.read_csv(
        str(
            files("q2_fungal_traits.assets").joinpath(
                "FungalTraits_1.2_ver_16Dec_2020_V.1.2.tsv"
            )
        ),
        sep="\t",
    )

    annotations_spores = add_spore_volume(taxonomy, spore_data)
    annotations_spores_traits = add_fungal_traits(annotations_spores, fungal_traits)

    annotations_spores_traits.rename(columns={"Feature ID": "feature-id"}, inplace=True)
    annotations_spores_traits.set_index("feature-id", inplace=True)

    return qiime2.Metadata(annotations_spores_traits)
