import pandas as pd

def clean_event_ids(csv_file_path, output_file_path=None):
    """
    Remove '.0' from event_id column entries
    
    Args:
        csv_file_path: Path to the input CSV file
        output_file_path: Path for the cleaned output file (optional)
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Check if event_id column exists
        if 'event_id' not in df.columns:
            print("Error: 'event_id' column not found in the CSV file")
            return False
        
        # Convert event_id to string and remove '.0' suffix
        df['event_id'] = df['event_id'].astype(str).str.replace('.0', '', regex=False)
        
        # Set output file path
        if output_file_path is None:
            output_file_path = csv_file_path
        
        # Save the cleaned CSV
        df.to_csv(output_file_path, index=False)
        
        print(f"Successfully cleaned event_id column!")
        print(f"File saved as: {output_file_path}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    # Update this path to your CSV file
    csv_file_path = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/scripts/milvus/2025_spring_events.csv"
    
    # Optional: specify a different output file path
    # output_file_path = "/path/to/cleaned_file.csv"
    
    clean_event_ids(csv_file_path)

if __name__ == "__main__":
    main()