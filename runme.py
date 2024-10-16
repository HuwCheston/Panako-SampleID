import subprocess
import csv
import os

# Hardcoded file paths
file_path = 'candidates.txt'
output_csv = 'resolved_ids.csv'

# Check if the input file exists
if not os.path.isfile(file_path):
    print(f"File not found: {file_path}")
    exit(1)

elif os.path.isfile(output_csv):
    print(f"File already exists: {output_csv}")
    print("Skipping resolve IDs...")

else:
    # Open the CSV file for writing
    with open(output_csv, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Input', 'Output'])  # Write the header

        # Read the input file and process each line
        with open(file_path, 'r') as infile:
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

print(f"Results saved to {output_csv}")
