# Intelligence Report Consolidation Tool

Automates the daily workflow of the IS Division, SSB, Kerala Police:
- Reads BACK FILES (event reports, forecasts, social media) for a given date
- Translates Malayalam documents to English
- Generates a consolidated Daily IS Report (.docx)
- Matches persons mentioned in reports against existing PP (Person Profile) files
- Creates new PP profiles and UO Notes for newly identified suspects
- Maintains a Graph Database of relationships (individuals ↔ crimes ↔ records)
- Uses a Graph Neural Network (GNN) to predict hidden suspect associations

---

## Directory Structure

```
27-04-2026/
│
├── BACK FILES/                          ← Input: source intelligence documents
│   └── dd.mm.yyyy/                      ← One subfolder per date (e.g. 10.03.2022)
│       ├── <EventFile>.docx             ← Event/incident reports (any name)
│       ├── TVM.docx / PKD.docx / …      ← District forecast (named by district code)
│       ├── F1.docx / F2.docx / …        ← Numbered forecast files
│       └── SOCIALMEDIA.docx             ← Social media intelligence
│
├── DAILY IS REPORT/                     ← Output: generated daily reports
│   └── IS Daily report dd.mm.yyyy.docx
│
├── PP & Uo Note Dummy-…/
│   └── PP & Uo Note Dummy/             ← Profile database
│       ├── PP Form details.docx         ← REQUIRED: blank profile template
│       ├── 1)  Name.docx                ← Individual PP profiles (numbered)
│       ├── 1a) UO Name.docx             ← Corresponding UO notes
│       └── …
│
├── graph_db.json                        ← Auto-generated: relationship graph
│
├── intel_tool.py                        ← Main CLI entry point
├── utils.py                             ← Core utilities (parsing, matching, reports)
├── graph_db.py                          ← Graph DB + GNN implementation
├── cleanup_junk_profiles.py             ← One-time cleanup utility
├── test_tool.py                         ← Unit tests
├── test_matching.py                     ← Profile matching tests
└── requirements.txt                     ← Python dependencies
```

---

## Prerequisites

### Python
Python 3.10 or later is required.

### Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
| Package | Purpose |
|---|---|
| `python-docx` | Read and write .docx files |
| `deep-translator` | Malayalam → English translation (Google free) |
| `requests` | Ollama integration (optional, better translation) |
| `networkx` | Graph database |
| `numpy` | Numerical operations |
| `scikit-learn` | TF-IDF feature extraction |
| `torch` | PyTorch GCN (Graph Neural Network) |
| `pytest` | Running unit tests |

### Optional: Ollama (Better Translation)
Install [Ollama](https://ollama.com) and pull the `llama3` model for higher-quality Malayalam translation:
```bash
ollama pull llama3
ollama serve
```
The tool automatically detects and uses Ollama if running. Falls back to Google Translate (via `deep-translator`) otherwise.

---

## Usage

### 1. Generate a Daily IS Report
Takes all BACK FILES for a date, translates them, and produces a consolidated report:
```bash
python intel_tool.py consolidate 10.03.2022
```
- Reads from: `BACK FILES/10.03.2022/`
- Writes to:  `DAILY IS REPORT/IS Daily report 10.03.2022.docx`
- Automatically updates PP profiles and the graph database

```bash
# Overwrite an existing report
python intel_tool.py consolidate 10.03.2022 --force

# Disable Ollama even if running
python intel_tool.py consolidate 10.03.2022 --no-ollama
```

### 2. Sync Profiles from an Existing Report
Re-scan a generated report and update profiles without regenerating the report:
```bash
python intel_tool.py sync-profiles "DAILY IS REPORT/IS Daily report 10.03.2022.docx"
```

### 3. Generate a UO Note
Generate a Malayalam Unofficial Note from an existing PP profile:
```bash
python intel_tool.py generate-uo "PP & Uo Note Dummy-…/PP & Uo Note Dummy/2) Chittur Kutty.docx"
```

### 4. Query the Graph Database
```bash
# Show node/edge statistics
python intel_tool.py graph-query --stats

# Show a suspect's profile, connections, and GNN-predicted hidden associates
python intel_tool.py graph-query --person "Chittoor Kutty"
```

### 5. Clean Junk Nodes from the Graph
```bash
python intel_tool.py clean-graph
```
Removes any Individual nodes from `graph_db.json` whose name is a place, org, or report jargon. Run this if the graph ever gets stale or corrupted.

---

## Profile Database Rules

The PP directory must contain:
- **`PP Form details.docx`** — the blank profile template (required for new profiles)
- Profile files named: `<number>)  <Name>.docx`
- UO note files named: `<number><letter>) UO <Name>.docx`

### Profile Field Format
Each profile `.docx` must have fields in `Key-Value` format:
```
Name of Person-Chittoor Kutty
Parentage Name-Rajan
Address-Meleparambil, Nilambur, Palakkad
Police Station-Chittur
PP ID-040/PKD
Type of Activity-Extremism
```

---

## BACK FILES Structure

| File pattern | Section | Description |
|---|---|---|
| Any `.docx` (not district code, not F#, not SOCIAL) | Section I — Events | Daily incident/event reports |
| `TVM.docx`, `KLM.docx`, … (14 district codes) | Section II — Forecasts | District-level forecasts |
| `F1.docx`, `F2.docx`, … | Section II — Forecasts | Numbered forecast files |
| `SOCIALMEDIA.docx` (or any filename containing "social media") | Section III — Social Media | RSU social media reports |

---

## First-Time Cleanup

If you have junk profiles created before name filtering was fully applied, run:
```bash
# Preview what will be deleted (safe — no files removed)
python cleanup_junk_profiles.py

# Delete the junk profiles and UO notes
python cleanup_junk_profiles.py --delete
```

This removes profiles named things like `According`, `Shadow`, `Kulathupuzha PS`, `City`, etc.

---

## Running Tests
```bash
python -m pytest test_tool.py -v
```
Expected output: **8 passed**

---

## How Name Extraction Works

When processing an event report, the tool:
1. Splits text into logical phrases on commas, semicolons, and prepositions
2. Extracts consecutive Title-Case word sequences (1–3 words)
3. Rejects any sequence containing a word from the **junk-word blocklist** (~300 terms)
4. Rejects sequences that consist entirely of **known place names** (~80 terms)
5. Strips parent names (`S/o`, `D/o`, `W/o` patterns) from the candidate set
6. Matches remaining candidates against existing PP profiles using fuzzy/phonetic matching

### Disambiguation
When a name matches multiple profiles, the GNN TF-IDF scorer ranks candidates by how well each profile's stored data aligns with the event text context.

---

## GNN Training

The Graph Neural Network trains automatically each time `consolidate` or `sync-profiles` runs:
- **Input features**: TF-IDF vectors from node description strings (64 features)
- **Architecture**: 2-layer GCN, 48 hidden dimensions, 32 output dimensions  
- **Task**: Link prediction (BCE loss, positive + negative edge sampling)
- **Training**: 50–100 epochs on CPU, completes in < 1 second for graphs up to ~200 nodes
- **Output**: 32-D embeddings used for cosine-similarity associate recommendations

No GPU or Colab needed for this dataset size.
