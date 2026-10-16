# ⚡ FirstGig AI — Turn Skills into Freelance Side Hustles

> **DEV Community Challenge Submission — Side Hustle Track**  
> A lightweight, local-first freelance strategy generator that translates technical and soft skills into scoped micro-services, pricing models, cold outreach scripts, and client proposal templates.

---

## 🎯 Overview

Starting a freelance side hustle often fails at the positioning phase: developers either sell commoditized hourly labor or struggle to communicate business value to non-technical clients.

**FirstGig AI** bridges this gap. By analyzing your technical skills, soft skills, and target market niche, it creates a structured **Freelance Launch Blueprint** within seconds. It runs completely locally using open weights (**Google Gemma 2 2B** via **Ollama**) with zero paid API dependencies, and includes an instant deterministic fallback mode so the application remains demonstrable even on machines without Ollama running.

---

## 🏗️ Architecture & Data Flow

```text
┌────────────────────────────────────────────────────────┐
│               Streamlit Web Interface                  │
│  (Skill inputs, Niche selection, Platform parameters) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Input Sanitization Layer  │
              │ (Length bounds, Escaping) │
              └─────────────┬─────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    [Ollama Online]                 [Ollama Offline / Demo]
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Local Ollama Service  │       │ Deterministic Engine  │
│ (Gemma 2 2B via HTTP) │       │ (Structured Templates)│
│  - 1x auto-retry      │       │  - Zero network call  │
│  - Strict JSON mode   │       │  - Clear demo badges  │
└───────────┬───────────┘       └───────────┬───────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
              ┌───────────────────────────┐
              │  Pydantic v2 Validation   │
              │  - Exactly 3 services     │
              │  - Exactly 3 pricing tiers│
              │  - Non-empty constraints  │
              └─────────────┬─────────────┘
                            │
                            ▼
       ┌────────────────────┴────────────────────┐
       │                                         │
       ▼                                         ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐
│       Interactive UI Tabs     │ │       Export Engines          │
│ • 3 Scoped Micro-Services     │ │ • Formatted PDF (fpdf2)       │
│ • Tiered Pricing Strategy     │ │ • Markdown Report (.md)       │
│ • Net Rate Calculator         │ │ • Platform-ready Copy (.txt)  │
│ • Cold Outreach & Proposal    │ └───────────────────────────────┘
└───────────────────────────────┘
```

---

## ✨ Features

1. **Scoped Micro-Service Generator**: Generates exactly 3 concrete, outcome-focused service packages (Title, Tagline, Target Persona, Bullet Deliverables, Turnaround) rather than generic hours.
2. **3-Tier Illustrative Pricing**: Starter Sprint, Full Implementation, and Growth Retainer tiers calculated in your chosen currency (`USD`, `EUR`, `INR`, `GBP`).
3. **Platform-Specific Rate Calculator**: Calculates estimated gross and take-home net earnings across platforms (`Upwork` 10%, `Fiverr` 20%, `Toptal`, `Direct / LinkedIn`) based on experience bracket.
4. **Structured Outreach Playbook**: Value-first cold outreach messaging and a polite 3-day follow-up script.
5. **Client Proposal Template**: Modular proposal outline containing problem empathy, roadmap phases, qualifications, and clear calls to action.
6. **One-Click Platform Formatter**: Formats output for immediate pasting into Upwork Bids, LinkedIn Posts, Fiverr Gig descriptions, or Cold Emails.
7. **Multi-Format Exports**: One-click download of the complete blueprint as Markdown (`.md`) or a formatted PDF report (`.pdf`).
8. **Deterministic Demo / Fallback Mode**: Instantly demonstrable offline without needing to download models or configure external services.

---

## ⚙️ Configuration & Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server API base URL |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Alternative alias for Ollama endpoint |
| `OLLAMA_MODEL` | `gemma2:2b` | Default model tag to query |
| `STREAMLIT_SERVER_PORT` | `8501` | Port on which Streamlit listens |

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10 or 3.11
- **Hardware**: Compatible with 8 GB RAM and standard CPU (no dedicated GPU required)
- **Ollama** (optional for live AI inference, not required for demo mode): [ollama.com](https://ollama.com)

---

### Option A: Native Local Run (Recommended for Low-Resource Environments)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mehtachandrashekhar/FirstGig.git
   cd FirstGig
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS / WSL
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Run Ollama and pull Gemma 2 2B**:
   ```bash
   ollama pull gemma2:2b
   ollama run gemma2:2b
   ```
   *If you skip this step, FirstGig AI automatically operates in Demo / Fallback Mode.*

5. **Start Streamlit**:
   ```bash
   streamlit run app.py
   ```
   Open [http://localhost:8501](http://localhost:8501) in your browser.

---

### Option B: Docker Compose (App + Ollama Service)

1. **Build and launch the containers**:
   ```bash
   docker compose up --build
   ```

2. **Access the application**:
   Open [http://localhost:8501](http://localhost:8501).

3. **Pull the model inside the Ollama container**:
   ```bash
   docker exec -it firstgig_ollama ollama pull gemma2:2b
   ```

4. **Persisted Storage**:
   Models are persisted inside the named volume `ollama_storage` across container restarts.

---

## 🧪 Automated Testing & CI

FirstGig AI includes a pytest test suite covering validation, security, calculation arithmetic, and exports. All external Ollama calls are mocked so tests run in seconds without requiring network access or models.

### Running Tests Locally

```bash
pytest tests/ -v
```

### Test Suite Coverage:
- **`tests/test_models.py`**: Pydantic schema validation, non-empty string checks, strict enforcement of exactly 3 services and 3 pricing tiers.
- **`tests/test_rates.py`**: Rate calculation arithmetic, platform fee bounds, and default fallback handling.
- **`tests/test_fallback.py`**: Verification of deterministic fallback data, demo flag labeling, and absence of fabricated guarantees.
- **`tests/test_security.py`**: XSS prevention, HTML escaping verification, and input length sanitization.
- **`tests/test_exports.py`**: Markdown structure validation and PDF generation with Unicode/Latin-1 character normalization.
- **`tests/test_ollama.py`**: Mocked inference tests verifying success path, 1x automatic retry on malformed JSON, and clean error reporting on model-not-found / timeout.

### Continuous Integration
A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the full test suite automatically across Python 3.10 and 3.11 on every push and pull request.

---

## ⚠️ Disclaimers & Limitations

1. **Illustrative Pricing Guidelines**: All rate calculations, suggested price ranges, and platform fees are illustrative starting points based on common industry benchmarks. They do not constitute financial advice or guarantee earnings. Platform fees (such as Upwork's 10% fee or Fiverr's 20% seller fee) should be verified directly against the latest terms of service on each platform.
2. **AI-Generated Content Review**: AI suggestions should always be reviewed and tailored before communicating with potential clients. FirstGig AI does not guarantee conversion rates or client acquisition.
3. **Demo / Fallback Mode vs. Live AI**: When Ollama is offline or unconfigured, the application presents sample demo data clearly labeled with badge indicators. Demo templates are deterministic and designed for evaluation.
4. **Local Hardware Constraints**: On CPU-only systems with 8 GB RAM, Gemma 2 2B inference typically takes between 30 and 60 seconds per generation.

---

## 📄 Licensing

- **Application Software**: Released under the [MIT License](LICENSE).
- **AI Model Weights**: Google Gemma 2 2B is governed by the [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and Google's Responsible AI Policy. Users deploying the model weights are responsible for complying with Gemma's terms and permissible use policies.
