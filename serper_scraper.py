import requests
import csv
from datetime import datetime
import re
import os
import sys

# API key for Serper (set SERPER_API_KEY environment variable)
API_KEY = os.getenv("SERPER_API_KEY")
if not API_KEY:
    print("SERPER_API_KEY environment variable not set. Please set it before running the script.")
    sys.exit(1)
QUERY = "thai dishes recipes"

headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
data = {"q": QUERY, "num": 50}  # 5 страниц по 10 результатов

response = requests.post("https://google.serper.dev/search", headers=headers, json=data)
print("Serper status:", response.status_code)
results = response.json()
print("Serper results:", results)

def extract_domain(url):
    try:
        return url.split("/")[2]
    except Exception:
        return ""

domains = []
domain_urls = []
for r in results.get("organic", []):
    url = r.get("link", "")
    domain = extract_domain(url)
    if domain and domain not in domains:
        domains.append(domain)
        domain_urls.append((domain, url))

print("Всего результатов в organic:", len(results.get("organic", [])))

def find_emails(text):
    EMAIL_PATTERN = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    return re.findall(EMAIL_PATTERN, text)

def try_get(url):
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.ok:
            return resp.text
    except Exception:
        return ""
    return ""

records = []
now = datetime.now().strftime("%Y-%m-%d %H:%M")
for domain, homepage in domain_urls[:5]:  # только первые 5 сайтов
    print(f"Проверяю домен: {domain} — {homepage}")
    emails = []
    contacts = []
    form_found = ""

    html = try_get(homepage)
    if html:
        emails = find_emails(html)
        links = re.findall(r'href="([^"]+)"', html)
        contact_links = [
            l for l in links if any(s in l.lower() for s in ["contact", "about", "advert"])
        ]
        contact_links = [
            l if l.startswith("http") else f"https://{domain}/{l.lstrip('/')}"
            for l in contact_links
        ]
        contacts = list(set(contact_links))
        for c_link in contacts:
            c_html = try_get(c_link)
            c_emails = find_emails(c_html)
            if c_emails:
                if "<form" in c_html:
                    form_found = "True"
                records.append([
                    now, domain, c_link, ", ".join(c_emails), form_found
                ])
        # Запись по главной
        records.append([
            now, domain, homepage, ", ".join(emails), ""
        ])

with open("result.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "domain", "page", "emails", "form_found"])
    for row in records:
        writer.writerow(row) 
