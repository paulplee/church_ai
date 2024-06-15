import os
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger
import pdfplumber

# Step 1: Go to the URL and get the page content
url = "https://www.vatican.va/chinese/ccc_zh.htm"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Step 2: Find all the PDF links and download them
pdf_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]
pdf_files = []
for link in pdf_links:
    pdf_url = "https://www.vatican.va/chinese/" + link
    try:
        pdf_response = requests.get(pdf_url)
        pdf_name = link.split('/')[-1]
        pdf_files.append(pdf_name)
        with open(pdf_name, 'wb') as f:
            f.write(pdf_response.content)
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {pdf_url}. Error: {e}")

# Step 3: Merge all the PDF files into one
merger = PdfMerger()
for pdf_file in sorted(pdf_files):
    merger.append(pdf_file)
merger.write("catechism_zh.pdf")
merger.close()

# Step 4: Convert the merged PDF to a Markdown file
with pdfplumber.open("catechism_zh.pdf") as pdf:
    text = "\n".join(page.extract_text() for page in pdf.pages)
with open("catechism_zh.txt", 'w') as f:
    f.write(text)

# Clean up the individual PDF files
for pdf_file in pdf_files:
    os.remove(pdf_file)