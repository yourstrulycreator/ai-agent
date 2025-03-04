import json
import csv
import os
import argparse

def json_to_csv(json_file, csv_file=None, fields=None):
    """
    Convert a JSON file to CSV format.
    
    Args:
        json_file (str): Path to the JSON file
        csv_file (str, optional): Path to the output CSV file. If not provided, 
                                 will use the same name as JSON file with .csv extension
        fields (list, optional): List of fields to include in the CSV. If not provided,
                                all fields from the first item will be used
    
    Returns:
        str: Path to the created CSV file
    """
    # Determine output CSV file path if not provided
    if not csv_file:
        base_name = os.path.splitext(json_file)[0]
        csv_file = f"{base_name}_converted.csv"
    
    try:
        # Read JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        if not data:
            print(f"No data found in {json_file}")
            return None
        
        # Determine fields to include
        if not fields:
            fields = list(data[0].keys())
        
        # Write to CSV
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Successfully converted {json_file} to {csv_file}")
        print(f"Processed {len(data)} records with fields: {', '.join(fields)}")
        return csv_file
    
    except json.JSONDecodeError:
        print(f"Error: {json_file} is not a valid JSON file")
    except Exception as e:
        print(f"Error converting file: {e}")
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Convert JSON file to CSV')
    parser.add_argument('json_file', help='Path to the JSON file')
    parser.add_argument('--output', '-o', help='Path to the output CSV file')
    parser.add_argument('--fields', '-f', nargs='+', help='Fields to include in the CSV')
    
    args = parser.parse_args()
    
    json_to_csv(args.json_file, args.output, args.fields)

if __name__ == "__main__":
    main()