# Prioritising Clean-Air Interventions Across London Boroughs

## Question of the research

Which London boroughs should receive priority clean-air interventions when both the severity and scale of exposure are considered?

## Project overview

This project uses the London Atmospheric Emissions Inventory 2022 to compare exposure across the 32 London boroughs and the City of London. It combines population exposure with pollution levels around schools, hospitals and care homes.

## Data source

Greater London Authority and Transport for London, *LAEI 2022: Population, School, Hospitals, Care Home Exposure and Proportion of Road Length Exceeding*.

Download the ZIP from the [London Atmospheric Emissions Inventory 2022](https://data.london.gov.uk/dataset/london-atmospheric-emissions-inventory-laei-2022-2lg5g) page. There it's possible to find 3 excel files covering population exposure and road-length exceedances, air-pollution exposure around schools and exposure around hospitals and care homes.

The analysis uses:

- population exposure above 20 µg/m³ annual NO₂;
- population exposure above 10 µg/m³ annual PM2.5;
- schools above the same thresholds;
- hospitals and care homes above the same thresholds.

The selected thresholds—20 µg/m³ for NO₂ and 10 µg/m³ for PM2.5—were chosen for three reasons: 

1) They have a health-based foundation, as both values correspond to interim targets established in the 2021 WHO Air Quality Guidelines.
2) They are policy-relevant because they correspond to the annual limits established by the European Union for 2030 (although UK is no longer in UE).
3) They are analytically useful: the current UK limit of 40 µg/m³ for NO₂ is exceeded by very few observations in the 2022 dataset, whereas the stricter WHO guideline of 10 µg/m³ is exceeded across all of London.

## Method

The baseline score is composed by two other indexes:

1. **Exposure severity:** the percentage of each group exposed above the selected threshold
2. **Exposure scale:** the number of affected residents, schools and health sites, normalised across boroughs

Within each part, population receives a 40% weight, schools 30% and health sites 30% : population exposure receives 40% because the model’s primary goal is to allocate public resources according to the overall number and proportion of residents affected. Schools receive 30% because children are particularly vulnerable to air pollution and spend a substantial amount of time at school. Hospitals and care homes receive the same weight (30%) because they contain patients, older residents and other health-vulnerable groups. The decision of assigning equal weights to schools and healthcare because I didn't have sufficient evidence to prioritise one vulnerable group over the other.

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

A high priority score means that a borough combines relatively severe exposure with a relatively large number of affected residents, schools, hospitals and care homes: exposure severity reflects the proportion of each group living above the selected NO₂ and PM2.5 thresholds, while exposure scale reflects the absolute number of people and vulnerable sites affected relative to other London boroughs. 
So it's understandable a borough with both indexes high may requires stronger attention from the London's policy makers.
The score is not a percentage measure of pollution: for example, Westminster’s score of 89.6 does not mean that its pollution level or health risk is 89.6%. It's a relative priority index: Westminster receives the highest score because it presents the strongest combination of exposure severity and affected scale compared with the other London boroughs.
Based the final scores calculated, I made a ranking of the different boroughs based on the interventions should be done:

Tier 1 – Immediate assessment and prioritised intervention: conduct detailed local analysis to clearly identify pollution hotspots, emission sources and vulnerable populations. It's mandatory in these areas the implementation of evidence-based measures.
Tier 2 – Targeted monitoring and prevention: strengthen monitoring around exposed schools, hospitals and care homes, while introducing proportionate preventive measures to avoid further deterioration.
Tier 3 – Routine monitoring and maintenance: maintain existing air-quality controls, monitor changes over time and redefine priorities if exposure indicators begin to worsen

## Policy Reccomandation


## Limitations

- The analysis uses 2022 data
- The selected thresholds and score weights are explicit analytical choices.
- Counts for different pollutants may refer to overlapping people or sites and must not be added as unique exposures.
- The analysis does not include intervention costs, deprivation or borough implementation capacity.
- The score supports further investigation; it does not prove the effectiveness of a particular policy.

## References

