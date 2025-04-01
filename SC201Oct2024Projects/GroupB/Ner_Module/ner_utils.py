from flair.models import SequenceTagger
from flair.data import Sentence
from difflib import get_close_matches
import re

# Import the NASDAQ company-to-ticker mapping dictionary
from nasdaq_companies import company_to_ticker

# Import mappings for relative time expressions
from relative_years import past_years_map, future_years_map

# Get the current year (based on financial report date)
CURRENT_YEAR = 2024

# Load the Flair NER model
tagger = SequenceTagger.load("flair/ner-english-ontonotes-large")


def extract_company_ticker(text):
    """
    Extract company name and convert it to ticker symbol.
    1. Use Flair NER to detect organization names.
    2. Try exact match with known companies.
    3. Use fuzzy matching for close alternatives if direct match fails.
    """
    sentence = Sentence(text)
    tagger.predict(sentence)
    entities = sentence.to_dict(tag_type="ner")["entities"]

    # Extract organization (ORG) entities
    detected_companies = [ent["text"] for ent in entities if ent["labels"][0]["value"] == "ORG"]

    if detected_companies:
        ner_company = " ".join(detected_companies).lower()
        print(f"Detected company by NER: {ner_company}")

        # Check for exact match
        if ner_company in company_to_ticker:
            ticker = company_to_ticker[ner_company]
            print(f"Exact match found: {ticker}")
            return {"company": ner_company, "ticker": ticker}

        # Try fuzzy matching if not found
        closest_match = get_close_matches(ner_company, company_to_ticker.keys(), n=1, cutoff=0.6)
        if closest_match:
            matched_company = closest_match[0]
            ticker = company_to_ticker[matched_company]
            print(f"Fuzzy match: {matched_company}, Ticker：{ticker}")
            return {"company": matched_company, "ticker": ticker}

        print("Company detected but not in NASDAQ-100.")
        return {"company": ner_company, "ticker": None}

    print("No company detected by NER.")
    return {"company": None, "ticker": None}


def extract_year(text):
    """
    Extract year from input text.
    1. Try Flair NER to identify DATE entities.
    2. Use regex to find 4-digit years if NER fails.
    3. Handle relative time phrases like 'last year' or '2 years ago'.
    """
    sentence = Sentence(text)
    tagger.predict(sentence)
    entities = sentence.to_dict(tag_type="ner")["entities"]

    # Extract date entities
    detected_years = [ent["text"] for ent in entities if ent["labels"][0]["value"] == "DATE"]

    # If NER fails, use regex to extract year
    if not detected_years:
        regex_years = re.findall(r"\b(19[0-9]{2}|20[0-9]{2})\b", text)
        if regex_years:
            detected_years = regex_years

    year = detected_years[0] if detected_years else None

    # Check for past time expressions
    for key, past_offset in past_years_map.items():
        if key in text.lower():
            year = CURRENT_YEAR - past_offset

    # Check for future time expressions
    for key, future_offset in future_years_map.items():
        if key in text.lower():
            year = CURRENT_YEAR - future_offset  # Negative offset for future

    # Handle specific patterns like "5 years ago"
    match = re.search(r"(\d+) years ago", text.lower())
    if match:
        years_ago = int(match.group(1))
        year = CURRENT_YEAR - years_ago

    match = re.search(r"(\d+) years later", text.lower())
    if match:
        years_later = int(match.group(1))
        year = CURRENT_YEAR + years_later

    if year:
        match = re.search(r"\b(19[0-9]{2}|20[0-9]{2})\b", str(year))
        if match:
            year = int(match.group(1))
            print(f"Extracted year: {year}")
        else:
            print(f"Invalid year format: {year}")
            year = None
    else:
        print("No year detected.")

    return {"year": year} if year else None
