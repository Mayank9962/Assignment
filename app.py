import streamlit as st
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
from langchain_ollama import OllamaLLM
import json
import re
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="Research Report Generator", layout="centered")

if "llm" not in st.session_state:
    st.session_state.llm = None
if "query_cache" not in st.session_state:
    st.session_state.query_cache = {}

def initialize_components():
    if st.session_state.llm is None:
        print(f"[DEBUG] Initializing LLM with model: deepseek-r1:8b")
        start_time = datetime.now()
        st.session_state.llm = OllamaLLM(model="deepseek-r1:8b")
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[DEBUG] LLM initialization completed in {elapsed:.2f} seconds")
        

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:()\-\'"]', '', text)
    return text.strip()

def extract_search_results(query):
    print(f"[DEBUG] Starting SERPAPI search for query: {query}")
    start_time = datetime.now()
    
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        st.error("SERPAPI_KEY not found in environment variables")
        return None, []
    
    params = {
        "q": query,
        "api_key": serpapi_key,
        "engine": "google",
        "num": 10
    }
    
    print(f"[DEBUG] Calling SERPAPI...")
    search = GoogleSearch(params)
    results = search.get_dict()
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"[DEBUG] SERPAPI search completed in {elapsed:.2f} seconds")
    
    extracted_texts = []
    sources = []
    
    if "organic_results" in results:
        for result in results["organic_results"]:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            if link:
                sources.append(link)
            
            combined_text = f"{title} {snippet}"
            cleaned = clean_text(combined_text)
            if cleaned:
                extracted_texts.append(cleaned)
    
    if "answer_box" in results:
        answer = results["answer_box"]
        answer_text = ""
        if "answer" in answer:
            answer_text = answer["answer"]
        elif "snippet" in answer:
            answer_text = answer["snippet"]
        if answer_text:
            cleaned = clean_text(answer_text)
            if cleaned:
                extracted_texts.insert(0, cleaned)
    
    if "knowledge_graph" in results:
        kg = results["knowledge_graph"]
        if "description" in kg:
            cleaned = clean_text(kg["description"])
            if cleaned:
                extracted_texts.insert(0, cleaned)
    
    full_text = " ".join(extracted_texts)
    print(f"[DEBUG] Extracted {len(extracted_texts)} text chunks, {len(sources)} sources")
    print(f"[DEBUG] Total context text length: {len(full_text)} characters")
    return full_text, sources

def check_existing_query(query):
    query_lower = query.lower().strip()
    print(f"[DEBUG] Checking cache for query: {query_lower}")
    if query_lower in st.session_state.query_cache:
        print(f"[DEBUG] Cache HIT - found existing data")
        cached_data = st.session_state.query_cache[query_lower]
        return cached_data.get("context"), cached_data.get("sources", [])
    print(f"[DEBUG] Cache MISS - no existing data found")
    return None, None

def save_to_cache(query, context_text, sources, report):
    query_lower = query.lower().strip()
    st.session_state.query_cache[query_lower] = {
        "context": context_text,
        "sources": sources,
        "report": report,
        "timestamp": datetime.now().isoformat()
    }

def generate_report(query, context_text, sources):
    print(f"[DEBUG] Starting report generation...")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Context text length: {len(context_text)} characters")
    print(f"[DEBUG] Number of sources: {len(sources)}")
    
    source_list = "\n".join([f"- {source}" for source in sources[:10]])
    
    prompt_template = """You are a research analyst. Based on the following context information, generate a comprehensive research report.

Context Information:
{context}

Query: {query}

Generate a detailed report following this exact structure:

---
📌 Research Summary: {query}

🏷 Overview:
[Provide a comprehensive overview of the topic]

📍 Verified Facts:
- [List key verified facts, one per line with dash]

📊 Extracted Data:
[Present structured data and statistics]

💡 Insights:
[Provide analytical insights and interpretations]

🔗 Sources / References:
{source_list}

🎯 Confidence Score (0–100):
[Provide a numerical confidence score based on source quality and information completeness]

---

Be thorough, accurate, and well-structured. Use the context information provided."""

    formatted_prompt = prompt_template.format(context=context_text, query=query, source_list=source_list)
    print(f"[DEBUG] Formatted prompt length: {len(formatted_prompt)} characters")
    print(f"[DEBUG] Calling LLM (this may take a while)...")
    
    start_time = datetime.now()
    try:
        response = st.session_state.llm.invoke(formatted_prompt)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[DEBUG] LLM response received in {elapsed:.2f} seconds")
        print(f"[DEBUG] Response length: {len(response)} characters")
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[DEBUG] ERROR during LLM call after {elapsed:.2f} seconds: {str(e)}")
        response = f"Error generating report: {str(e)}"
    
    return response

def main():
    initialize_components()
    
    st.markdown(
        "<h1 style='text-align: center;'>Research Report Generator</h1>",
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    query = st.text_input("Enter your research query:", placeholder="e.g., Latest developments in AI")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        generate_btn = st.button("Generate Report", type="primary", use_container_width=True)
    
    report_text = ""
    
    if generate_btn and query:
        total_start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"[DEBUG] ===== NEW REQUEST STARTED =====")
        print(f"[DEBUG] Query: {query}")
        print(f"[DEBUG] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        with st.spinner("Processing your query..."):
            existing_content, existing_sources = check_existing_query(query)
            
            if existing_content:
                print(f"[DEBUG] Using cached data")
                st.info("Found existing data for this query. Generating report from cached information...")
                context_text = existing_content
                sources = existing_sources
            else:
                print(f"[DEBUG] Fetching new data from SERPAPI")
                st.info("Fetching latest information from the internet...")
                context_text, sources = extract_search_results(query)
                
                if not context_text:
                    print(f"[DEBUG] ERROR: No context text extracted")
                    st.error("No information found. Please try a different query.")
                    return
            
            st.info("Generating report using LLM...")
            report_text = generate_report(query, context_text, sources)
            
            if report_text:
                print(f"[DEBUG] Saving to cache...")
                save_to_cache(query, context_text, sources, report_text)
                st.session_state.current_report = report_text
                st.session_state.current_query = query
                
                total_elapsed = (datetime.now() - total_start_time).total_seconds()
                print(f"\n{'='*60}")
                print(f"[DEBUG] ===== REQUEST COMPLETED =====")
                print(f"[DEBUG] Total time: {total_elapsed:.2f} seconds")
                print(f"{'='*60}\n")
    
    if "current_report" in st.session_state and st.session_state.current_report:
        st.markdown("### Generated Report:")
        st.markdown(
            f"<div style='border: 1px solid #444; padding: 20px; border-radius: 5px; max-height: 500px; overflow-y: auto; background-color: #000000;'>"
            f"<pre style='white-space: pre-wrap; font-family: inherit; color: #ffffff;'>{st.session_state.current_report}</pre>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with col2:
            report_bytes = st.session_state.current_report.encode('utf-8')
            st.download_button(
                label="Download .txt",
                data=report_bytes,
                file_name=f"report_{st.session_state.current_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
