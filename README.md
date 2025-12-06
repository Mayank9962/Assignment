# Research Report Generator

A Streamlit web application that generates research reports using RAG (Retrieval Augmented Generation) with SERPAPI, Chroma, and Ollama.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your SERPAPI key to `.env`

3. Make sure Ollama is running with the deepseekR1 7B model:


4. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Enter a research query in the text input
2. Click "Generate Report"
3. The app will fetch information from SERPAPI (first time) or use cached data
4. Review the generated report
5. Download the report as a .txt file



