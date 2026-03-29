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

white_goods_content = """
Domestic Electrical Appliances (White Goods) Regulations

Before placing or importing white goods (fridges, washing machines, dishwashers, ovens, air conditioners, etc.) on the market in Malta, manufacturers and importers must strictly comply with the following interrelated directives:

1. Low Voltage Directive (LVD) (2014/35/EU): All domestic electrical machinery must be safe for use within specific voltage limits. Devices must carry the CE Mark and a Declaration of Conformity.
2. EcoDesign Directive (2009/125/EC): White goods and household appliances must meet minimum environmental and energy efficiency requirements. Models that fail to meet these minimum energy performance standards (MEPS) cannot be imported or sold.
3. Energy Labelling Framework (Regulation (EU) 2017/1369): Appliances must feature an accurate, visible Energy Rating Label at the point of sale (both physical and online), scaling from A to G in relation to energy efficiency.
4. EPREL Registration: The European Product Registry for Energy Labelling (EPREL). All models of white goods MUST be registered in the EPREL database before being placed on the European market. A QR code linking to the EPREL product sheet must be printed on the Energy Label.
5. Electromagnetic Compatibility (EMC) Directive (2014/30/EU): Appliances must not generate excessive electromagnetic interference and must be immune to normal interference from other equipment.
6. WEEE Directive: Importers are responsible for the Waste Electrical and Electronic Equipment (WEEE) regulations, ensuring proper end-of-life recycling.
"""

print("Embedding White Goods compliance dataset...")
res = client.embeddings.create(input=white_goods_content, model="openai/text-embedding-3-small")
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
    "https://mccaa.org.mt/section/appliances-energy",
    "Household Electrical Appliances (White Goods) and Energy Labelling",
    white_goods_content,
    "webpage",
    json.dumps({"source": "manual_seed"}),
    emb
))

conn.commit()
cursor.close()
conn.close()

print("Successfully injected White Goods Data into the RAG Database!")
