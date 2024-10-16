#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Little wrapper around panako that calculates mAP for tracks used in the Sample ID project"""


import subprocess
import csv
import os


def store_candidates(candidate_filepath: str = 'candidates.txt') -> None:
    with open(candidate_filepath, 'r') as op:
        for line in list(op):
            output = subprocess.check_output(['panako', 'store', line.strip()], text=True).strip()
            print(output)


def resolve_panako_ids_to_tracknames(
        candidate_filepath: str = 'candidates.txt',
        output_filepath: str = 'resolved_ids.csv'
) -> dict:
    if os.path.isfile(output_filepath):
        print(f"File already exists: {output_filepath}")
        print("Skipping resolve IDs...")
        with open(output_filepath, mode='r') as infile:
            reader = csv.reader(infile)
            return {rows[1]: rows[0] for rows in reader}
    else:
        mapper = {}
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
                        output = subprocess.check_output(['panako', 'resolve', line], text=True).strip()
                    except subprocess.CalledProcessError as e:
                        output = f"Error: {e}"
                    # Write the line and output to the CSV file
                    csv_writer.writerow([line, output])
                    mapper[line] = output
        return mapper


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


def query_panako(query_filename: str, candidate_id_resolver: dict) -> list[str]:
    print('Querying: ', query_filename)
    # opt ['PANAKO_MIN_HITS_UNFILTERED=1', 'PANAKO_MIN_HITS_FILTERED=1', 'PANAKO_MIN_MATCH_DURATION=1']
    res = subprocess.check_output(['panako', 'query', query_filename.strip()], text=True).strip()
    res = res.splitlines()[1:-1]
    query_hits = []
    for cand in res:
        # Get the ID as second word
        id_ = cand.split(' ')[1]
        try:
            matched_id = candidate_id_resolver[id_]
        except KeyError:
            print("Cannot resolve: ", id_)
        else:
            n_hits = int(cand.split(' ')[5])
            query_hits.append((matched_id, n_hits))
    return [i[0] for i in sorted(query_hits, key=lambda x: x[1], reverse=True)]


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

    print('Resolving panako IDs to actual filenames...')
    cand_mapper = resolve_panako_ids_to_tracknames()
    print(f'... loaded {len(list(cand_mapper.keys()))} candidate tracks')

    print('Loading query-candidate relations...')
    query_cand_relations = load_query_candidate_relations()
    print(f'... loaded {len(list(query_cand_relations.keys()))} query tracks')

    average_precisions = []
    for query, ground_truths in query_cand_relations.items():
        ranked_candidates_panako = query_panako(query, cand_mapper)
        ap = compute_average_precision(ground_truths, ranked_candidates_panako)
        average_precisions.append(ap)

    mean_average_precision = sum(average_precisions) / len(average_precisions)
    print('Panako mAP: ', mean_average_precision)
    print('Finished!')
