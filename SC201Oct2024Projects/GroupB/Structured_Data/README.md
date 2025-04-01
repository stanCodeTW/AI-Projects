# FinScope3D: Structured_Data query

This project builds an intelligent Q&A system for financial data using two core modules:

- **Financial Data Ingestion via yfinance**  
- **Vector-Based Semantic Search with ChromaDB and OpenAI**

---

## yfinance_data_ingestion.ipynb

### Overview
Fetches annual financial statements (Income Statement, Balance Sheet, Cash Flow) for NASDAQ-100 companies using `yfinance`, then stores the data into an SQLite database on Google Drive.

### Pipeline
1. Install packages and mount Google Drive
2. Create and initialize the SQLite database
3. Define helper functions to extract and format financial data
4. Iterate through all NASDAQ-100 tickers and store their 10-K data

### Technologies
- `yfinance`
- `sqlite3`
- `pandas`
- `json` and `re` (for year extraction and formatting)

---

## chroma_embedding_generation.ipynb

### Overview
Loads structured financial data from SQLite, converts it into text format, embeds it into a ChromaDB vector store, and allows natural language queries via OpenAI’s GPT model.

### Pipeline
1. Install necessary packages and mount Google Drive
2. Initialize ChromaDB and create or load a collection
3. Batch insert financial records into ChromaDB
4. Enable querying using natural language
5. Use OpenAI GPT to generate human-readable answers based on vector search results

### Technologies
- `chromadb`: vector storage and retrieval
- `openai`: for natural language answers
- `sqlite3`: data source
- `torch`: GPU availability check

### Sample Usage
```python
query_chromadb("AAPL 2023 financials Revenue")
generate_answer_with_openai("What was Tesla's accounts payable in 2021?")
```

---

## Project Structure
```text
├── yfinance_data_ingestion.ipynb       # Financial data extraction and storage
├── chroma_embedding_generation.ipynb    # Embedding generation and semantic Q&A
└── README.md                            # Project documentation
```

---

## Status
- NASDAQ-100 10-K data from 2020–2025 ingested
- ChromaDB and GPT integration tested and working
