"""London borough clean-air policy prioritisation.

Run from the project directory with:
    python analysis.py --zip path/to/LAEI2022-Population-Exposure-and-Proportion-Road-Length-Exceeding-Stats.zip

The script creates a borough ranking, a sensitivity table and three figures in
the ``outputs`` directory. It uses only the official LAEI 2022 workbooks.
"""

from __future__ import annotations

import argparse
import math
import re
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


NO2_THRESHOLD = 20.0
PM25_THRESHOLD = 10.0

# Baseline policy weights. These are explicit value judgements, not estimated
# parameters. Alternative severity/scale weights are tested below.
GROUP_WEIGHTS = {
    "population": 0.40,
    "schools": 0.30,
    "health": 0.30,
}
BASELINE_SEVERITY_WEIGHT = 0.50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prioritise London boroughs for clean-air intervention."
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        required=True,
        help="Path to the downloaded LAEI 2022 population-exposure ZIP file.",
    )
    parser.add_argument(
        "--output",
        dest="output_dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for CSV tables and PNG figures (default: outputs).",
    )
    return parser.parse_args()


def safe_extract(zip_path: Path, destination: Path) -> None:
    """Extract a ZIP while rejecting paths outside the destination."""
    destination = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if destination not in member_path.parents and member_path != destination:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        archive.extractall(destination)


def find_workbook(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one file named {filename!r}; found {len(matches)}."
        )
    return matches[0]


def borough_key(value: object) -> str:
    """Create a stable key across small naming differences in the workbooks."""
    text = str(value).lower().replace("&", "and")
    return re.sub(r"[^a-z]+", "", text)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_population_data(aq_workbook: Path) -> pd.DataFrame:
    """Read the borough blocks for NO2 >20 and PM2.5 >10 exposure."""
    no2 = pd.read_excel(aq_workbook, sheet_name="Population_NO2", header=None)
    pm25 = pd.read_excel(aq_workbook, sheet_name="Population_PM2.5", header=None)

    # The official workbook contains several formatted blocks. These two blocks
    # hold the 33 borough rows for the selected interim thresholds.
    no2_block = pd.DataFrame(
        {
            "borough": no2.iloc[136:169, 1].values,
            "population_total": numeric(no2.iloc[136:169, 9]).values,
            "population_no2_exposed": numeric(no2.iloc[136:169, 10]).values,
            "population_no2_rate": numeric(no2.iloc[136:169, 11]).values,
            "population_weighted_no2": numeric(no2.iloc[136:169, 3]).values,
        }
    )
    pm25_block = pd.DataFrame(
        {
            "borough_pm25": pm25.iloc[27:60, 1].values,
            "population_pm25_exposed": numeric(pm25.iloc[27:60, 10]).values,
            "population_pm25_rate": numeric(pm25.iloc[27:60, 11]).values,
            "population_weighted_pm25": numeric(pm25.iloc[27:60, 3]).values,
        }
    )

    population = pd.concat(
        [no2_block.reset_index(drop=True), pm25_block.reset_index(drop=True)], axis=1
    )
    if not (
        population["borough"].map(borough_key)
        == population["borough_pm25"].map(borough_key)
    ).all():
        raise ValueError("NO2 and PM2.5 borough rows are not aligned.")

    population["borough_key"] = population["borough"].map(borough_key)
    return population.drop(columns="borough_pm25")


def aggregate_sites(
    sites: pd.DataFrame,
    id_column: str,
    prefix: str,
) -> pd.DataFrame:
    """Aggregate school or health-site exposure by borough."""
    required = {
        "Borough",
        id_column,
        "2022 Average NO2 (ug/m3)",
        "2022 Average PM2.5 (ug/m3)",
    }
    missing = required.difference(sites.columns)
    if missing:
        raise ValueError(f"Missing columns in {prefix} data: {sorted(missing)}")

    frame = sites.copy()
    frame["borough_key"] = frame["Borough"].map(borough_key)
    frame["above_no2"] = frame["2022 Average NO2 (ug/m3)"] > NO2_THRESHOLD
    frame["above_pm25"] = frame["2022 Average PM2.5 (ug/m3)"] > PM25_THRESHOLD

    grouped = frame.groupby("borough_key", as_index=False).agg(
        site_count=(id_column, "size"),
        no2_exposed_count=("above_no2", "sum"),
        pm25_exposed_count=("above_pm25", "sum"),
        no2_exposed_rate=("above_no2", "mean"),
        pm25_exposed_rate=("above_pm25", "mean"),
        mean_no2=("2022 Average NO2 (ug/m3)", "mean"),
        mean_pm25=("2022 Average PM2.5 (ug/m3)", "mean"),
    )
    return grouped.rename(
        columns={column: f"{prefix}_{column}" for column in grouped.columns if column != "borough_key"}
    )


