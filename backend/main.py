from fastapi import FastAPI, UploadFile, File, Query
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from qdrant_client.http.models import SearchRequest
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader, errors
from PIL import Image
import pytesseract
import uuid
from datetime import datetime
from io import BytesIO

# -------------------------
# APP CONFIG
# -------------------------
app = FastAPI(
    title="Swasthya – Personal Health Memory System",
    description="A vector-based personal health memory and retrieval system",
    version="1.0.0"
)

# -------------------------
# QDRANT + MODEL SETUP
# -------------------------
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "health_memory"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# CREATE COLLECTION ON START
# -------------------------
@app.on_event("startup")
def startup_event():
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

# -------------------------
# ROOT CHECK
# -------------------------
@app.get("/")
def root():
    return {"message": "Swasthya backend is running", "status": "OK"}

# -------------------------
# PDF UPLOAD (PRESCRIPTIONS / REPORTS)
# -------------------------
@app.post("/upload/prescription")
async def upload_prescription(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        reader = PdfReader(BytesIO(pdf_bytes))
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text

        if not extracted_text.strip():
            return {"error": "No readable text found in PDF"}

        vector = model.encode(extracted_text).tolist()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "type": "prescription",
                    "content": extracted_text,
                    "uploaded_at": datetime.now().isoformat()
                }
            }]
        )
        return {"status": "Prescription stored successfully", "characters_saved": len(extracted_text)}

    except errors.PdfReadError:
        return {"error": "Invalid or corrupted PDF file"}
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# IMAGE UPLOAD (REPORTS / SCANS)
# -------------------------
@app.post("/upload/report")
async def upload_report(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            return {"error": "No text found in image"}

        vector = model.encode(extracted_text).tolist()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "type": "report",
                    "content": extracted_text,
                    "uploaded_at": datetime.now().isoformat()
                }
            }]
        )
        return {"status": "Report stored successfully", "characters_saved": len(extracted_text)}

    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}"}

# -------------------------
# ADD HEALTH VITALS
# -------------------------
@app.post("/add/vitals")
def add_vitals(
    weight: float = Query(None),
    height: float = Query(None),
    blood_pressure: str = Query(None)
):
    try:
        records = []
        today = datetime.now().date().isoformat()

        if weight:
            records.append(("weight", f"Weight recorded: {weight} kg on {today}"))
        if height:
            records.append(("height", f"Height recorded: {height} cm on {today}"))
        if blood_pressure:
            records.append(("bp", f"Blood Pressure recorded: {blood_pressure} on {today}"))

        for metric, text in records:
            vector = model.encode(text).tolist()
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[{
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {
                        "type": "vitals",
                        "metric": metric,
                        "content": text,
                        "date": today
                    }
                }]
            )
        return {"status": "Vitals stored as time-aware memory"}
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# WEIGHT TREND
# -------------------------
@app.get("/trend/weight")
def weight_trend():
    try:
        points, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter={
                "must": [
                    {"key": "type", "match": {"value": "vitals"}},
                    {"key": "metric", "match": {"value": "weight"}}
                ]
            },
            limit=50
        )
        if not points:
            return {"message": "No weight records found"}

        history = sorted(
            [{"date": p.payload["date"], "record": p.payload["content"]} for p in points],
            key=lambda x: x["date"]
        )

        return {"metric": "weight", "history": history, "insight": "Weight history retrieved from long-term memory"}
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# SEMANTIC SEARCH / ASK QUESTIONS
# -------------------------
@app.post("/ask")
def ask_question(question: str = Query(..., description="Ask about your health records")):
    try:
        query_vector = model.encode(question).tolist()

        # Qdrant query API
        result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            with_payload=True,
            limit=5
        )

        points = result.points

        if not points:
            return {"question": question, "answer": "No relevant health records found"}

        retrieved_data = []
        for p in points:
            retrieved_data.append({
                "type": p.payload.get("type"),
                "content": p.payload.get("content"),
                "score": p.score
            })

        return {"question": question, "retrieved_records": retrieved_data}

    except Exception as e:
        return {"error": str(e)}

# -------------------------
# VIEW ALL STORED RECORDS
# -------------------------
@app.get("/memory/all")
def get_all_memory():
    try:
        points = client.scroll(collection_name=COLLECTION_NAME, limit=100)[0]
        return {
            "total_records": len(points),
            "records": [
                {"id": p.id, "type": p.payload.get("type"), "content_preview": p.payload.get("content")[:200]}
                for p in points
            ]
        }
    except Exception as e:
        return {"error": str(e)}
