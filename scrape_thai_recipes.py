#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import csv
from datetime import datetime
import tldextract  # нужно установить через pip install tldextract

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
            candidate = href.split("mailto:")[1]
            # Отфильтровываем названия файлов по расширению
            if not candidate.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".svg")):
                # Проверяем, что домен валидный
                ext = tldextract.extract(candidate)
                if ext.suffix:
                    emails.add(candidate)
    # Ищем через регулярку, но фильтруем по TLD
    found = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)
    for candidate in found:
        # Отсекаем файлы по расширению
        if candidate.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".svg")):
            continue
        ext = tldextract.extract(candidate)
        if ext.suffix:  # есть TLD, значит это настоящий e-mail
            emails.add(candidate)
    return list(emails)

def extract_contact_links_from_html(html, domain):
    soup = BeautifulSoup(html, "html.parser")
    contact_links = set()
    keywords = ["contact", "about", "advertis", "support", "impressum"]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Строим абсолютный URL
        full_url = requests.compat.urljoin(f"https://{domain}/", href)
        # Парсим домен ссылки
        parsed = urlparse(full_url)
        link_domain = parsed.netloc.lower()
        # Проверяем, что ссылка ведёт на тот же домен или поддомен
        if link_domain == domain or link_domain.endswith("." + domain):
            href_lower = href.lower()
            if any(k in href_lower for k in keywords):
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

    # Извлечь уникальные домены, отфильтровать пустые
    all_domains = [get_domain_from_url(link) for link in all_links]
    unique_domains = list({d for d in all_domains if d})

    print("Обработка доменов:")
    records = []  # каждая запись: (domain, page_url, emails_list, contact_links_list)

    for domain in unique_domains:
        print(f"  → {domain}")
        homepage_html = ""
        try:
            r = requests.get(f"https://{domain}/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code == 200:
                homepage_html = r.text
        except Exception:
            homepage_html = ""

        if homepage_html:
            # 1) Ищем e-mail на главной
            emails_main = extract_emails_from_html(homepage_html)
        else:
            emails_main = []

        # 2) Ищем contact-ссылки на главной
        if homepage_html:
            contacts = extract_contact_links_from_html(homepage_html, domain)
        else:
            contacts = []
        # Фильтруем только корректные ссылки, уже внутри функции
        valid_contacts = contacts

        # 3) Записываем результаты для главной (даже если e-mail пустые)
        records.append((domain, f"https://{domain}/", emails_main, valid_contacts))

        # 4) Для каждой contact-ссылки заходим и ищем e-mail
        for clink in valid_contacts:
            try:
                rc = requests.get(clink, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if rc.status_code == 200:
                    cl_html = rc.text
                    emails_contact = extract_emails_from_html(cl_html)
                else:
                    emails_contact = []
            except Exception:
                emails_contact = []
            # Записываем запись для contact-страницы
            records.append((domain, clink, emails_contact, valid_contacts))

    # Записываем всё в result.csv
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("result.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "domain", "page", "emails", "contact_links"])
        for domain, page_url, emails_list, contacts_list in records:
            emails_str = ",".join(emails_list)
            contacts_str = ",".join(contacts_list)
            writer.writerow([current_time, domain, page_url, emails_str, contacts_str])

    print("\nСохранили результат в result.csv, строк:", len(records))

if __name__ == "__main__":
    main() 