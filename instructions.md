# Swasthya – Personal Health Memory System

## Instructions to Run the Application

### 1️⃣ Prerequisites

Make sure you have the following installed:

- **Python 3.11+**  
- **pip** (Python package manager)  
- **Qdrant** vector database (local or Docker)  
- **Tesseract OCR** for image text extraction  
  - [Install Tesseract](https://github.com/tesseract-ocr/tesseract)  
- Optional: **Git** to clone repository

---

### 2️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd Swasthya/backend

# Swasthya – Personal Health Memory System

## 3️⃣ Create a Virtual Environment (Recommended)
```bash
python -m venv venv
```
Activate the environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / Mac:**
```bash
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
**Dependencies include:**
- `fastapi` – API framework  
- `uvicorn` – ASGI server  
- `qdrant-client` – Qdrant vector database client  
- `sentence-transformers` – Embedding model  
- `pypdf` – PDF text extraction  
- `pillow` – Image processing  
- `pytesseract` – OCR for images  

---

## 5️⃣ Start Qdrant Server
Qdrant can be started **locally** or via **Docker**.

### Option 1: Local installation
Run Qdrant on `localhost:6333`

### Option 2: Docker
```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

## 6️⃣ Start the FastAPI Backend
From the `backend` directory:
```bash
uvicorn main:app --reload
```
- Backend runs at: `http://127.0.0.1:8000`  
- Swagger UI (for visual API testing): `http://127.0.0.1:8000/docs`  

---

## 7️⃣ Using the Application

### 7.1 Upload Prescription (PDF or Image)
**Endpoint:** `POST /upload/prescription`
- Supported file types: `.pdf`, `.jpg`, `.jpeg`, `.png`  
- Stores the prescription in semantic memory  
- Returns: status, modality (PDF/Image), number of characters saved  

---

### 7.2 Upload Lab Report / Scan (Image)
**Endpoint:** `POST /upload/report`
- Supports image files only  
- Performs OCR to extract text  
- Stores extracted text as semantic memory  

---

### 7.3 Add Health Vitals
**Endpoint:** `POST /add/vitals?weight=56&height=136&blood_pressure=120/80`
- Stores weight, height, and blood pressure as **long-term memory**  
- Automatically timestamped  

---

### 7.4 Add Child Vaccination Record
**Endpoint:** `POST /add/vaccine?child_name=John&vaccine_name=BCG&date=2026-01-20`
- Adds vaccination date for a child  
- System automatically calculates **pending vaccinations** based on standard schedules  

---

### 7.5 Ask / Semantic Search
**Endpoint:** `POST /ask?question=what is my weight`
- Converts user query to a semantic vector  
- Retrieves top 5 relevant records (prescriptions, reports, vitals, vaccinations)  
- Returns: type, modality, content, and similarity score  

---

### 7.6 View All Stored Records
**Endpoint:** `GET /memory/all`
- Returns all stored records with previews  
- Includes type and modality for each record  

---

### 7.7 Weight Trend
**Endpoint:** `GET /trend/weight`
- Returns a chronological list of recorded weights  
- Useful for tracking personal health trends  

---

## 8️⃣ Notes & Tips
- **Tesseract OCR:** Ensure the executable path is correctly set in your environment if needed  
- **PDF quality:** Text extraction works best with digitally generated PDFs. Handwritten PDFs may fail OCR  
- **Image clarity:** Blurry or low-resolution images reduce OCR accuracy  
- **Testing:** Use Swagger UI `/docs` to interact with endpoints without building a separate frontend  
- **Vaccination schedule:** Can be expanded or localized based on country-specific immunization guidelines  

---

## 9️⃣ Recommended Workflow
1. Start Qdrant server  
2. Start FastAPI backend  
3. Upload prescriptions and reports  
4. Add health vitals  
5. Add child vaccination records  
6. Query your health data using `/ask` or check trends using `/trend/weight`  
7. View all stored records with `/memory/all`  

---

## 10️⃣ Example Endpoints Summary
| Endpoint                  | Method | Description                                |
|----------------------------|--------|--------------------------------------------|
| `/upload/prescription`     | POST   | Upload PDF/Image prescription             |
| `/upload/report`           | POST   | Upload lab report image                    |
| `/add/vitals`              | POST   | Add health vitals (weight, height, BP)    |
| `/add/vaccine`             | POST   | Add child vaccination record               |
| `/ask`                     | POST   | Semantic search of stored health data     |
| `/memory/all`              | GET    | View all stored records                    |
| `/trend/weight`            | GET    | Retrieve weight trend                      |

---


