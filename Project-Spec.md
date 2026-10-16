# Project: FirstGig AI (Hacktoberfest Week 2: Side Hustle)

## Objective
Build a lightweight Streamlit application powered by open-source AI (Gemma 2 2B) running via Ollama. 
The app turns technical and soft skills into 3 realistic micro-services, starter pricing, a cold outreach script, and a freelance proposal.

## Constraints & Environment
- Host: Windows 10/11, 8GB RAM, Intel i5 8th Gen
- AI Engine: Local Ollama (gemma2:2b Q4_K_M) or remote fallback
- Architecture:
  - `app.py`: Streamlit frontend and Ollama orchestration
  - `requirements.txt`: streamlit, ollama, pydantic
  - `Dockerfile` & `docker-compose.yml` for containerization
  - Minimal resource usage (do not run heavy local background agents)

## Tasks for Agent
1. Create `requirements.txt` with minimal dependencies.
2. Build `app.py` with clean Streamlit components and structured prompting.
3. Test connectivity to `http://localhost:11434` for Ollama.
4. Add export feature to save outputs as Markdown.