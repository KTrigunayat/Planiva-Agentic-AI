def clean_links(input_file, output_file=None):
    """
    Read links from input file, remove duplicates while preserving order, and save to output file
    as a Python list of strings.
    If output_file is not provided, it will overwrite the input file.
    
    Args:
        input_file (str): Path to the input file containing links
        output_file (str, optional): Path to save the cleaned links. Defaults to None (overwrite input file).
    
    Returns:
        list: List of unique links
    """
    # If output file is not provided, use input file
    if output_file is None:
        output_file = input_file
    
    # Read all lines from the file
    with open(input_file, 'r', encoding='utf-8') as f:
        # Read lines and strip, ignoring empty lines
        lines = [line.strip().strip('"') for line in f.readlines() if line.strip()]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in lines:
        # Clean the link (remove any extra whitespace or quotes)
        clean_link = link.strip().strip('"')
        if clean_link and clean_link not in seen:
            seen.add(clean_link)
            unique_links.append(clean_link)
    
    # Save the unique links back to the output file as a Python list
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n')  # Start the list
        
        # Write each link, enclosed in quotes, followed by a comma and newline
        for i, link in enumerate(unique_links):
            # Check if it's the last element to avoid a trailing comma
            if i == len(unique_links) - 1:
                f.write(f'    "{link}"\n')
            else:
                f.write(f'    "{link}",\n')
        
        f.write(']\n')  # End the list
    
    print(f"Original links: {len(lines)}")
    print(f"Unique links: {len(unique_links)}")
    print(f"Removed {len(lines) - len(unique_links)} duplicate links")
    print(f"Cleaned links saved to: {output_file} (as a Python list)")
    
    return unique_links

if __name__ == "__main__":
    import os
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Create the full path to links.txt in the same directory
    input_file = os.path.join(script_dir, "links.txt")
    
    # This will process the file and print the results
    # NOTE: You must ensure 'links.txt' exists in the same directory for this to run!
    # For testing, you might need to create a dummy links.txt first.
    
    try:
        unique_links = clean_links(input_file)
        
        # If you want to see the first few unique links, uncomment the following:
        # print("\nFirst 5 unique links:")
        # for link in unique_links[:5]:
        #     print(link)
            
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        print("Please create a 'links.txt' file with links (one per line) in the script's directory and run again.")