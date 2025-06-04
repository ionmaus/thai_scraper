#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import csv
from datetime import datetime

# Шаблон для поиска e-mail
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def fetch_google_page(query, start_index):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&start={start_index}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return ""
    except requests.RequestException:
        return ""


def extract_links_from_google_html(html):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/url?q="):
            real_url = href.split("/url?q=")[1].split("&")[0]
            urls.append(real_url)
    return urls


def get_domain_from_url(full_url):
    parsed = urlparse(full_url)
    domain = parsed.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def extract_emails_from_html(html):
    emails = set()
    soup = BeautifulSoup(html, "html.parser")
    # Ищем все mailto:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            email = href.split("mailto:")[1]
            emails.add(email)
    # Ищем все вхождения вида user@domain.com
    found = re.findall(EMAIL_PATTERN, html)
    for email in found:
        emails.add(email)
    return list(emails)

def extract_contact_links_from_html(html, domain):
    soup = BeautifulSoup(html, "html.parser")
    contact_links = set()
    keywords = ["contact", "about", "advertis", "support", "impressum"]
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(k in href for k in keywords):
            full_url = requests.compat.urljoin(f"https://{domain}/", a["href"])
            contact_links.add(full_url)
    return list(contact_links)

def main():
    query = "thai dishes recipies"
    all_links = []
    for start in range(0, 50, 10):
        html = fetch_google_page(query, start)
        if html:
            links = extract_links_from_google_html(html)
            all_links.extend(links)

    all_domains = [get_domain_from_url(link) for link in all_links]
    unique_domains = list(set(all_domains))

    print("Первый список доменов:")
    for d in unique_domains[:10]:
        print(d)


if __name__ == "__main__":
    main() 