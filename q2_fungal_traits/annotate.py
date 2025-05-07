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
    taxonomy = pd.read_csv(taxonomy_path, sep="\t")

    # Split the taxon string into separate columns
    taxonomy_split = taxonomy["Taxon"].str.split(";", expand=True)

    # Extract taxonomic prefixes from a fully annotated row
    prefixes = taxonomy_split.dropna().iloc[0].map(lambda x: x.split("__")[0])

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

    taxonomy = taxonomy[["Feature ID"]].join(taxonomy_split[cols_to_add])

    return taxonomy


def load_spore_data(spore_data_path) -> pd.DataFrame:
    spore_data = pd.read_csv(spore_data_path, sep="\t")

    for col in ["names_to_use", "SporeType"]:
        spore_data[col] = spore_data[col].str.replace(" ", "_", regex=False)

    return spore_data


def add_spore_volume(taxonomy: pd.DataFrame, spore_data: pd.DataFrame) -> pd.DataFrame:
    """
    Annotate a taxonomy DataFrame with spore volume data.

    The annotation follows a hierarchical matching strategy:
    1. Species-level: Direct string match using the species columns.
    2. Genus-level: For unmatched entries, log-mean spore volume is computed per genus,
       and mapped to matching genera.
    3. Family-level: If genus-level data is still missing, the process is repeated
       at the family level.

    If no match is found, the volume remains `NaN` and the information column is set
    to `"no hit"`.

    Parameters:
        taxonomy (pd.DataFrame): The input DataFrame containing at least 'genus' and/or
                                 'family',and optionally a 'species' column.
        spore_data (pd.DataFrame): A DataFrame containing the spore volume data.

    Returns:
        pd.DataFrame: The input `taxonomy` DataFrame with added spore volume columns
                      for each spore type and information columns denoting what level
                      the spore data is derived from.
    """

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

        # Genus or family level fallback
        for rank in ["genus", "family"]:
            if rank in taxonomy.columns:
                missing = taxonomy[volume_col].isna()
                missing_genera = taxonomy.loc[missing, rank].dropna().unique()
                rank_means = spore_type_filtered[
                    spore_type_filtered[rank].isin(missing_genera)
                ]
                rank_means = rank_means.groupby(rank)["SporeVolume"].apply(
                    lambda x: 10 ** np.mean(np.log10(x))
                )
                rank_hits = taxonomy.loc[missing, rank].map(rank_means)
                mask = rank_hits.notna()
                taxonomy.loc[missing[missing].index[mask], volume_col] = rank_hits[mask]
                taxonomy.loc[missing[missing].index[mask], info_col] = rank

    return taxonomy


def drop_duplicates(df):
    """
    Handles duplicated IDs in the merged taxonomy with fungal traits.

    This function first removes exact duplicate rows. Then it removes duplicated rows
    due to inconsistent family assignments of the genera 'Caudospora' and
    'Campanulospora' by keeping the most appropriate row based on the assigned family.

    Parameters:
        df (pd.DataFrame): A pandas DataFrame of taxonomy merged with fungal trait data.

    Returns:
        pd.DataFrame: The cleaned DataFrame with appropriate duplicates removed.
    """
    df = df.drop_duplicates()

    dup_ids = df[df["Feature ID"].duplicated(keep=False)]

    for feature_id, group in dup_ids.groupby("Feature ID"):
        genus = group["GENUS"].iloc[0]
        if genus in ["Caudospora", "Campanulospora"]:
            row_micro = group.query(
                "Family == 'Microsporidea family incertae sedis'"
            ).squeeze()
            row_other = group.query(
                "Family != 'Microsporidea family incertae sedis'"
            ).squeeze()

            if row_other["Family"] == row_other["family"]:
                df = df.drop(index=row_micro.name)
            else:
                df = df.drop(index=row_other.name)

    return df


def add_fungal_traits(taxonomy, fungal_traits):
    merged = pd.merge(
        taxonomy, fungal_traits, left_on="genus", right_on="GENUS", how="left"
    )
    unique_merged = drop_duplicates(merged)

    return unique_merged.drop(
        columns=[
            "GENUS",
            "COMMENT on genus",
            "jrk_template",
            "Phylum",
            "Class",
            "Order",
            "Family",
            "family",
            "species",
        ],
        errors="ignore",
    )


def annotate(taxonomy: TSVTaxonomyDirectoryFormat) -> qiime2.Metadata:
    taxonomy = load_taxonomy(os.path.join(taxonomy.path, "taxonomy.tsv"))
    spore_data = load_spore_data(
        str(files("q2_fungal_traits.assets").joinpath("Spore_data_12Nov21.tsv"))
    )
    fungal_traits = pd.read_csv(
        str(
            files("q2_fungal_traits.assets").joinpath(
                "FungalTraits_1.2_ver_16Dec_2020_V.1.2.tsv"
            )
        ),
        sep="\t",
    )

    # Add spore volume data and fungal traits
    annotations_spores = add_spore_volume(taxonomy, spore_data)
    annotations_spores_traits = add_fungal_traits(annotations_spores, fungal_traits)

    # To adhere to the qiime metadata format
    annotations_spores_traits.rename(columns={"Feature ID": "feature-id"}, inplace=True)
    annotations_spores_traits.set_index("feature-id", inplace=True)

    return qiime2.Metadata(annotations_spores_traits)
