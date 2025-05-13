import pandas as pd
import os
import glob

def merge_excel_files(directory_path, output_file):
    """
    Merge all Excel files in the specified directory into one CSV file
    Args:
        directory_path: Path to directory containing Excel files
        output_file: Name of output CSV file
    """
    # Get all Excel files in directory
    all_files = glob.glob(os.path.join(directory_path, "output_*.xlsx"))
    
    if not all_files:
        print("No Excel files found in the specified directory")
        return
    
    # Create empty list to store dataframes
    df_list = []
    
    # Read and append each Excel file
    for file in all_files:
        df = pd.read_excel(file)
        df_list.append(df)
        print(f"Processed: {file}")
    
    # Concatenate all dataframes
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # Write to CSV file
    combined_df.to_csv(output_file, index=False)
    print(f"All files merged successfully into {output_file}")


directory_path = "/Users/wanxinxiao/Desktop/UCLA-Xplore/data/raw/excel"
output_file = "2025spring_events.csv"  # Changed extension to .csv
merge_excel_files(directory_path, output_file)