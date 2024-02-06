I. Requirement
================
Clone the following repos directly into the root folder of this repository.
 - [Defects4J](https://github.com/rjust/defects4j)
 - [TBar Customized](https://github.com/squaresLab/TBar)

Follow the TBar setup from the readme. Make sure to check out all D4J projects.


All requirements for running the replication package is pre-installed in this [Docker image](https://hub.docker.com/repository/docker/aidanben/entropy-apr/general)

Run your own docker container as follows:
```
docker run --name=entropy -it \
--mount type=bind,src=entropy-apr-replication/,dst=/home \
docker.io/aidanben/entropy-apr:latest
```

All LLMs involved will be downloaded automatically during your first run.

II. Replicate results
================

1. RQ1 Fault localization (FL):
The following script prints out fault localization top-score values for entropy and prior FL tools.
   - `python3 analysis_notebooks/rq1_fl.py`

2. RQ2-3 Patch classification:
Run the interactive ipynb notebook. 
   - `analysis_notebooks/patch_analysis.ipynb`.
This notebook provides results on patch ranking, patch classification, and generates plots used in the paper.


III. Rerun entropy from scratch
================
1. The following 3 scripts generates entropy for FL results:

    - `python3 fl_scores/process_llmao_prior.py`
    - `python3 fl_scores/process_sbfl.py`
    - `python3 fl_scores/process_transfer.py`

2. The following 3 scripts generates entropy for patch ranking results.

    - `python3 patches/shib_panther_patch_entropy.py`
    - `python3 patches/generate_tbar_patches.py`
    - `python3 patches/tbar_patch_entropy.py`