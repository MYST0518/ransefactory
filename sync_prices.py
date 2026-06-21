#!/usr/bin/env python3
import os
import sys
import csv
import hashlib
import urllib.request
import subprocess

# Configurations
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1MSCnS4pY8Hf55N4xT05ok0CltxTHS2whB7hWNehnhlE/export?format=csv"
HTML_FILE_PATH = "index.html"
HASH_FILE_PATH = "price_data_hash.txt"

START_MARKER = "<!-- PRICE_TABLE_ROWS_START -->"
END_MARKER = "<!-- PRICE_TABLE_ROWS_END -->"

def fetch_csv_data(url):
    print(f"Fetching CSV data from Google Sheets...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            content_bytes = response.read()
            return content_bytes
    except Exception as e:
        print(f"Error fetching CSV: {e}", file=sys.stderr)
        sys.exit(1)

def normalize_and_hash(content_bytes):
    # Decode as UTF-8 (with BOM if present)
    content_str = content_bytes.decode("utf-8-sig")
    
    # Read rows and filter out completely empty ones
    lines = content_str.strip().splitlines()
    reader = csv.reader(lines)
    
    normalized_rows = []
    for row in reader:
        # Strip each cell, ignore empty rows
        cleaned_row = [cell.strip() for cell in row]
        if any(cleaned_row):
            normalized_rows.append(cleaned_row)
            
    # Serialize to standard CSV string for consistent hashing
    serialized = ""
    for r in normalized_rows:
        serialized += ",".join(r) + "\n"
        
    # Calculate SHA-256
    hasher = hashlib.sha256()
    hasher.update(serialized.encode("utf-8"))
    data_hash = hasher.hexdigest()
    
    return normalized_rows, data_hash

def generate_rows_html(rows):
    if len(rows) <= 1:
        # If only header or empty
        return "          <div class=\"price-row\">\n            <div class=\"col-date\">-</div>\n            <div class=\"col-item\">現在、参考価格情報はございません。</div>\n            <div class=\"col-price\">-</div>\n          </div>\n"
        
    # First row is header: 日付け, 買取品, 価格 (or similar)
    header = rows[0]
    data_rows = rows[1:]
    
    html_lines = []
    for idx, row in enumerate(data_rows):
        # Handle cases where row might not have 3 columns
        date_val = row[0] if len(row) > 0 else ""
        item_val = row[1] if len(row) > 1 else ""
        price_val = row[2] if len(row) > 2 else ""
        
        # Skip if all are empty
        if not date_val and not item_val and not price_val:
            continue
            
        # 5 items or more (0-indexed so 5th data item is index 4 and beyond) -> collapse
        hidden_class = " hidden-row" if idx >= 5 else ""
        
        row_html = (
            f"          <div class=\"price-row{hidden_class}\">\n"
            f"            <div class=\"col-date\">{date_val}</div>\n"
            f"            <div class=\"col-item\">{item_val}</div>\n"
            f"            <div class=\"col-price\">{price_val}</div>\n"
            f"          </div>"
        )
        html_lines.append(row_html)
        
    return "\n".join(html_lines) + "\n"

def update_html_file(file_path, new_rows_html):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!", file=sys.stderr)
        sys.exit(1)
        
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    start_idx = html_content.find(START_MARKER)
    end_idx = html_content.find(END_MARKER)
    
    if start_idx == -1 or end_idx == -1:
        print(f"Error: Markers not found in {file_path}!", file=sys.stderr)
        sys.exit(1)
        
    # Replace content between markers
    before_part = html_content[:start_idx + len(START_MARKER)]
    after_part = html_content[end_idx:]
    
    # Add a newline after the start marker, then the indented html, then the end marker
    updated_content = before_part + "\n" + new_rows_html + "          " + after_part
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print(f"Updated {file_path} successfully with latest price rows.")

def main():
    force_update = "--force" in sys.argv
    
    # 1. Fetch
    csv_bytes = fetch_csv_data(SHEET_CSV_URL)
    
    # 2. Parse & Hash
    rows, current_hash = normalize_and_hash(csv_bytes)
    
    # 3. Check for previous hash
    prev_hash = ""
    if os.path.exists(HASH_FILE_PATH):
        with open(HASH_FILE_PATH, "r", encoding="utf-8") as f:
            prev_hash = f.read().strip()
            
    print(f"Current Hash:  {current_hash}")
    print(f"Previous Hash: {prev_hash if prev_hash else 'None'}")
    
    if prev_hash == current_hash and not force_update:
        print("SEO Rule: No data changes detected in the Google Sheet. Skipping build and deploy to avoid search engine freshness spam penalty.")
        sys.exit(0)
        
    # 4. Generate HTML & Update File
    rows_html = generate_rows_html(rows)
    update_html_file(HTML_FILE_PATH, rows_html)
    
    # 5. Save new hash
    with open(HASH_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(current_hash)
    print(f"Saved new hash to {HASH_FILE_PATH}")
    
    # 6. Deploy changes
    if os.path.exists("deploy.py"):
        print("Running deploy.py...")
        result = subprocess.run([sys.executable, "deploy.py", "-y"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print("Deployment failed!", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        else:
            print("Deployment completed successfully.")
    else:
        print("Warning: deploy.py not found in the current directory. Skipping auto-deployment.")

if __name__ == "__main__":
    main()
