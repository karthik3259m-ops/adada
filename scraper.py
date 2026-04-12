import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_SITES = {
    "TNPSC": "https://tnpsc.gov.in/english/AISO-questions.html",
    "UPSC": "https://www.upsc.gov.in/examinations/previous-question-papers",
    "Adda247": "https://www.adda247.com/exams/upsc/upsc-previous-year-question-papers/"
}

BASE_DIR = "Longinsent_Archive"
BATCH_LIMIT = 80  # Max files per run to avoid push failures

def organize_file(filename, source_folder):
    year_match = re.search(r'20[0-2][0-9]', filename)
    year = year_match.group(0) if year_match else "Unknown_Year"
    
    fn_upper = filename.upper()
    if any(x in fn_upper for x in ["G4", "GROUP_IV", "GROUP-IV"]):
        exam_type = "Group_4"
    elif any(x in fn_upper for x in ["G2", "GROUP_II", "GROUP-II"]):
        exam_type = "Group_2"
    else:
        exam_type = "Mains" if "MAIN" in fn_upper else "Prelims"

    target_path = os.path.join(BASE_DIR, source_folder, year, exam_type)
    os.makedirs(target_path, exist_ok=True)
    return target_path

def download_and_organize():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    download_count = 0
    
    for folder_name, url in TARGET_SITES.items():
        if download_count >= BATCH_LIMIT:
            break
            
        print(f"--- Scraping {folder_name} ---")
        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                if download_count >= BATCH_LIMIT:
                    print("Batch limit reached. Stopping for this run.")
                    return # Exit function to trigger commit

                href = link['href']
                if href.lower().endswith('.pdf'):
                    pdf_url = urljoin(url, href)
                    original_name = pdf_url.split('/')[-1].split('?')[0]
                    
                    target_dir = organize_file(original_name, folder_name)
                    final_path = os.path.join(target_dir, original_name)

                    if not os.path.exists(final_path):
                        print(f"[{download_count+1}/{BATCH_LIMIT}] Downloading: {original_name}")
                        r = requests.get(pdf_url, stream=True, verify=False)
                        with open(final_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                        download_count += 1
                        
        except Exception as e:
            print(f"Error processing {folder_name}: {e}")

if __name__ == "__main__":
    download_and_organize()
