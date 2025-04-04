import os
import sys
import csv

def clean_text_file(file_path):
    """
    Reads a text file, removes everything before 'Staff/Faculty/Administrators',
    strips only empty lines while preserving meaningful new lines,
    removes all 'Signatory' and 'Advisor' fields along with the lines immediately after them,
    removes footer information including UCLA contact details and social media links,
    extracts Name, Full Description, Category, Email, Website, and Social Media fields (Facebook, Instagram, Twitter, LinkedIn),
    and returns structured club data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.readlines()

    # Find the position of the target keyword
    keyword = "Staff/Faculty/Administrators"
    start_index = next((i for i, line in enumerate(content) if keyword in line), None)
    
    if start_index is not None:
        cleaned_content = content[start_index + 1:]
    else:
        cleaned_content = content  # If keyword not found, return original content

    # Remove empty lines
    cleaned_content = [line.strip() for line in cleaned_content if line.strip()]
    
    # Remove Signatory and Advisor fields along with the next line
    filtered_content = []
    skip_next = False
    for line in cleaned_content:
        if skip_next:
            skip_next = False
            continue
        if line.startswith("Signatory") or line.startswith("Advisor") or line.startswith("Contact"):
            skip_next = True  # Skip this line and the next one
        elif "UCLA Student Organizations, Leadership & Engagement" in line:
            break  # Stop processing at the start of footer details
        else:
            filtered_content.append(line)
    
    # Extract structured data for CSV
    clubs = []
    i = 0
    while i < len(filtered_content):
        name = filtered_content[i]
        description = filtered_content[i + 1] if i + 1 < len(filtered_content) else ""
        # category = filtered_content[i + 3] if i + 3 < len(filtered_content) else ""
        
        # Reset optional fields for each club
        category, email, website, facebook, instagram, twitter, youtube, linkedin ="", "", "", "", "", "", "", ""
        
        j = i + 2  # Start looking for optional fields after category
        max_lookup = min(j + 8, len(filtered_content))  # Limit how far to look ahead
        while j < max_lookup:
            line = filtered_content[j]
            if line.startswith("Category:") and j + 1 < len(filtered_content):
                category = filtered_content[j + 1].strip()
                j += 2
                print(f"Processing Category then jumping to {j}")
                continue
            if line.startswith("Email:") and j + 1 < len(filtered_content):
                email = filtered_content[j + 1].strip()
                j += 2
                print(f"Processing Email then jumping to {j}")
                continue
            elif line.startswith("Website:") and j + 1 < len(filtered_content):
                website = filtered_content[j + 1].strip()
                j += 2
                print(f"Processing Website then jumping to {j}")
                continue
            elif line.startswith("Social Media:") and j + 1 < len(filtered_content):
                line = filtered_content[j + 1]
                if "Facebook" in line and "[" in line and "](" in line:
                    facebook = line.split("[Facebook](", 1)[1].split(")")[0]
                if "Instagram" in line and "[" in line and "](" in line:
                    instagram = line.split("[Instagram](", 1)[1].split(")")[0]
                if "Twitter" in line and "[" in line and "](" in line:
                    twitter = line.split("[Twitter](", 1)[1].split(")")[0]
                if "YouTube" in line and "[" in line and "](" in line:
                    youtube = line.split("[YouTube](", 1)[1].split(")")[0]
                if "LinkedIn" in line and "[" in line and "](" in line:
                    linkedin = line.split("[LinkedIn](", 1)[1].split(")")[0]
                j += 2
                print(f"Processing Social Media then jumping to {j}")
                break
            else:
                break
        
        clubs.append([name, description, category, email, website, facebook, instagram, twitter, youtube, linkedin])
        
        # Move index to the next club entry
        i = j  # Move to the next club entry
        print(f"The value of j is: {j}")
    
    return clubs

def process_folder(folder_path, output_csv):
    """
    Reads all .txt files from a folder, extracts data, and appends to a single CSV file.
    """
    all_clubs = []

    # Iterate through all text files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # Process only .txt files
            file_path = os.path.join(folder_path, filename)
            print(f"Processing: {file_path}")
            clubs = clean_text_file(file_path)
            all_clubs.extend(clubs)

    # Save extracted data to one big CSV file
    with open(output_csv, "w", encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Full Description", "Category", "Email", "Website", "Facebook", "Instagram", "Twitter", "YouTube", "LinkedIn"])
        writer.writerows(all_clubs)
    
    print(f"Combined CSV file saved to: {output_csv}")

# Run from command line
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean_text_file.py <folder_path> <output_csv>")
    else:
        process_folder(sys.argv[1], sys.argv[2])
