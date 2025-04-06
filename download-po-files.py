"""Download latest POT and PO files of a given language from TranslationProject.org"""

import os
import re
import urllib3
import argparse
from bs4 import BeautifulSoup

http = urllib3.PoolManager()


def fetch_domains_and_versions():
    url = "https://translationproject.org/domain/index.html"
    response = http.request("GET", url)

    if response.status != 200:
        raise RuntimeError(f"Error accessing {url}: {response.status}")

    soup = BeautifulSoup(response.data, "html.parser")
    table = soup.find("table")

    if not table:
        raise RuntimeError("Table not found on the page.")

    domains = []
    for row in table.find_all("tr")[1:]:  # Skip header
        columns = row.find_all("td")
        if len(columns) >= 2:
            name = columns[0].text.strip()
            version = columns[1].text.strip()
            if name and version:
                domains.append((name, version))
    return domains


def download_po_files(domains, target_dir, language="pt_BR", quiet=False):
    base_po_url = "https://translationproject.org/latest/"
    for domain, _ in domains:
        po_url = f"{base_po_url}{domain}/{language}.po"
        po_path = os.path.join(target_dir, domain, f"{language}.po")

        try:
            response = http.request("GET", po_url)
            if response.status == 200:
                os.makedirs(os.path.dirname(po_path), exist_ok=True)
                with open(po_path, "wb") as f:
                    f.write(response.data)
                if not quiet:
                    print(f"Downloaded: {po_url} → {po_path}")
            elif not quiet:
                print(f"Not found: {po_url} (status {response.status}). Translation not started?")
        except Exception as e:
            print(f"Error downloading {po_url}: {e}")


def download_latest_pots(domains, target_dir, quiet=False):
    base_potfiles_url = "https://translationproject.org/POT-files/"
    for domain, version in domains:
        filename = f"{domain}-{version}.pot"
        url = f"{base_potfiles_url}{filename}"
        destination_path = os.path.join(target_dir, domain, f"{domain}.pot")

        try:
            response = http.request("GET", url)
            if response.status == 200:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                with open(destination_path, "wb") as f:
                    f.write(response.data)
                if not quiet:
                    print(f"Downloaded: {url} → {destination_path}")
            elif not quiet:
                print(f"Not found: {url} (status {response.status})")
        except Exception as e:
            print(f"Error downloading {url}: {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-l", "--language", default="pt_BR", help="Language code for the PO files (default: pt_BR)")
    parser.add_argument("-d", "--target-directory", default=".", help="Target directory to save files (default: current directory)")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress most output messages")

    args = parser.parse_args()

    if not os.path.isdir(args.target_directory):
        raise SystemExit(f"Error: directory '{args.target_directory}' does not exist or is not a directory.")
    if not os.path.isdir(os.path.join(args.target_directory, ".git")):
        raise SystemExit(f"Error: '{args.target_directory}' does not appear to be a Git repository root ('.git/' not found).")

    domains = fetch_domains_and_versions()
    download_po_files(domains, args.target_directory, language=args.language, quiet=args.quiet)
    download_latest_pots(domains, args.target_directory, quiet=args.quiet)


if __name__ == "__main__":
    main()

