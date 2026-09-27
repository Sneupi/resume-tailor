import argparse
from playwright.sync_api import sync_playwright
import io
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

# Parse Args From CLI
parser = argparse.ArgumentParser(description="A sample script demonstrating argparse.")
parser.add_argument("resume", help="Path to resume file (plaintext preferred).")
parser.add_argument("job", help="URL to job listing webpage (permalink preferred).")
args = parser.parse_args()

# Validate Local Resume File
assert os.path.isfile(args.resume), f"File \"{args.resume}\" not exists."
assert os.access(args.resume, os.R_OK), f"File \"{args.resume}\" not accessible."

# Scrape Job Listing From URL
job_filename = "extracted_job.txt"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # Check Page Availability
    try:
        page.goto(args.job)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(-1)

    # Await Full Page Load (e.g. Network-Received Data, SPA Client Updates)
    page.wait_for_timeout(2000)
    
    # Translate Page For LLM
    page_content = page.inner_text('body')
    with open(job_filename, "+w") as f:
        f.write(page_content)
    
    browser.close()

# Initialize LLM
API_KEY = os.getenv("GOOGLE_API_KEY")
API_MODEL = os.getenv("GOOGLE_API_MODEL")
client = genai.Client(api_key=API_KEY)

# Prompt LLM 
chat = client.chats.create(model=API_MODEL)
resume_file = client.files.upload(file=args.resume)
job_file = client.files.upload(file=job_filename)
response = chat.send_message(
    message=[
        resume_file,
        job_file,
        f"Given the provided resume file, as well as the job description file, generate a tailored resume file in the same format, matching my closest bullets to the company language, keywords and skills present in the job description. Do not fabricate experiences not listed in the original resume. Do not generate anything else besides the new resume body."
    ]
)

# Handle LLM Response
with open(f"tailored-{args.resume}", "+w") as f:
    f.write(response.text)