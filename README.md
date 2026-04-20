# q2-fungal-traits

`q2-fungal-traits` is a **[QIIME 2](https://qiime2.org) plugin** that annotates fungal taxonomic data with
ecological traits and spore volumes derived from published fungal trait datasets.
The plugin provides an **`annotate` action** that generates a metadata table containing fungal trait annotations and spore volume estimates based on the taxonomy of input sequences.

---

# What the plugin does

The plugin links taxonomic assignments to known fungal trait datasets and produces a metadata table with:

- ecological fungal lifestyle traits
- estimated spore volumes

Trait and spore annotations are inferred from the taxonomy hierarchy.

### Spore volume estimation

Spore volume annotations are assigned hierarchically:

1. **Species level**
   If a species match exists in the spore dataset, that value is used.

2. **Genus level fallback**
   If no species-level match exists, the **geometric mean of spore volumes within the genus** is used.

3. **Family level fallback**
   If no genus-level match exists, the **geometric mean of spore volumes within the family** is used.

### Trait annotation behavior

- Trait annotations are assigned **at the genus level**.
- If genus-level taxonomy is missing, **trait annotation is skipped**, and only spore
  volume annotation is performed.

---


# Data sources

The annotations rely on two curated fungal datasets.

## Fungal trait dataset

Ecological trait data are derived from:

Põlme, S., Abarenkov, K., Henrik Nilsson, R. et al. FungalTraits: a user-friendly traits database of fungi and fungus-like stramenopiles. Fungal Diversity 105, 1–16 (2020). https://doi.org/10.1007/s13225-020-00466-2

This dataset links ~10210 fungal genera to 17 ecological traits like lifestyle and
fruit body type.

---

## Spore volume dataset

Spore volume estimates are derived from:

Abrego, N., Furneaux, B., Hardwick, B. et al. Airborne DNA reveals predictable spatial and seasonal dynamics of fungi. Nature 631, 835–842 (2024). https://doi.org/10.1038/s41586-024-07658-9

This dataset provides measured spore dimensions for ~30000 fungal species.

---

# Usage

The plugin provides a single action: `annotate`.

This action takes taxonomic assignments as input and produces a metadata table with fungal trait annotations and spore volume estimates.


```bash
qiime fungal-traits annotate \
  --i-taxonomy taxonomy.qza \
  --o-metadata fungal_traits.qza
```

The metadata output can be examined in the browser:

```bash
qiime metadata tabulate \
  --m-input-file fungal_traits.qza \
  --o-visualization fungal_traits.qzv
```
```bash
qiime tools view fungal_traits.qzv
```

---

# Output format

The `annotate` action produces a metadata table where each row corresponds to a feature (e.g., ASV or sequence) and columns contain taxonomic information, ecological trait annotations, and estimated spore volumes.

| Column | Description |
|------|-------------|
| feature-id | Unique identifier of the feature (e.g., ASV or sequence ID). |
| taxon | Taxonomic assignment for the feature. |
| fungal_traits_genus | Genus used for fungal trait matching. |
| primary_lifestyle | Primary ecological lifestyle (e.g., saprotroph, pathogen, symbiont). |
| secondary_lifestyle | Secondary lifestyle annotation if present. |
| comment_on_lifestyle_template | Notes or comments related to the lifestyle classification. |
| endophytic_interaction_capability_template | Indicates whether the genus has the capacity for endophytic interactions with plants. |
| plant_pathogenic_capacity_template | Indicates whether the genus includes plant pathogenic taxa. |
| decay_substrate_template | Substrate type the fungus is associated with during decay (e.g., wood, litter). |
| decay_type_template | Type of decay performed by the fungus (e.g., white rot, brown rot). |
| aquatic_habitat_template | Indicates whether taxa are associated with aquatic environments. |
| animal_biotrophic_capacity_template | Indicates whether taxa have biotrophic interactions with animals. |
| specific_hosts | Known host organisms associated with the fungus. |
| growth_form_template | Morphological growth form (e.g., filamentous mycelium, yeast-like). |
| fruitbody_type_template | Type of fruiting body produced by the fungus. |
| hymenium_type_template | Type of hymenium structure present in reproductive structures. |
| ectomycorrhiza_exploration_type_template | Exploration type for ectomycorrhizal fungi. |
| ectomycorrhiza_lineage_template | Phylogenetic lineage associated with ectomycorrhizal fungi. |
| primary_photobiont | Primary photobiont partner in lichenized fungi. |
| secondary_photobiont | Secondary photobiont partner if present. |
| mitospores_taxon | Taxon used to match mitospore measurements. |
| mitospores_volume | Estimated volume of mitospores. |
| mitospores_matching_level | Taxonomic level used to determine mitospore volume (species, genus, or family). |
| meiospores_taxon | Taxon used to match meiospore measurements. |
| meiospores_volume | Estimated volume of meiospores. |
| meiospores_matching_level | Taxonomic level used to determine meiospore volume (species, genus, or family). |
| multinucleate_sexual_spores_taxon | Taxon used to match multinucleate sexual spore measurements. |
| multinucleate_sexual_spores_volume | Estimated volume of multinucleate sexual spores. |
| multinucleate_sexual_spores_matching_level | Taxonomic level used to determine multinucleate sexual spore volume (species, genus, or family). |
| multinucleate_asexual_spores_taxon | Taxon used to match multinucleate asexual spore measurements. |
| multinucleate_asexual_spores_volume | Estimated volume of multinucleate asexual spores. |
| multinucleate_asexual_spores_matching_level | Taxonomic level used to determine multinucleate asexual spore volume (species, genus, or family). |

# Handling of duplicated genera in the fungal trait dataset

Several inconsistencies exist in the original fungal trait dataset. These are handled during annotation.

### Completely duplicated rows

Three rows in the dataset are exact duplicates.
These are removed automatically if encountered.

### Duplicate genus with incomplete data

One genus entry was duplicated with differing completeness.
The less complete row was removed.

Removed row:

jrk00561 | Ascomycota | Dothideomycetes | Dothideomycetes order incertae sedis | Paranectriellaceae | Paranectriella |   | litter_saprotroph |   |   | no_endophytic_capacity |   | leaf/fruit/seed |   | non-aquatic |   |   | filamentous_mycelium

### Genera present in multiple families

The genera Campanulospora and Caudospora appear in **two different families** in the
dataset. To resolve this ambiguity, the plugin matches traits using **both genus and phylum**
for these genera.

---

## About

The `q2-fungal-traits` Python package was [created from a template](https://develop.qiime2.org/en/latest/plugins/tutorials/create-from-template.html).
To learn how to use QIIME 2, refer to the [QIIME 2 User Documentation](https://docs.qiime2.org).
To learn QIIME 2 plugin development, refer to [*Developing with QIIME 2*](https://develop.qiime2.org).
