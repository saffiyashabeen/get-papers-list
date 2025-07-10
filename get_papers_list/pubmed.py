import requests
from typing import List, Dict
from lxml import etree
import csv
import re

def fetch_papers(query: str, debug: bool = False) -> List[str]:
    """Fetch PubMed IDs based on search query."""
    if debug:
        print(f"[DEBUG] Fetching paper IDs for query: {query}")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 5,
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

def fetch_paper_details(paper_ids: List[str], debug: bool = False) -> List[Dict]:
    """Fetch detailed info for given PubMed paper IDs."""
    if debug:
        print(f"[DEBUG] Fetching paper details for IDs: {paper_ids}")
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    root = etree.fromstring(response.content)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        paper = {}

        # PubMed ID
        pmid_elem = article.find(".//PMID")
        paper["PubmedID"] = pmid_elem.text if pmid_elem is not None else ""

        # Title
        title_elem = article.find(".//ArticleTitle")
        paper["Title"] = title_elem.text if title_elem is not None else ""

        # Publication Date
        year_elem = article.find(".//PubDate/Year")
        paper["Publication Date"] = year_elem.text if year_elem is not None else ""

        # Authors and Affiliations
        authors = []
        affiliations = set()
        for author in article.findall(".//Author"):
            lastname = author.findtext("LastName")
            forename = author.findtext("ForeName")
            fullname = f"{forename} {lastname}" if forename and lastname else None

            affiliation_elem = author.find(".//AffiliationInfo/Affiliation")
            if affiliation_elem is not None:
                affiliation = affiliation_elem.text
                if affiliation:
                    affiliations.add(affiliation)

            if fullname:
                authors.append(fullname)

        paper["Authors"] = authors
        paper["Affiliations"] = list(affiliations)

        papers.append(paper)

    return papers

def detect_non_academic_authors(paper: Dict) -> Dict:
    """Detect non-academic authors & emails from affiliations."""
    company_affiliations = []
    email_addresses = []

    pharma_keywords = ["Inc", "Ltd", "Corporation", "Pharma", "Biotech", "LLC", "Company"]

    for affiliation in paper["Affiliations"]:
        if any(keyword in affiliation for keyword in pharma_keywords):
            company_affiliations.append(affiliation)

    for affiliation in paper["Affiliations"]:
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", affiliation)
        email_addresses.extend(emails)

    return {
        "PubmedID": paper["PubmedID"],
        "Title": paper["Title"],
        "Publication Date": paper["Publication Date"],
        "Non-academic Author(s)": "N/A",  # Placeholder
        "Company Affiliation(s)": "; ".join(company_affiliations),
        "Corresponding Author Email": ", ".join(set(email_addresses))
    }

def export_to_csv(papers: List[Dict], filename: str):
    """Export paper details to CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["PubmedID", "Title", "Publication Date",
                      "Non-academic Author(s)", "Company Affiliation(s)", "Corresponding Author Email"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for paper in papers:
            writer.writerow(paper)