def minmax(series: pd.Series) -> pd.Series:
    spread = series.max() - series.min()
    if spread == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / spread


def build_ranking(
    population: pd.DataFrame,
    schools: pd.DataFrame,
    health: pd.DataFrame,
) -> pd.DataFrame:
    data = population.merge(schools, on="borough_key", validate="one_to_one")
    data = data.merge(health, on="borough_key", validate="one_to_one")

    if len(data) != 33:
        raise ValueError(f"Expected 33 London boroughs; found {len(data)}.")

    # Exposure severity is rate-based. Scale uses affected counts, normalised
    # within London so populations, schools and health sites remain comparable.
    data["population_severity"] = (
        data["population_no2_rate"] + data["population_pm25_rate"]
    ) / 2
    data["school_severity"] = (
        data["schools_no2_exposed_rate"] + data["schools_pm25_exposed_rate"]
    ) / 2
    data["health_severity"] = (
        data["health_no2_exposed_rate"] + data["health_pm25_exposed_rate"]
    ) / 2

    data["population_exposed_count"] = (
        data["population_no2_exposed"] + data["population_pm25_exposed"]
    ) / 2
    data["school_exposed_count"] = (
        data["schools_no2_exposed_count"] + data["schools_pm25_exposed_count"]
    ) / 2
    data["health_exposed_count"] = (
        data["health_no2_exposed_count"] + data["health_pm25_exposed_count"]
    ) / 2

    data["severity_index"] = (
        GROUP_WEIGHTS["population"] * data["population_severity"]
        + GROUP_WEIGHTS["schools"] * data["school_severity"]
        + GROUP_WEIGHTS["health"] * data["health_severity"]
    )
    data["scale_index"] = (
        GROUP_WEIGHTS["population"] * minmax(data["population_exposed_count"])
        + GROUP_WEIGHTS["schools"] * minmax(data["school_exposed_count"])
        + GROUP_WEIGHTS["health"] * minmax(data["health_exposed_count"])
    )

    scenarios = {
        "baseline_score": 0.50,
        "severity_focused_score": 0.70,
        "scale_focused_score": 0.30,
    }
    for score_column, severity_weight in scenarios.items():
        data[score_column] = 100 * (
            severity_weight * data["severity_index"]
            + (1 - severity_weight) * data["scale_index"]
        )
        rank_column = score_column.replace("score", "rank")
        data[rank_column] = (
            data[score_column].rank(ascending=False, method="min").astype(int)
        )

    data["rank_change_range"] = data[
        ["baseline_rank", "severity_focused_rank", "scale_focused_rank"]
    ].max(axis=1) - data[
        ["baseline_rank", "severity_focused_rank", "scale_focused_rank"]
    ].min(axis=1)

    upper_cutoff = math.ceil(len(data) * 0.25)
    lower_cutoff = math.floor(len(data) * 0.75)
    data["priority_tier"] = np.select(
        [data["baseline_rank"] <= upper_cutoff, data["baseline_rank"] <= lower_cutoff],
        ["Tier 1", "Tier 2"],
        default="Tier 3",
    )

    return data.sort_values("baseline_rank").reset_index(drop=True)


