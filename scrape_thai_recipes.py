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
    # Basic-HTML (mobile) выдача: gbv=1
    url = (
        "https://www.google.com/search"
        f"?q={query.replace(' ', '+')}"
        f"&start={start_index}"
        "&num=10"        # 10 результатов
        "&hl=en&gl=us"   # английский, регион US
        "&pws=0"         # без персонализации
        "&gbv=1"         # ← основное: мобильный / базовый HTML
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.text if r.status_code == 200 else ""
    except requests.RequestException:
        return ""


def extract_links_from_google_html(html):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # в mobile-версии прямые URL уже в href
        if href.startswith("http") and "google." not in href:
            urls.append(href)
    # убираем дубликаты, сохраняя порядок
    return list(dict.fromkeys(urls))


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

def has_contact_form(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("form") is not None

def main():
    # Используем оригинальную фразу с опечаткой (если нужно), либо можно вернуть "recipes":
    query = "thai dishes recipes"

    # 1) Собираем «сырые» HTML-ответы от Google (5 страниц)
    all_html = []
    for start in range(0, 50, 10):
        html = fetch_google_page(query, start)
        print(f"DEBUG: start={start}, len={len(html) if html else 0}")
        # Сохраняем всё, что пришло (даже если это заглушка)
        with open(f"debug_page_{start}.html", "w", encoding="utf-8") as f:
            f.write(html if html else "")
        if html:
                all_html.append(html)

    # <<< Выводим, сколько действительно непустых HTML-ответов получили
    print(f"Получили {len(all_html)} непустых HTML-ответов от Google")

    # Если нет ни одного непустого ответа — выходим
    if not all_html:
        print("‼️ Ничего не получено от Google. Проверьте запрос или связь.")
        return

    # 2) Из каждого HTML вытаскиваем «сырые» ссылки
    all_links = []
    for html in all_html:
        links = extract_links_from_google_html(html)
        # <<< Отладочная строка: сколько ссылок нашли в этой HTML-странице
        print(f"DEBUG: найдено {len(links)} ссылок на этой странице")
        # <<< Если есть какие-то ссылки, показываем первые до 5
        for link in links[:5]:
            print("    ->", link)
        all_links.extend(links)

    print(f"Извлечено всего {len(all_links)} «сырых» ссылок из Google-страниц")

    # 3) Преобразуем «сырые» ссылки в уникальные домены
    all_domains = [get_domain_from_url(link) for link in all_links]
    unique_domains = list({d for d in all_domains if d})
    print(f"Уникальных доменов после фильтрации: {len(unique_domains)}")

    # Если уникальных доменов нет — информируем и выходим
    if not unique_domains:
        print("‼️ Не удалось получить ни одного домена. Проверьте логику extract_links_from_google_html.")
        return

    # Если домены есть, выводим первые 10 для проверки
    print("Первый список доменов:")
    for d in unique_domains[:10]:
        print(" ", d)

    # Далее идёт основная логика обхода доменов и запись в CSV...
    records = []

    print("\nОбходим все домены для поиска e-mail и contact-ссылок:")
    for domain in unique_domains:
        print(f"  → Обрабатываем домен: {domain}")
        homepage_html = ""
        try:
            r = requests.get(f"https://{domain}/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code == 200:
                homepage_html = r.text
        except Exception:
            homepage_html = ""

        if homepage_html:
            emails_main = extract_emails_from_html(homepage_html)
            valid_contacts = [
                u for u in extract_contact_links_from_html(homepage_html, domain)
                if u.startswith("http")
            ]
        else:
            emails_main = []
            valid_contacts = []

        # Добавляем запись для главной страницы
        records.append((domain, f"https://{domain}/", emails_main, valid_contacts))

        # Для каждой найденной contact-ссылки заходим на неё и ищем e-mail
        for clink in valid_contacts:
            cl_html = ""
            try:
                rc = requests.get(clink, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if rc.status_code == 200:
                    cl_html = rc.text
            except Exception:
                cl_html = ""

            if cl_html:
                emails_contact = extract_emails_from_html(cl_html)
            else:
                emails_contact = []
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

    print(f"\nСохранили результат в result.csv, строк: {len(records)}")

if __name__ == "__main__":
    main() 
