import os
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The primary hub
START_URL = "https://www.adda247.com/jobs/previous-year-question-papers/"
BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 80 

def download_batch():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    download_count = 0
    os.makedirs(BASE_DIR, exist_ok=True)
    visited_pages = set()

    print(f"--- Aggressive Crawl Started: {START_URL} ---")
    try:
        response = requests.get(START_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for all links in the main content body
        # Adda247 often puts these in a specific 'entry-content' div
        content_div = soup.find('div', class_='entry-content')
        search_area = content_div if content_div else soup
        
        raw_links = search_area.find_all('a', href=True)
        job_links = []
        
        for a in raw_links:
            href = a['href']
            full_url = urljoin(START_URL, href)
            # Filter: must be internal to adda247 and not the start page itself
            if "adda247.com" in full_url and full_url != START_URL and "#" not in href:
                job_links.append(full_url)
        
        # Unique links only
        job_links = list(set(job_links))
        print(f"Detected {len(job_links)} potential exam pages. Starting scan...")

        for sub_url in job_links:
            if download_count >= BATCH_LIMIT:
                print("Batch limit reached.")
                return
            
            if sub_url in visited_pages:
                continue

            print(f"Opening: {sub_url}")
            try:
                sub_res = requests.get(sub_url, headers=headers, timeout=20)
                visited_pages.add(sub_url)
                sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                
                # Check for PDF links
                for link in sub_soup.find_all('a', href=True):
                    pdf_href = link['href'].split('?')[0]
                    if pdf_href.lower().endswith('.pdf'):
                        pdf_url = urljoin(sub_url, pdf_href)
                        
                        file_name = pdf_url.split('/')[-1]
                        # Use the sub-page slug as the folder name
                        folder_name = sub_url.rstrip('/').split('/')[-1]
                        save_path = os.path.join(BASE_DIR, folder_name)
                        os.makedirs(save_path, exist_ok=True)
                        
                        final_file = os.path.join(save_path, file_name)

                        if not os.path.exists(final_file):
                            print(f"[{download_count+1}] Saving: {file_name}")
                            r = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                            if r.status_code == 200:
                                with open(final_file, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                download_count += 1
                                if download_count >= BATCH_LIMIT:
                                    return
            except Exception as e:
                continue

    except Exception as e:
        print(f"Failed to load Hub: {e}")

if __name__ == "__main__":
    download_batch()
