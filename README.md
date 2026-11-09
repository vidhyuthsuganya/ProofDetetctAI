# ProofDetect AI: Refined Web Prototype

## What this version does
- Runs as a local website using Streamlit.
- Offers grade bands from Grades 1–2 through Grades 11–12.
- Includes **Solve / explain a statement** so a student can ask for a solution without knowing the reason.
- Solves/checks selected arithmetic equalities, some simple one-variable equations, and a few common angle word problems.
- Checks selected proof-step patterns and simple numerical equalities.
- Returns SUPPORTED PATTERN, LIKELY INCORRECT, NEEDS REVIEW, SOLVED, CHECKED, NOT TRUE, or NEEDS MORE DETAIL, with explanations.

## Important limitation
This is not a universal proof checker or general-purpose AI. It does not validate every proof, understand arbitrary diagrams, or solve all curriculum topics. A supported pattern is not a guarantee that the full proof is correct. Expand the rule library using teacher-reviewed examples and report measured results honestly.

## Windows setup
1. Install Python from https://www.python.org/downloads/windows/
2. Extract this ZIP to a folder.
3. Open the extracted folder in File Explorer.
4. Click the address bar, type `cmd`, and press Enter.
5. Run these commands one at a time:

   `py -m venv .venv`

   `.venv\Scripts\activate`

   `python -m pip install --upgrade pip`

   `pip install -r requirements.txt`

   `python -m streamlit run app.py`

6. Open `http://localhost:8501` in your browser.
7. Keep Command Prompt open while using the site. Press Ctrl+C to stop it.

If `requirements.txt` is missing or installation fails, run:
`python -m pip install streamlit`
Then run:
`python -m streamlit run app.py`
from the folder containing `app.py`.
