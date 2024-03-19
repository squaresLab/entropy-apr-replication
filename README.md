I. Requirement
================
Clone the following repos directly into the root folder of this repository.
 - [Defects4J](https://github.com/rjust/defects4j)

Follow the TBar setup from the readme in TBar folder. Make sure to check out all D4J projects.

Ensure you have successfully installed CUDA (version >= 11.4, preferably 11.7) along with the necessary drivers. Additionally, make sure you have installed torch (version 2.0.1).

Next, we have provided an init_env.sh script to simplify the installation of smaller required packages. Execute the following command to run the script:
```bash
sh init_env.sh
```

All LLMs involved will be downloaded automatically during your first run.

II. Replicate results
================
1. RQ1 Fault localization (FL):
The following script prints out fault localization top-score values for entropy and prior FL tools.
   - `python3 analysis_notebooks/rq1_fl.py`

1. RQ2-3 Patch classification:
Run the interactive ipynb notebook. 
   - `analysis_notebooks/patch_analysis.ipynb`.
This notebook provides results on patch ranking, patch classification, and generates plots used in the paper.


III. Rerun entropy from scratch
================
1. The following 3 scripts generate entropy for FL results:

    - `python3 fl_scores/process_llmao_prior.py`
    - `python3 fl_scores/process_sbfl.py`
    - `python3 fl_scores/process_transfer.py`

2. The following scripts generate entropy for patch efficiency results:
   - `python3 patches/generate_tbar_patches.py tbar_vanilla`
   - `python3 patches/generate_tbar_patches.py tbar_testcache`
   - `python3 patches/generate_tbar_patches.py tbar_testcache_ranked`

3. The following 3 scripts generate entropy for patch ranking results.
    - `python3 patches/shib_panther_patch_entropy.py`
    - `python3 patches/tbar_patch_entropy.py`