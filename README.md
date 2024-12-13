# Panako Sample ID wrapper

Small wrapper around Panako that calculates mAP for tracks used in the Sample ID project.

## Requirements

- Python 3: any version should be fine, and no dependencies are needed
- Panako installed and accessible on the command line by running `panako`

## Running the script

1. Install Panako following the instructions [on the Git repository](https://github.com/JorenSix/Panako)
2. Test that you can access panako on the command line just by running `panako`. If you get an output, you're all good.
3. Place audio files for the sample ID project inside `audio`. These should be labelled as either `T001.wav`, `T002.wav`, ... (for query and candidate tracks) or `X001.wav`, `X002.wav` (for noise tracks). Naming *must* follow the order given in Van Balen et al. (2011), appendix.
4. Make sure Python is installed (no dependencies needed) and run `python runme.py`

The script will store all the candidate and noise tracks in the database, then query all the query tracks and calculate the average precision for each using the modifications referred to in our paper.
