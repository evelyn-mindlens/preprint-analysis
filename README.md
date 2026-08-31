# preprint-analysis

Analysis code for the two 2026 MindLens Lab preprints on emotion perception.

- **Author:** Evelyn Kim ([ORCID 0009-0002-6649-5141](https://orcid.org/0009-0002-6649-5141))
- **Affiliation:** MindLens Lab · Singapore American School
- **Contact:** evelyn@mindlenslab.org
- **Project site:** https://mindlens-lab.vercel.app

## Related preprints

- Kim, E. (2026a). *Plural Emotion Readings in Short Social Video Clips.* PsyArXiv. DOI: TBA.
- Kim, E. (2026b). *Where One AI Diverges from Plural Human Readings.* PsyArXiv. DOI: TBA.

## What is in this repository

This repository holds the Python scripts used to generate figures and to run the AI stochasticity check for the two preprints. The MindLens Lab data-collection platform (the Next.js web application) is a separate project and is not included here.

- `analysis/generate_figures.py` — regenerates all figures for both preprints from the source CSVs, using the Okabe-Ito colorblind-safe palette.
- `analysis/stochasticity_check.py` — reproduces the 5-run × 7-iteration × 3-condition Gemini stochasticity check for the AI-comparison paper. Requires a Gemini API key.

## Where the data is

Anonymized participant response data are hosted on the Open Science Framework alongside the PsyArXiv preprints. Once the OSF DOI is issued, place the CSV files (`per_clip_stats_adults_final.csv`, `paper2_3condition_comparison_adults.csv`, `stochasticity_results.csv`) in the same directory as the scripts to reproduce the figures.

- **OSF Project:** DOI TBA.

## Reproducing the figures

```
pip install -r requirements.txt
python analysis/generate_figures.py
```

Figures land in `analysis/figures_v3/`.

## Reproducing the stochasticity check

```
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
python analysis/stochasticity_check.py
```

## Author contributions and AI-tool use

I used AI tools (Anthropic's Claude, via Cowork mode) to support code implementation, data checking, descriptive-statistics computation, repeated API execution for the stochasticity check, and manuscript editing. I designed the studies, curated the stimuli, collected the human data, defined the AI-comparison protocol, reviewed all analytical outputs, interpreted the findings, and take responsibility for the manuscripts and the code in this repository.

## License

MIT — see [LICENSE](LICENSE).

## How to cite

See [CITATION.cff](CITATION.cff). GitHub's "Cite this repository" button generates APA and BibTeX automatically.
