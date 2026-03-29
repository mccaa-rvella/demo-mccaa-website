import os
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
import fitz  # PyMuPDF
from openai import OpenAI

# Load environment variables
load_dotenv(dotenv_path="../.env")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "mysecretpassword")
DB_NAME = os.getenv("DB_NAME", "mccaa_website")

def init_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Drop table to safely migrate column size back to OpenAI's 1536
    cursor.execute("DROP TABLE IF EXISTS documents;")
    
    cursor.execute("""
    CREATE TABLE documents (
        id SERIAL PRIMARY KEY,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT,
        type TEXT,
        metadata JSONB,
        embedding vector(1536)
    );
    """)
    conn.commit()
    return conn, cursor

def download_and_parse_pdf(url):
    print(f"Downloading PDF from {url}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.mccaa.org.mt/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        
        tmp_path = "/tmp/temp_mccaa_doc.pdf"
        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        text = ""
        doc = fitz.open(tmp_path)
        for page in doc:
            text += page.get_text()
            
        return text
    except Exception as e:
        print(f"Error extracting PDF {url}: {e}")
        return ""

def get_embedding(text, client):
    if not client: return None
    try:
        response = client.embeddings.create(
            input=text,
            model="openai/text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def main():
    if not FIRECRAWL_API_KEY:
        print("Missing FIRECRAWL_API_KEY.")
        return
        
    print("Initializing Database...")
    conn, cursor = init_db()
    
    print("Initializing Firecrawl and OpenRouter OpenAI...")
    fc_app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    
    openai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    ) if OPENROUTER_API_KEY else None
    
    target_url = "https://www.mccaa.org.mt"
    print(f"Starting crawl for {target_url}...")
    
    try:
        cache_file = "firecrawl_cache.json"
        
        if os.path.exists(cache_file):
            print("Found local cache. Loading data from cache instead of re-crawling...")
            with open(cache_file, "r") as f:
                data = json.load(f)
        else:
            job = fc_app.crawl(
                url=target_url,
                limit=100,
                scrape_options={"formats": ["markdown", "links"], "includeHtml": False}
            )
            data = job.get('data', []) if isinstance(job, dict) else getattr(job, 'data', [])
            serializable_data = []
            for page in data:
                if hasattr(page, 'model_dump'): serializable_data.append(page.model_dump())
                elif hasattr(page, 'dict'): serializable_data.append(page.dict())
                else: serializable_data.append(getattr(page, '__dict__', page if isinstance(page, dict) else {}))
            data = serializable_data
            with open(cache_file, "w") as f: json.dump(data, f)
        
        pdf_links_to_process = set()
        
        for page in data:
            if hasattr(page, 'model_dump'): p_dict = page.model_dump()
            elif hasattr(page, 'dict'): p_dict = page.dict()
            else: p_dict = getattr(page, '__dict__', page if isinstance(page, dict) else {})
                
            metadata = p_dict.get('metadata', {})
            if not isinstance(metadata, dict): metadata = getattr(metadata, 'model_dump', lambda: getattr(metadata, '__dict__', {}))()
                
            url = metadata.get('sourceURL', '')
            title = metadata.get('title', 'Unknown Title')
            content = p_dict.get('markdown', '')
            links = p_dict.get('links', [])
            
            content = content or ""
            links = links or []
            
            for link in links:
                if link.lower().endswith('.pdf'): pdf_links_to_process.add(link)
            
            print(f"Processing Webpage: {url}")
            embedding = get_embedding(content[:8000], openai_client) if openai_client and content else None
            
            cursor.execute("""
            INSERT INTO documents (url, title, content, type, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
            """, (url, title, content, 'webpage', json.dumps(metadata), embedding))
            
        print(f"Found {len(pdf_links_to_process)} PDFs to parse.")
        for pdf_url in pdf_links_to_process:
            if not pdf_url.startswith('http'): continue
                
            pdf_text = download_and_parse_pdf(pdf_url)
            if pdf_text:
                embedding = get_embedding(pdf_text[:8000], openai_client) if openai_client else None
                cursor.execute("""
                INSERT INTO documents (url, title, content, type, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
                """, (pdf_url, pdf_url.split('/')[-1], pdf_text, 'pdf', json.dumps({"source": "pdf_extraction"}), embedding))
                
        conn.commit()
        print("Data ingestion complete.")
        
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
