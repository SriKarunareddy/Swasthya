from fastapi import FastAPI, UploadFile, File, Query
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
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
# UNIVERSAL PRESCRIPTION UPLOAD (PDF + IMAGE)
# -------------------------
@app.post("/upload/prescription")
async def upload_prescription(file: UploadFile = File(...)):
    try:
        extracted_text = ""
        filename = file.filename.lower()

        # -------- PDF --------
        if filename.endswith(".pdf"):
            pdf_bytes = await file.read()
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text
            modality = "pdf"

        # -------- IMAGE --------
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file.file).convert("RGB")
            extracted_text = pytesseract.image_to_string(image)
            modality = "image"

        else:
            return {"error": "Unsupported file type"}

        if not extracted_text.strip():
            return {"error": "No readable text found"}

        vector = model.encode(extracted_text).tolist()

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "type": "prescription",
                    "modality": modality,
                    "content": extracted_text,
                    "uploaded_at": datetime.now().isoformat()
                }
            }]
        )

        return {
            "status": "Prescription stored successfully",
            "modality": modality,
            "characters_saved": len(extracted_text)
        }

    except errors.PdfReadError:
        return {"error": "Invalid or corrupted PDF"}
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# IMAGE REPORT UPLOAD (LAB REPORTS / SCANS)
# -------------------------
@app.post("/upload/report")
async def upload_report(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            return {"error": "No readable text found in image"}

        vector = model.encode(extracted_text).tolist()

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "type": "report",
                    "modality": "image",
                    "content": extracted_text,
                    "uploaded_at": datetime.now().isoformat()
                }
            }]
        )

        return {"status": "Report stored successfully"}

    except Exception as e:
        return {"error": str(e)}

# -------------------------
# ADD HEALTH VITALS
# -------------------------
@app.post("/add/vitals")
def add_vitals(
    weight: float = Query(None),
    height: float = Query(None),
    blood_pressure: str = Query(None)
):
    today = datetime.now().date().isoformat()

    entries = []
    if weight:
        entries.append(("weight", f"Weight recorded: {weight} kg on {today}"))
    if height:
        entries.append(("height", f"Height recorded: {height} cm on {today}"))
    if blood_pressure:
        entries.append(("bp", f"Blood Pressure recorded: {blood_pressure} on {today}"))

    for metric, text in entries:
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

    return {"status": "Vitals stored as long-term memory"}

# -------------------------
# WEIGHT TREND
# -------------------------
@app.get("/trend/weight")
def weight_trend():
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

    return {
        "metric": "weight",
        "history": history,
        "insight": "Retrieved from long-term personal health memory"
    }

# -------------------------
# ASK / SEMANTIC SEARCH
# -------------------------

# -------------------------
# CHILD VACCINATION UPLOAD (PDF + IMAGE)
# -------------------------
# -------------------------
# ADD CHILD VACCINATION (STRUCTURED MEMORY)
# -------------------------
@app.post("/add/vaccination")
def add_vaccination(
    child_name: str = Query(...),
    dob: str = Query(..., description="Child DOB in YYYY-MM-DD"),
    vaccine_name: str = Query(...),
    vaccination_date: str = Query(..., description="YYYY-MM-DD")
):
    try:
        dob_date = datetime.fromisoformat(dob).date()
        vac_date = datetime.fromisoformat(vaccination_date).date()

        age_months = (vac_date.year - dob_date.year) * 12 + (vac_date.month - dob_date.month)

        text = (
            f"Child {child_name} received {vaccine_name} vaccine "
            f"at age {age_months} months on {vaccination_date}"
        )

        vector = model.encode(text).tolist()

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": str(uuid.uuid4()),
                "vector": vector,
                "payload": {
                    "type": "vaccination",
                    "child_name": child_name,
                    "vaccine": vaccine_name,
                    "age_months": age_months,
                    "date": vaccination_date,
                    "content": text
                }
            }]
        )

        return {
            "status": "Vaccination recorded",
            "child": child_name,
            "vaccine": vaccine_name,
            "age_months": age_months
        }

    except Exception as e:
        return {"error": str(e)}



@app.post("/ask")
def ask_question(question: str = Query(...)):
    query_vector = model.encode(question).tolist()

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        with_payload=True,
        limit=5
    )

    if not result.points:
        return {"question": question, "answer": "No relevant records found"}

    retrieved = [{
        "type": p.payload.get("type"),
        "modality": p.payload.get("modality"),
        "content": p.payload.get("content"),
        "score": p.score
    } for p in result.points]

    return {
        "question": question,
        "retrieved_records": retrieved,
        "explanation": "Results retrieved using semantic vector similarity from stored health memory"
    }

# -------------------------
# VIEW ALL MEMORY
# -------------------------
@app.get("/memory/all")
def get_all_memory():
    points, _ = client.scroll(collection_name=COLLECTION_NAME, limit=100)

    return {
        "total_records": len(points),
        "records": [
            {
                "id": p.id,
                "type": p.payload.get("type"),
                "modality": p.payload.get("modality"),
                "preview": p.payload.get("content")[:200]
            }
            for p in points
        ]
    }