def save_charts(ranking: pd.DataFrame, output_dir: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    palette = {"Tier 1": "#b43c3c", "Tier 2": "#d89c3d", "Tier 3": "#547aa5"}

    top = ranking.head(10).sort_values("baseline_score")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(
        top["borough"],
        top["baseline_score"],
        color=[palette[tier] for tier in top["priority_tier"]],
    )
    ax.set_title("Top 10 boroughs by clean-air priority score")
    ax.set_xlabel("Priority score (0–100)")
    ax.set_ylabel("")
    ax.set_xlim(0, 100)
    for index, value in enumerate(top["baseline_score"]):
        ax.text(value + 1, index, f"{value:.1f}", va="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(output_dir / "01_top_10_priority_score.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(
        data=ranking,
        x="scale_index",
        y="severity_index",
        hue="priority_tier",
        palette=palette,
        s=130,
        alpha=0.8,
        ax=ax,
    )
    label_offsets = {
        "Westminster": (6, 8),
        "Tower Hamlets": (6, 8),
        "Camden": (6, -12),
        "Southwark": (6, 10),
        "Hackney": (6, -12),
        "Wandsworth": (6, -12),
        "Lambeth": (-55, 10),
        "Kensington & Chelsea": (6, 8),
        "Islington": (6, 8),
        "Ealing": (6, 8),
    }
    label_rows = pd.concat(
        [ranking.head(10), ranking.loc[ranking["borough"] == "City of London"]]
    ).drop_duplicates(subset="borough")
    label_offsets["City of London"] = (6, 8)
    for _, row in label_rows.iterrows():
        offset = label_offsets.get(row["borough"], (5, 5))
        ax.annotate(
            row["borough"],
            (row["scale_index"], row["severity_index"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_title("Exposure severity and scale by borough")
    ax.set_xlabel("Scale index")
    ax.set_ylabel("Exposure severity index")
    ax.legend(title="Priority tier", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_dir / "02_severity_vs_scale.png", dpi=200)
    plt.close(fig)

    components = (
        ranking.head(10)
        .set_index("borough")[["population_severity", "school_severity", "health_severity"]]
        .rename(
            columns={
                "population_severity": "Population",
                "school_severity": "Schools",
                "health_severity": "Health sites",
            }
        )
    )
    fig, ax = plt.subplots(figsize=(9, 8))
    sns.heatmap(
        components,
        annot=True,
        fmt=".0%",
        cmap="YlOrRd",
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Share above selected thresholds"},
        ax=ax,
    )
    ax.set_title("Exposure components for the top 10 boroughs")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(output_dir / "03_exposure_components.png", dpi=200)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    zip_path = args.zip_path.resolve()
    output_dir = args.output_dir.resolve()
    extracted_dir = output_dir / "extracted_data"

    if not zip_path.exists():
        raise FileNotFoundError(zip_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_extract(zip_path, extracted_dir)

    aq_workbook = find_workbook(
        extracted_dir, "LAEI2022_AQExceedingPopulation_RoadStats.xlsx"
    )
    school_workbook = find_workbook(
        extracted_dir, "LAEI2022_Schools Summary.xlsx"
    )
    health_workbook = find_workbook(
        extracted_dir, "LAEI2022_Hospital and CareHomes Summary.xlsx"
    )

    population = load_population_data(aq_workbook)
    school_sites = pd.read_excel(
        school_workbook, sheet_name="EdubaseAllEstablishments_GLA"
    )
    schools = aggregate_sites(school_sites, id_column="ID", prefix="schools")

    care_homes = pd.read_excel(health_workbook, sheet_name="CareHomeSites_GLA")
    hospitals = pd.read_excel(health_workbook, sheet_name="HospitalSites_GLA")
    health_sites = pd.concat(
        [
            care_homes[
                [
                    "Borough",
                    "ID",
                    "2022 Average NO2 (ug/m3)",
                    "2022 Average PM2.5 (ug/m3)",
                ]
            ],
            hospitals[
                [
                    "Borough",
                    "ID",
                    "2022 Average NO2 (ug/m3)",
                    "2022 Average PM2.5 (ug/m3)",
                ]
            ],
        ],
        ignore_index=True,
    )
    health = aggregate_sites(health_sites, id_column="ID", prefix="health")

    ranking = build_ranking(population, schools, health)
    ranking.to_csv(output_dir / "borough_priority_ranking.csv", index=False)

    sensitivity_columns = [
        "borough",
        "baseline_rank",
        "severity_focused_rank",
        "scale_focused_rank",
        "rank_change_range",
    ]
    ranking[sensitivity_columns].to_csv(
        output_dir / "sensitivity_analysis.csv", index=False
    )
    save_charts(ranking, output_dir)

    print("\nTop 10 boroughs")
    print(
        ranking[["baseline_rank", "borough", "baseline_score", "priority_tier"]]
        .head(10)
        .to_string(index=False, float_format=lambda value: f"{value:.1f}")
    )
    print(f"\nOutputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
