#!/usr/bin/env python3
import os
import sys
import csv
import hashlib
import urllib.request
import urllib.parse
import subprocess

# Configurations
# Fetch specific sheet "コラム" via gviz API which is more human-readable than gid numbers
SHEET_NAME = "コラム"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/1MSCnS4pY8Hf55N4xT05ok0CltxTHS2whB7hWNehnhlE/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(SHEET_NAME)}"

HTML_FILE_PATH = "blog.html"
TEMPLATE_FILE_PATH = "blog_detail_template.html"
HASH_FILE_PATH = "blog_data_hash.txt"

START_MARKER = "<!-- BLOG_LIST_START -->"
END_MARKER = "<!-- BLOG_LIST_END -->"

def fetch_csv_data(url):
    print(f"Fetching CSV data for blog from sheet '{SHEET_NAME}'...")
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
    content_str = content_bytes.decode("utf-8-sig")
    lines = content_str.strip().splitlines()
    reader = csv.reader(lines)
    
    normalized_rows = []
    for row in reader:
        cleaned_row = [cell.strip() for cell in row]
        if any(cleaned_row):
            normalized_rows.append(cleaned_row)
            
    # Serialize to standard CSV string for consistent hashing
    serialized = ""
    for r in normalized_rows:
        serialized += ",".join(r) + "\n"
        
    hasher = hashlib.sha256()
    hasher.update(serialized.encode("utf-8"))
    data_hash = hasher.hexdigest()
    
    return normalized_rows, data_hash

def format_body_content(body_text):
    # If the user has already included HTML tags like <p>, <h3>, <br>, just return it.
    if "<p>" in body_text or "<br>" in body_text or "<h3>" in body_text:
        return body_text
        
    # Otherwise, split by lines and wrap non-empty lines in <p> tags
    # and handle double newlines as paragraph breaks.
    paragraphs = body_text.strip().split("\n\n")
    formatted_html = []
    for p in paragraphs:
        if not p.strip():
            continue
        # Within paragraph, convert single newlines to <br>
        p_content = p.replace("\n", "<br>\n")
        formatted_html.append(f"        <p>{p_content}</p>")
        
    return "\n".join(formatted_html)

def generate_blog_list_html(posts):
    if not posts:
        return "        <p>現在、コラム記事はございません。</p>\n"
        
    html_lines = []
    for post in posts:
        post_id = post["id"]
        date_val = post["date"]
        tag_val = post["tag"]
        title_val = post["title"]
        excerpt_val = post["excerpt"]
        
        item_html = (
            f"        <article class=\"blog-item\">\n"
            f"          <span class=\"blog-date\">{date_val}</span>\n"
            f"          <span class=\"blog-tag\">{tag_val}</span>\n"
            f"          <h3 class=\"blog-item-title\"><a href=\"blog_detail_{post_id}.html\">{title_val}</a></h3>\n"
            f"          <p class=\"blog-excerpt\">{excerpt_val}</p>\n"
            f"          <a href=\"blog_detail_{post_id}.html\" class=\"blog-more-link\">READ MORE ➔</a>\n"
            f"        </article>"
        )
        html_lines.append(item_html)
        
    return "\n\n".join(html_lines) + "\n"

def generate_detail_pages(posts, template_path):
    if not os.path.exists(template_path):
        print(f"Error: Template {template_path} not found!", file=sys.stderr)
        sys.exit(1)
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    for post in posts:
        post_id = post["id"]
        detail_filename = f"blog_detail_{post_id}.html"
        
        # Format body content nicely (convert line breaks to paragraph tags)
        formatted_content = format_body_content(post["content"])
        
        # Hydrate template
        page_html = template_content
        page_html = page_html.replace("{{TITLE}}", post["title"])
        page_html = page_html.replace("{{EXCERPT}}", post["excerpt"])
        page_html = page_html.replace("{{DATE}}", post["date"])
        page_html = page_html.replace("{{TAG}}", post["tag"])
        page_html = page_html.replace("{{CONTENT}}", formatted_content)
        
        with open(detail_filename, "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"Generated detail page: {detail_filename}")

def update_blog_list_html(file_path, new_list_html):
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
        
    before_part = html_content[:start_idx + len(START_MARKER)]
    after_part = html_content[end_idx:]
    
    updated_content = before_part + "\n\n" + new_list_html + "\n        " + after_part
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print(f"Updated {file_path} successfully with latest blog list.")

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
        print("No changes detected in Google Sheet. Skipping blog generation to avoid redundant deployments.")
        sys.exit(0)
        
    # Parse posts from rows (skip header row)
    # Target columns layout: ID, 日付, カテゴリ, タイトル, 抜粋, 本文
    if len(rows) <= 1:
        print("No blog posts found in CSV.")
        posts = []
    else:
        posts = []
        data_rows = rows[1:]
        for r in data_rows:
            if len(r) < 6:
                continue
            post_id = r[0].strip()
            # Skip rows without numeric ID
            if not post_id.isdigit():
                continue
                
            posts.append({
                "id": int(post_id),
                "date": r[1].strip(),
                "tag": r[2].strip(),
                "title": r[3].strip(),
                "excerpt": r[4].strip(),
                "content": r[5].strip()
            })
            
        # Sort posts by ID in descending order (newest first)
        posts.sort(key=lambda x: x["id"], reverse=True)
        
    # 4. Generate individual detail pages
    generate_detail_pages(posts, TEMPLATE_FILE_PATH)
    
    # 5. Generate blog list HTML & Update blog.html
    blog_list_html = generate_blog_list_html(posts)
    update_blog_list_html(HTML_FILE_PATH, blog_list_html)
    
    # 6. Save new hash
    with open(HASH_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(current_hash)
    print(f"Saved new hash to {HASH_FILE_PATH}")
    
    # 7. Deploy changes
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
        print("Warning: deploy.py not found. Skipping auto-deployment.")

if __name__ == "__main__":
    main()
