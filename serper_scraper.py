import requests
import csv
from datetime import datetime
import re
import os
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse

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
    EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return re.findall(EMAIL_PATTERN, text)


def extract_contact_links_from_html(html, domain):
    """Return contact-related links found on a page."""
    soup = BeautifulSoup(html, "html.parser")
    contact_links = set()
    keywords = ["contact", "about", "advertis", "support", "impressum"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = requests.compat.urljoin(f"https://{domain}/", href)
        parsed = urlparse(full_url)
        link_domain = parsed.netloc.lower()
        if link_domain == domain or link_domain.endswith("." + domain):
            if any(k in href.lower() for k in keywords):
                contact_links.add(full_url)
    return list(contact_links)


def has_contact_form(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("form") is not None

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
for domain, homepage in domain_urls:  # обрабатываем все найденные домены
    print(f"Проверяю домен: {domain} — {homepage}")

    homepage_html = try_get(homepage)
    if homepage_html:
        emails = find_emails(homepage_html)
        contacts = extract_contact_links_from_html(homepage_html, domain)
    else:
        emails = []
        contacts = []

    # Запись по главной странице
    records.append([now, domain, homepage, ", ".join(emails), ""])

    for c_link in contacts:
        c_html = try_get(c_link)
        c_emails = find_emails(c_html) if c_html else []
        form_found_flag = "True" if c_html and has_contact_form(c_html) else "False"
        records.append([
            now,
            domain,
            c_link,
            ", ".join(c_emails),
            form_found_flag,
        ])

with open("result.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "domain", "page", "emails", "form_found"])
    for row in records:
        writer.writerow(row) 
