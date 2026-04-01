# ----------------------------------------------------------------------------
# Copyright (c) 2026, QIIME 2 development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------
import os
from importlib.resources import files

import numpy as np
import pandas as pd
import rachis
from q2_types.feature_data import TSVTaxonomyDirectoryFormat


def normalize_taxon_key(value):
    """Normalize taxon strings for case-insensitive matching across datasets."""
    if not isinstance(value, str):
        return value

    value = value.replace("[", "").replace("]", "")
    value = value.replace("-", " ").replace("_", " ")
    value = " ".join(value.split())

    if value == "":
        return np.nan

    return value.casefold()


def ensure_species_key_has_genus(taxonomy: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure normalized species keys include the normalized genus prefix.

    For rows where both ``genus_tax_key`` and ``species_tax_key`` are present,
    this function checks whether the normalized species key already starts with
    the normalized genus key. If not, the genus key is prepended so downstream
    species-level matching uses a consistent ``genus species`` form.

    Parameters:
        taxonomy (pd.DataFrame): Taxonomy DataFrame that may contain
            ``genus_tax_key`` and ``species_tax_key``.

    Returns:
        pd.DataFrame: ``taxonomy`` with ``species_tax_key`` updated where
        the genus prefix was missing.
    """
    if {"genus_tax_key", "species_tax_key"}.issubset(taxonomy.columns):
        genus_key = taxonomy["genus_tax_key"]
        species_key = taxonomy["species_tax_key"]
        species_has_genus = (
            species_key.fillna("").str.split().str[0].eq(genus_key.fillna(""))
        )
        needs_genus_prefix = (
            genus_key.notna() & species_key.notna() & ~species_has_genus
        )
        taxonomy.loc[needs_genus_prefix, "species_tax_key"] = (
            genus_key[needs_genus_prefix] + " " + species_key[needs_genus_prefix]
        )

    return taxonomy


def load_taxonomy(taxonomy_path: str) -> pd.DataFrame:
    """
    Load and parse a taxonomy file with taxon annotations.

    Extract taxonomic ranks from the semicolon-separated ``Taxon`` column and add
    normalized taxonomy columns and keys to the DataFrame.

    The extracted columns use the ``rank_tax`` naming scheme, for example
    ``kingdom_tax``, ``phylum_tax``, ``genus_tax``, and ``species_tax``. For each
    extracted column, a normalized ``*_key`` companion column is also created for
    downstream matching.

    Parameters:
        taxonomy_path (str): Path to the taxonomy TSV file.

    Returns:
        pd.DataFrame: DataFrame with the original columns plus extracted
        ``*_tax`` columns and normalized ``*_tax_key`` columns for each extracted
        rank.
    """

    taxonomy = pd.read_csv(taxonomy_path, sep="\t")

    # Split the taxon string into separate columns
    taxonomy_split = taxonomy["Taxon"].str.split(";", expand=True)

    # Strip whitespaces
    taxonomy_split = taxonomy_split.apply(lambda col: col.str.strip())

    # Extract taxonomic prefixes from a fully annotated row
    prefixes = taxonomy_split.dropna().iloc[0].map(lambda x: x.split("__")[0])

    # Name the columns with the appropriate taxonomic levels
    taxonomy_split.columns = prefixes
    taxonomy_split = taxonomy_split.rename(
        columns={
            "s": "species_tax",
            "g": "genus_tax",
            "f": "family_tax",
            "p": "phylum_tax",
            "k": "kingdom_tax",
        }
    )

    # Remove the prefixes from the taxon strings and convert explicit empty
    # ranks such as ``f__`` to missing values.
    taxonomy_split = taxonomy_split.apply(
        lambda col: col.map(lambda x: x.split("__")[-1] if isinstance(x, str) else x)
    )
    taxonomy_split = taxonomy_split.mask(taxonomy_split.eq(""), np.nan)

    rank_cols = ["kingdom_tax", "phylum_tax", "family_tax", "genus_tax", "species_tax"]
    cols_to_add = [
        col
        for col in rank_cols
        if col in taxonomy_split.columns and taxonomy_split[col].notna().any()
    ]

    taxonomy = taxonomy.join(taxonomy_split[cols_to_add])

    for col in cols_to_add:
        taxonomy[f"{col}_key"] = taxonomy[col].map(normalize_taxon_key)

    taxonomy = ensure_species_key_has_genus(taxonomy)

    return taxonomy


def load_spore_data(spore_data_path) -> pd.DataFrame:
    """
    Load and preprocess spore volume data for annotation.

    The spore data columns used for matching are renamed to the ``rank_spd``
    scheme so their origin remains explicit after merges:
    ``phylum_spd``, ``family_spd``, ``genus_spd``, and ``species_spd``.
    Normalized key columns are added as ``species_spd_key``, ``genus_spd_key``,
    and ``family_spd_key``.

    ``SporeType`` values are normalized by replacing spaces with underscores.

    Parameters:
        spore_data_path (str): Path to the spore volume TSV file.

    Returns:
        pd.DataFrame: Preprocessed spore data with renamed rank columns and
        normalized key columns for matching.
    """
    spore_data = pd.read_csv(spore_data_path, sep="\t").rename(
        columns={
            "phylum": "phylum_spd",
            "family": "family_spd",
            "genus": "genus_spd",
            "names_to_use": "species_spd",
        }
    )

    spore_data["SporeType"] = spore_data["SporeType"].str.replace(" ", "_", regex=False)

    for col, key_col in [
        ("species_spd", "species_spd_key"),
        ("genus_spd", "genus_spd_key"),
        ("family_spd", "family_spd_key"),
    ]:
        if col in spore_data.columns:
            spore_data[key_col] = spore_data[col].map(normalize_taxon_key)

    return spore_data


def add_spore_volume(taxonomy: pd.DataFrame, spore_data: pd.DataFrame) -> pd.DataFrame:
    """
    Annotate a taxonomy DataFrame with spore volume data.

    The annotation follows a hierarchical matching strategy:
    1. Species-level: Exact matching between ``species_tax_key`` and
       ``species_spd_key``.
    2. Genus-level: For unmatched fungal rows, compute the log-mean spore volume per
       ``genus_spd_key`` and map it back to ``genus_tax_key``.
    3. Family-level: If genus-level data is still missing, repeat the same process
       with ``family_spd_key`` and ``family_tax_key``.

    A spore match is only allowed for rows where ``kingdom_tax_key == "fungi"``.

    Parameters:
        taxonomy (pd.DataFrame): Taxonomy DataFrame containing the ``*_tax`` and
            ``*_tax_key`` columns needed for matching.
        spore_data (pd.DataFrame): Spore volume DataFrame containing the
            ``*_spd`` and ``*_spd_key`` columns used for matching.

    Returns:
        pd.DataFrame: The input ``taxonomy`` DataFrame with added spore volume,
        matched taxon, and matching-level columns for each spore type.
    """

    for spore_type in [
        "Mitospores",
        "Meiospores",
        "Multinucleate_sexual_spores",
        "Multinucleate_asexual_spores",
    ]:
        taxon_col = f"{spore_type.lower()}_taxon"
        volume_col = f"{spore_type.lower()}_volume"
        info_col = f"{spore_type.lower()}_matching_level"

        taxonomy[taxon_col] = pd.Series(np.nan, index=taxonomy.index, dtype="object")
        taxonomy[volume_col] = pd.Series(np.nan, index=taxonomy.index, dtype="float64")
        taxonomy[info_col] = pd.Series(np.nan, index=taxonomy.index, dtype="object")

        spore_type_filtered = spore_data[spore_data["SporeType"] == spore_type]
        fungal_taxonomy_mask = taxonomy["kingdom_tax_key"].eq("fungi")

        # Species-level exact match
        if "species_tax_key" in taxonomy.columns:
            species_map = spore_type_filtered.set_index("species_spd_key")[
                "SporeVolume"
            ]
            species_matches = taxonomy["species_tax_key"].map(species_map)
            mask = species_matches.notna() & fungal_taxonomy_mask
            taxonomy.loc[mask, volume_col] = species_matches[mask]
            taxonomy.loc[mask, info_col] = "species"
            taxonomy.loc[mask, taxon_col] = taxonomy.loc[mask, "species_tax"]

        # Genus or family level fallback
        for rank in ["genus", "family"]:
            rank_tax = f"{rank}_tax"
            rank_tax_key = f"{rank}_tax_key"
            rank_spd_key = f"{rank}_spd_key"
            if rank_tax in taxonomy.columns and rank_tax_key in taxonomy.columns:
                # Identify rows where volume is still missing
                missing = taxonomy[volume_col].isna() & fungal_taxonomy_mask
                # Get unique ranks (genus or family) for missing entries
                ranks_to_check = taxonomy.loc[missing, rank_tax_key].dropna().unique()

                # Compute log-mean spore volume for each rank present in spore data
                rank_means = (
                    spore_type_filtered[
                        spore_type_filtered[rank_spd_key].isin(ranks_to_check)
                    ]
                    .groupby(rank_spd_key)["SporeVolume"]
                    .apply(lambda x: 10 ** np.mean(np.log10(x)))
                )

                # Map the computed means back to the taxonomy for missing entries
                rank_matches = taxonomy.loc[missing, rank_tax_key].map(rank_means)
                # Find where matches were successful
                matched = rank_matches.notna()

                # Update the taxonomy with matched volumes and info
                idx = rank_matches[matched].index
                taxonomy.loc[idx, volume_col] = rank_matches[matched]
                taxonomy.loc[idx, info_col] = rank
                taxonomy.loc[idx, taxon_col] = taxonomy.loc[idx, rank_tax]

    return taxonomy


def add_fungal_traits(taxonomy, fungal_traits):
    """
    Merge fungal trait annotations into the taxonomy table.

    The fungal traits table is renamed to use explicit source-aware column names,
    including ``phylum_ft`` and ``genus_ft`` with corresponding normalized key
    columns. Traits are merged to taxonomy on genus using
    ``genus_tax_key`` and ``genus_ft_key``. After merging, rows are retained only
    when the phylum keys also agree.

    Parameters:
        taxonomy (pd.DataFrame): Taxonomy DataFrame containing taxonomy-derived
            columns such as ``genus_tax_key`` and ``phylum_tax_key``.
        fungal_traits (pd.DataFrame): Raw fungal traits DataFrame.

    Returns:
        pd.DataFrame: Merged taxonomy and fungal traits table with phylum-mismatched
        rows removed and exact duplicate rows dropped.
    """
    fungal_traits = fungal_traits.rename(
        columns={
            "Phylum": "phylum_ft",
            "GENUS": "genus_ft",
        }
    )
    fungal_traits["genus_ft_key"] = fungal_traits["genus_ft"].map(normalize_taxon_key)
    fungal_traits["phylum_ft_key"] = fungal_traits["phylum_ft"].map(normalize_taxon_key)

    merged = pd.merge(
        taxonomy,
        fungal_traits,
        left_on=["genus_tax_key", "phylum_tax_key"],
        right_on=["genus_ft_key", "phylum_ft_key"],
        how="left",
    )

    return merged


def annotate(taxonomy: TSVTaxonomyDirectoryFormat) -> rachis.Metadata:
    """
    Annotate a QIIME 2 taxonomy artifact with fungal traits and spore volumes.

    The workflow loads taxonomy, fungal trait, and spore datasets; conditionally
    performs fungal trait merging and spore volume matching based on the
    available taxonomy ranks; drops intermediate matching columns; and returns
    the result as ``rachis.Metadata``.

    Parameters:
        taxonomy (TSVTaxonomyDirectoryFormat): QIIME 2 taxonomy directory format
            containing ``taxonomy.tsv``.

    Returns:
        rachis.Metadata: Annotated metadata table ready for downstream use.

    Raises:
        ValueError: If the taxonomy does not contain enough rank information to
        run either fungal trait annotation or spore volume annotation.
    """
    # Load taxonomy, spore data, and fungal traits
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
    can_add_fungal_traits = {"genus_tax", "phylum_tax"}.issubset(taxonomy.columns)
    can_add_spore_volume = "kingdom_tax" in taxonomy.columns and any(
        col in taxonomy.columns for col in ["species_tax", "genus_tax", "family_tax"]
    )

    if can_add_fungal_traits:
        taxonomy = add_fungal_traits(taxonomy, fungal_traits)

    if can_add_spore_volume:
        taxonomy = add_spore_volume(taxonomy, spore_data)

    if not can_add_fungal_traits and not can_add_spore_volume:
        raise ValueError(
            "Annotation could not be performed. Fungal traits annotations require both "
            "'genus' and 'phylum' ranks in the taxonomy. Spore volume annotation "
            "requires 'kingdom' and at least one of 'species', 'genus', or 'family' "
            "ranks."
        )

    # Drop columns that are not needed for the final output
    taxonomy.drop(
        columns=[
            "genus_tax",
            "COMMENT on genus",
            "jrk_template",
            "phylum_ft",
            "Family",
            "Class",
            "Order",
            "phylum_tax",
            "phylum_tax_key",
            "kingdom_tax",
            "kingdom_tax_key",
            "species_tax",
            "species_tax_key",
            "family_tax",
            "family_tax_key",
            "genus_tax_key",
            "genus_ft_key",
            "phylum_ft_key",
        ],
        errors="ignore",
        inplace=True,
    )

    # To adhere to the qiime metadata format
    taxonomy.rename(
        columns={"Feature ID": "feature-id", "genus_ft": "fungal_traits_genus"},
        inplace=True,
    )
    taxonomy.columns = taxonomy.columns.str.lower()
    taxonomy.set_index("feature-id", inplace=True)
    taxonomy.index = taxonomy.index.astype(str)

    return rachis.Metadata(taxonomy)
