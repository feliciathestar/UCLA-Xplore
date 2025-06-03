import pandas as pd
import sys

def match_and_copy_event_ids(csv1_path, csv2_path, output_path=None):
    """
    Match events between two CSV files and copy event_id from csv1 to csv2
    
    Args:
        csv1_path: Path to CSV file with event_name, event_id, and date
        csv2_path: Path to CSV file with event_name and date (to be updated)
        output_path: Path for output file (optional, defaults to csv2_path)
    """
    try:
        # Read both CSV files
        csv1 = pd.read_csv(csv1_path)
        csv2 = pd.read_csv(csv2_path)
        
        # Ensure required columns exist
        required_cols_csv1 = ['event_name', 'event_id', 'date']
        required_cols_csv2 = ['event_name', 'date']
        
        for col in required_cols_csv1:
            if col not in csv1.columns:
                raise ValueError(f"Column '{col}' not found in {csv1_path}")
        
        for col in required_cols_csv2:
            if col not in csv2.columns:
                raise ValueError(f"Column '{col}' not found in {csv2_path}")
        
        # Convert date columns to datetime for proper comparison
        csv1['date'] = pd.to_datetime(csv1['date'])
        csv2['date'] = pd.to_datetime(csv2['date'])
        
        # Create event_id column in csv2 if it doesn't exist
        if 'event_id' not in csv2.columns:
            csv2['event_id'] = None
        
        # Create a lookup dictionary from csv1
        lookup_dict = {}
        for _, row in csv1.iterrows():
            key = (row['event_name'], row['date'])
            lookup_dict[key] = row['event_id']
        
        # Match and copy event_ids
        matches_found = 0
        for index, row in csv2.iterrows():
            key = (row['event_name'], row['date'])
            if key in lookup_dict:
                csv2.at[index, 'event_id'] = lookup_dict[key]
                matches_found += 1
        
        # Save the updated csv2
        output_file = output_path if output_path else csv2_path
        csv2.to_csv(output_file, index=False)
        
        print(f"Processing complete!")
        print(f"Total rows in CSV2: {len(csv2)}")
        print(f"Matches found and updated: {matches_found}")
        print(f"Updated file saved as: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python script.py <csv1_path> <csv2_path> [output_path]")
        print("Example: python script.py events_with_ids.csv events_to_update.csv")
        return
    
    csv1_path = sys.argv[1]
    csv2_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    match_and_copy_event_ids(csv1_path, csv2_path, output_path)

if __name__ == "__main__":
    main()