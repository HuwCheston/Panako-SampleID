#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Little wrapper around panako that calculates mAP for tracks used in the Sample ID project"""


import subprocess
import csv
import os


def store_candidates(candidate_filepath: str = 'candidates.txt') -> None:
    with open(candidate_filepath, 'r') as op:
        for line in list(op):
            output = subprocess.check_output(['panako', 'AVAILABLE_PROCESSORS=0', 'STRATEGY=panako', 'store',  line.strip()], text=True).strip()
            print(output)


def resolve_panako_ids_to_tracknames(
        candidate_filepath: str = 'candidates.txt',
        output_filepath: str = 'resolved_ids.csv'
) -> dict:
    if os.path.isfile(output_filepath):
        print(f"File already exists: {output_filepath}")
        print("Skipping resolve IDs...")
    else:
        # Open the CSV file for writing
        with open(output_filepath, mode='w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)    # Don't need a header
            # Read the input file and process each line
            with open(candidate_filepath, 'r') as infile:
                for line in infile:
                    print('Resolving ID for track: ', line)
                    line = line.strip()  # Remove leading/trailing whitespace
                    # Execute the command and capture the output
                    try:
                        output = subprocess.check_output(['panako', 'STRATEGY=panako', 'resolve', line], text=True).strip()
                    except subprocess.CalledProcessError as e:
                        output = f"Error: {e}"
                    # Write the line and output to the CSV file
                    csv_writer.writerow([line, output])
    with open(output_filepath, mode='r') as infile:
        reader = csv.reader(infile)
        return {int(rows[1]): rows[0] for rows in reader}


def load_query_candidate_relations(relations_fpath: str = 'relations.txt') -> dict:
    relations = {}
    with open(relations_fpath, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            candidate, query = f'audio/{row[0]}.wav', f'audio/{row[1]}.wav'
            if query in relations.keys():
                if candidate not in relations[query]:
                    relations[query].append(candidate)
            else:
                relations[query] = [candidate]
    return relations


def query_panako(query_filename: str) -> list[str]:
    print('Querying: ', query_filename)
    opt = [
        'AVAILABLE_PROCESSORS=0',
        'PANAKO_MIN_HITS_UNFILTERED=1', 
        'PANAKO_MIN_HITS_FILTERED=1', 
        'PANAKO_MIN_MATCH_DURATION=0.1',
        'PANAKO_MIN_SEC_WITH_MATCH=0.01'
        # 'PANAKO_MIN_TIME_FACTOR=0.6',
        # 'PANAKO_MAX_TIME_FACTOR=1.4',
        # 'PANAKO_MIN_FREQ_FACTOR=0.6',
        # 'PANAKO_MAX_FREQ_FACTOR=1.4',
    ]
    res = subprocess.check_output(['panako', *opt, 'STRATEGY=panako', 'query', query_filename.strip()], text=True).strip()
    res = res.splitlines()[1:-1]
    query_hits = []
    for cand in res:
        # Get the ID as second word
        id_ = cand.split(' ; ')[5]
        match_start, match_stop = float(cand.split(' ; ')[3]), float(cand.split(' ; ')[4])
        match_duration = match_stop - match_start
        id_ = str(os.path.sep.join(i for i in id_.split(os.path.sep)[-2:]))
        n_hits = int(cand.split(' ; ')[9])
        query_hits.append((id_, n_hits, match_duration))
    return [i[0] for i in sorted(query_hits, key=lambda x: (x[1], x[2]), reverse=True)]


def compute_average_precision(ground_truth_candidates, panako_candidates):
    precisions_this_query = []
    relevant_count = 0
    for idx, candidate in enumerate(panako_candidates):
        if candidate in ground_truth_candidates:
            relevant_count += 1
            precisions_this_query.append(relevant_count / (idx + 1))
    if len(precisions_this_query) == 0:
        return 0.
    else:
        return sum(precisions_this_query) / len(precisions_this_query)


if __name__ == "__main__":
    print('Panako mAP calculator for Sample ID project')

    print('Storing all candidate hashes in database...')
    store_candidates()

    print('Loading query-candidate relations...')
    query_cand_relations = load_query_candidate_relations()
    print(f'... loaded {len(list(query_cand_relations.keys()))} query tracks')

    average_precisions = []
    for query, ground_truths in query_cand_relations.items():
        ranked_candidates_panako = query_panako(query)
        ap = compute_average_precision(ground_truths, ranked_candidates_panako)
        print(f"Query {query}")
        print(f"Ground truth candidates: {ground_truths}")
        print(f"Ranked panako candidates: {ranked_candidates_panako}")
        print(f"Average precision: ", ap)
        print('\n\n\n')
        average_precisions.append(ap)

    mean_average_precision = sum(average_precisions) / len(average_precisions)
    print('Panako mAP: ', mean_average_precision)
    print('Finished!')
