import requests, re, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# ---------------- CONFIG ---------------- #
PRIORITY_PATHS = [
    "", "about", "company", "products", "solutions",
    "industries", "pricing", "contact", "careers"
]

SOCIAL_DOMAINS = {
    "linkedin.com": "LinkedIn",
    "twitter.com": "Twitter",
    "x.com": "X",
    "instagram.com": "Instagram",
    "youtube.com": "YouTube"
}

PROOF_KEYWORDS = [
    "trusted by", "clients", "case study",
    "certified", "iso", "award", "testimonial"
]

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"\+?\d[\d\s\-]{7,}\d"

# ---------------- UTILS ---------------- #
def normalize_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")

def fetch_page(url):
    try:
        r = requests.get(url, timeout=10)
        return r.text, None
    except Exception as e:
        return None, str(e)

# ---------------- SCRAPER ---------------- #
def scrape_company(url):
    base_url = normalize_url(url)

    record = {
        "identity": {},
        "business_summary": {},
        "evidence": {},
        "contact": {},
        "team_hiring": {},
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "pages_visited": [],
            "errors": []
        }
    }

    all_text = ""
    social_links = {}
    proof_signals = set()
    emails, phones = set(), set()

    for path in PRIORITY_PATHS:
        page_url = base_url if path == "" else f"{base_url}/{path}"
        html, error = fetch_page(page_url)

        if error:
            record["metadata"]["errors"].append(f"{page_url}: {error}")
            continue

        soup = BeautifulSoup(html, "html.parser")
        record["metadata"]["pages_visited"].append(page_url)

        text = soup.get_text(" ", strip=True).lower()
        all_text += " " + text

        # Identity
        if not record["identity"].get("company_name"):
            record["identity"]["company_name"] = soup.title.text.strip() if soup.title else "not_found"
            record["identity"]["website_url"] = base_url

        # Tagline
        if not record["identity"].get("tagline"):
            meta = soup.find("meta", attrs={"name": "description"})
            record["identity"]["tagline"] = meta["content"] if meta else "not_found"

        # Emails / Phones
        emails.update(re.findall(EMAIL_REGEX, text))
        phones.update(re.findall(PHONE_REGEX, text))

        # Proof signals
        for kw in PROOF_KEYWORDS:
            if kw in text:
                proof_signals.add(kw)

        # Social links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            for domain, name in SOCIAL_DOMAINS.items():
                if domain in href and name not in social_links:
                    social_links[name] = href

    # Business summary (light interpretation + scraped text)
    record["business_summary"]["what_they_do"] = all_text[:400] if all_text else "not_found"
    record["business_summary"]["primary_offerings"] = "not_found"
    record["business_summary"]["target_segments"] = "not_found"

    # Evidence
    record["evidence"]["proof_signals_found"] = list(proof_signals) if proof_signals else "not_found"
    record["evidence"]["social_links"] = social_links if social_links else "not_found"

    # Contact
    record["contact"]["emails"] = list(emails) if emails else "not_found"
    record["contact"]["phones"] = list(phones) if phones else "not_found"
    record["contact"]["contact_page"] = f"{base_url}/contact"

    # Hiring
    record["team_hiring"]["careers_page"] = f"{base_url}/careers"

    return record

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    url = input("Enter company website URL: ")
    output = scrape_company(url)
    print(json.dumps(output, indent=2))
