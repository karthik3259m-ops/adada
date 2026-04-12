import os
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The hub for all previous year papers
START_URL = "https://www.adda247.com/jobs/previous-year-question-papers/"
BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 80 

def download_batch():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Referer': 'https://www.adda247.com/'
    }
    
    download_count = 0
    os.makedirs(BASE_DIR, exist_ok=True)
    visited_pages = set()

    print(f"--- Crawling Hub: {START_URL} ---")
    try:
        response = requests.get(START_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all article/job links on the hub page
        job_links = [urljoin(START_URL, a['href']) for a in soup.find_all('a', href=True) 
                     if "/jobs/" in a['href'] or "/exams/" in a['href']]
        
        # Remove duplicates
        job_links = list(set(job_links))
        print(f"Found {len(job_links)} potential sub-pages. Starting deep scan...")

        for sub_url in job_links:
            if download_count >= BATCH_LIMIT:
                break
            if sub_url in visited_pages:
                continue

            print(f"Scanning sub-page: {sub_url}")
            try:
                sub_res = requests.get(sub_url, headers=headers, timeout=20)
                visited_pages.add(sub_url)
                sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
                
                # Look for PDF links on the sub-page
                for link in sub_soup.find_all('a', href=True):
                    href = link['href'].split('?')[0]
                    if href.lower().endswith('.pdf'):
                        pdf_url = urljoin(sub_url, href)
                        
                        # Clean filename and organize
                        file_name = pdf_url.split('/')[-1]
                        # Create a folder based on the job type (from the sub_url slug)
                        folder_name = sub_url.split('/')[-2] if sub_url.endswith('/') else sub_url.split('/')[-1]
                        save_path = os.path.join(BASE_DIR, folder_name)
                        os.makedirs(save_path, exist_ok=True)
                        
                        final_file = os.path.join(save_path, file_name)

                        if not os.path.exists(final_file):
                            print(f"[{download_count+1}/{BATCH_LIMIT}] Downloading: {file_name}")
                            r = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
                            if r.status_code == 200:
                                with open(final_file, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                download_count += 1
                                if download_count >= BATCH_LIMIT:
                                    return
            except Exception as e:
                print(f"Skipping page {sub_url} due to error.")
                continue

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    download_batch()
