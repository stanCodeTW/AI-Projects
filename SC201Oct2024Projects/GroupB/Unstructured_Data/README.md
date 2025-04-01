# 🌟 Query for Unstructured Data

This module leverages **HybridRAG** to generate responses for queries regarding companies within the **NASDAQ-100** index, based on their recent **10-K reports** and **earnings transcripts**.

---

## 📌 Project Purpose

This project aims to provide **accurate**, **context-aware** responses by combining:

- **Traditional semantic search**
- **Knowledge graph reasoning**

By integrating both methods, the system enhances financial insights and improves the relevance of responses for users.

---

## ⚙️ Main Functionalities

### 1. Text Extraction (`pdf_text_reader.ipynb`)
- Extract texts from PDF documents using `pdfplumber` and OCR (`pytesseract`).

### 2. Text Embedding (`load_embedd_10-k.ipynb`)
- Process 10-K HTML reports using `BeautifulSoup` and `LangChain`
- Clean, parse, and split text
- Generate embeddings with `sentence-transformers`
- Store embeddings in `ChromaDB` for semantic search

### 3. Knowledge Graph Construction (`pdf_load_graph.ipynb`)
- Extract named entities using `flair`
- Build relationships using LLM to generate triplets
- Construct a **Knowledge Graph** in `Neo4j`

### 4. Hybrid Retrieval & Response Generation (`HybridRAG_Generation.ipynb`)
- Load both **vector database (ChromaDB)** and **knowledge graph (Neo4j)**
- Generate responses with **HybridRAG** using `LangChain` and LLMs

---

## 📂 File Dependencies

| Notebook | Dependencies |
|----------|--------------|
| `pdf_text_reader.ipynb` | `pdfplumber`, `pytesseract` |
| `load_embedd_10-k.ipynb` | `BeautifulSoup`, `LangChain`, `ChromaDB` |
| `pdf_load_graph.ipynb` | `LangChain`, `Neo4j`, `flair` |
| `HybridRAG_Generation.ipynb` | `LangChain`, `Neo4j`, `ChromaDB` |
| Optional | `sentence-transformers-reranking` |

---

## 🚀 Example Usage

Run the notebooks in the following order for best results:

1. **Extract text from PDFs**  
   `pdf_text_reader.ipynb`

2. **Process 10-Ks, split text, generate embeddings**  
   `load_embedd_10-k.ipynb`

3. **Extract entities & build knowledge graph**  
   `pdf_load_graph.ipynb`

4. **Run hybrid retrieval & generate responses**  
   `HybridRAG_Generation.ipynb`

---

## 📌 Notes

- Ensure **ChromaDB** and **Neo4j** are properly set up before running the system.
- 10-Ks must be in **HTML format** for text embedding.
- The **knowledge graph** models relationships between companies, executives, and events.
- The **HybridRAG** system enhances accuracy by combining:
  - **Semantic search (vector DB)**
  - **Structured retrieval (Neo4j graph)**
- Final responses are generated using **OpenAI API** via **LangChain**.

---

## 🧠 Tech Stack

- LangChain
- Neo4j
- ChromaDB
- sentence-transformers
- pdfplumber
- pytesseract
- flair
- BeautifulSoup

---

## 🏁 Goal

Enable intelligent and reliable financial document querying using a hybrid approach, empowering users with deeper insights into NASDAQ-100 companies.