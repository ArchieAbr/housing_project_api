import csv

INPUT_CSV = "Management_information_-_state-funded_schools_-_latest_inspections_as_at_28_Feb_2026.csv"
OUTPUT_CSV = "leeds_ofsted_data.csv"
TARGET_AUTHORITY = "Leeds"

def filter_csv(input_csv, output_csv, target_authority):
    encodings = ["utf-8", "cp1252", "latin1"]
    for enc in encodings:
        try:
            with open(input_csv, newline='', encoding=enc) as infile:
                reader = csv.DictReader(infile)
                filtered_rows = [row for row in reader if row.get("Local authority", "").strip().lower() == target_authority.lower()]
                if not filtered_rows:
                    print(f"No rows found for local authority: {target_authority}")
                else:
                    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
                        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                        writer.writeheader()
                        writer.writerows(filtered_rows)
                    print(f"Filtered data written to {output_csv} ({len(filtered_rows)} rows)")
                return
        except UnicodeDecodeError:
            continue
    print("Failed to read the CSV file with common encodings. Please check the file encoding.")

if __name__ == "__main__":
    filter_csv(INPUT_CSV, OUTPUT_CSV, TARGET_AUTHORITY)
