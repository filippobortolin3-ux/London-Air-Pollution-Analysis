# Prioritising Clean-Air Interventions Across London Boroughs

## Question of the research

Which London boroughs should receive priority clean-air interventions when both the severity and scale of exposure are considered?

## Project overview
This project uses the London Atmospheric Emissions Inventory 2022 to compare exposure across the 32 London boroughs and the City of London. It combines population exposure with pollution levels around schools, hospitals and care homes.

## Data source

Greater London Authority and Transport for London, *LAEI 2022: Population, School, Hospitals, Care Home Exposure and Proportion of Road Length Exceeding*.

Download the ZIP from the [London Atmospheric Emissions Inventory 2022](https://data.london.gov.uk/dataset/london-atmospheric-emissions-inventory-laei-2022-2lg5g) page.

The analysis uses:

- population exposure above 20 µg/m³ annual NO₂;
- population exposure above 10 µg/m³ annual PM2.5;
- schools above the same thresholds;
- hospitals and care homes above the same thresholds.

These thresholds are used as practical interim benchmarks. They are not presented as the current WHO guideline values.

## Method

The baseline score has two parts:

1. **Exposure severity:** the percentage of each group exposed above the selected thresholds.
2. **Exposure scale:** the number of affected residents, schools and health sites, normalised across boroughs.

Within each part, population receives a 40% weight, schools 30% and health sites 30%. The final score assigns equal weight to severity and scale.

Because these weights represent policy choices rather than estimated parameters, the script also tests severity-focused and scale-focused scenarios.

## Run the analysis

Install the required packages:

```bash
pip install pandas numpy matplotlib seaborn openpyxl
```

Then run:

```bash
python analysis.py --zip "/path/to/LAEI2022-Population-Exposure-and-Proportion-Road-Length-Exceeding-Stats.zip"
```

The script creates:

- `borough_priority_ranking.csv`;
- `sensitivity_analysis.csv`;
- `01_top_10_priority_score.png`;
- `02_severity_vs_scale.png`;
- `03_exposure_components.png`.

## Interpretation

A high score means that a borough combines relatively severe exposure with a relatively large affected population or number of vulnerable sites. The score is useful for screening and prioritisation. It should not be interpreted as a complete cost-benefit analysis.

The results support three policy tiers:

- **Tier 1:** detailed local assessment and early intervention;
- **Tier 2:** targeted monitoring and prevention;
- **Tier 3:** routine monitoring and maintenance.

Potential Tier 1 actions include school-street measures, targeted monitoring near hospitals and care homes, low-emission transport initiatives and source-specific investigation. The dataset identifies where exposure is concentrated but does not by itself establish which emission source caused it.

## Limitations

- Results use modelled 2022 annual concentrations rather than real-time sensor observations.
- The selected thresholds and score weights are explicit analytical choices.
- Counts for different pollutants may refer to overlapping people or sites and must not be added as unique exposures.
- The analysis does not include intervention costs, deprivation or borough implementation capacity.
- The score supports further investigation; it does not prove the effectiveness of a particular policy.

## Suggested CV description

**Independent Urban Analytics Project — London Air Quality**

- Developed a reproducible Python model combining population, school and healthcare exposure data across 33 London borough areas.
- Designed a severity-and-scale framework to prioritise clean-air interventions and tested ranking stability under alternative policy weights.
- Translated official LAEI 2022 data into a borough ranking, visual analysis and tiered policy recommendations.
