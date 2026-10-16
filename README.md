# ⚡ FirstGig AI (Hacktoberfest Week 2: Side Hustle)

Turn your technical and soft skills into 3 realistic micro-services, starter pricing, high-converting cold outreach scripts, and client-winning freelance proposals.

Built as a lightweight, resource-efficient Streamlit application powered by open-source AI (**Gemma 2 2B**) running via **Ollama**.

---

## 🚀 Features

- **🎯 Skill Matrix Transformation**: Automatically transforms a combination of technical tools (e.g. Python, React, APIs) and soft skills (communication, reliability) into concrete, market-ready offerings.
- **🛠️ 3 Scoped Micro-Services**: Focuses on bite-sized, outcome-based deliverables rather than commoditized hourly work.
- **💰 3-Tier Pricing Strategy**: Structured tiers (Starter Sprint, Standard Implementation, Growth Retainer) tailored in your preferred currency (USD, EUR, INR, GBP).
- **📨 Cold Outreach Playbook**: Non-salesy, value-first email/LinkedIn scripts with a 3-day polite follow-up.
- **📝 Winning Freelance Proposal**: Complete proposal structure with problem understanding, milestone roadmap, "Why Me" pitch, and low-friction call-to-action.
- **📄 Markdown Export**: Download complete blueprints as a clean `.md` file or save directly to your workspace.
- **🛡️ Built-in Offline Fallback / Demo Mode**: Test and explore all features immediately even if Ollama is not yet downloaded or running.

---

## 💻 Tech Stack & Environment

- **Frontend & Logic**: Streamlit
- **AI Engine**: Ollama (`gemma2:2b Q4_K_M`) or configurable remote endpoint
- **Data Validation**: Pydantic v2
- **Optimized for**: 8GB RAM, Intel Core i5 8th Gen, Windows 10/11

---

## 🛠️ Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Local Ollama (Recommended)
1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull and run the Gemma 2 2B model:
   ```bash
   ollama run gemma2:2b
   ```
3. Ollama will run on `http://localhost:11434`.

> **Note**: If Ollama is not installed or offline, the app includes a **Demo / Fallback Mode** so you can test the full user journey without delay.

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🐳 Running with Docker

### Using Docker Compose (App + Ollama)
```bash
docker compose up --build
```
Once the containers start:
1. Access Streamlit at `http://localhost:8501`.
2. To download the model into the Ollama container:
   ```bash
   docker exec -it firstgig_ollama ollama pull gemma2:2b
   ```

---

## 📁 Project Structure

```
FirstGig/
├── app.py                # Main Streamlit application & AI orchestration
├── requirements.txt      # Minimal Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Multi-container setup (Streamlit + Ollama)
├── Project-Spec.md       # Original specification
└── README.md             # Documentation
```
