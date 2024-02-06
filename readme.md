I. Requirement
[Defects4J](https://github.com/rjust/defects4j)
[TBar Customized](https://github.com/squaresLab/TBar)
Follow the TBar setup from the readme. Make sure to check out all D4J projects.

II. Replicate results

RQ1 Fault localization: `python3 analysis_notebooks/rq1_fl.py`

RQ2-3 Patch classification: Run the interactive jupyter notebook analysis_notebooks/patch_analysis.ipynb


III. Rerun entropy from scratch

`python3 fl_scores/process_llmao_prior.py`

`python3 fl_scores/process_sbfl.py`

`python3 fl_scores/process_transfer.py`

`python3 patches/shib_panther_patch_entropy.py`

`python3 patches/generate_tbar_patches.py`

`python3 patches/tbar_patch_entropy.py`