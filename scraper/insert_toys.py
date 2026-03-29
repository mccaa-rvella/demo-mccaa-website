import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv(dotenv_path="../.env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

toy_content = """
Toy Safety Regulations (S.L. 427.40) & Directive 2009/48/EC on the Safety of Toys.

Before placing or importing a toy on the market in Malta, manufacturers and importers must ensure strict compliance with the following requirements:
1. CE Marking: The toy must bear a visible, legible, and indelible CE mark, assuring it meets EU safety standards.
2. Safety Assessment: Conduct a thorough hazard and safety assessment covering physical, mechanical, chemical, and electrical risks.
3. Instructions & Warnings: Ensure the toy is accompanied by clear instructions for use and critical safety warnings in either Maltese or English.
4. Traceability: The toy must bear a type, batch, serial, or model number, alongside the manufacturer's or importer's registered trade name and contact address.
5. Documentation: Keep the technical documentation and the EC Declaration of Conformity available to the Market Surveillance Directorate for a period of 10 years after placing it on the market.
6. Customs Clearance: Importing toys from non-EU nations requires clearance through Malta Customs, who closely coordinate with the MCCAA Market Surveillance Directorate to intercept non-compliant toys.

If a toy is found to be dangerous, the MCCAA holds the right to demand product recalls via the RAPEX rapid alert system.
"""

print("Embedding Toys content...")
res = client.embeddings.create(input=toy_content, model="openai/text-embedding-3-small")
emb = res.data[0].embedding

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5434")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "mysecretpassword")
DB_NAME = os.getenv("DB_NAME", "mccaa_website")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    dbname=DB_NAME
)
cursor = conn.cursor()

cursor.execute("""
INSERT INTO documents (url, title, content, type, metadata, embedding)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO UPDATE SET content = EXCLUDED.content, embedding = EXCLUDED.embedding
""", (
    "https://mccaa.org.mt/section/toys-safety",
    "Toys Safety Regulations and Import Rules",
    toy_content,
    "webpage",
    json.dumps({"source": "manual_seed"}),
    emb
))

conn.commit()
cursor.close()
conn.close()

print("Successfully injected Toy Safety Data into the RAG Database!")
