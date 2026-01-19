# Swasthya – Personal Health Memory System

**Hackathon:** Convolve 4.0 – Pan-IIT AI/ML Hackathon  
**Category:** Search, Memory, and Recommendations for Societal Impact  
**Team:** [Your Team Name]  
**Version:** 1.0  

---

## 1. Problem Statement

Individuals often lose access to past medical information — prescriptions, lab reports, vaccination history, and vitals — across multiple healthcare visits. This results in:  

- Repeated tests  
- Incomplete medical history  
- Poor continuity of care  

**Challenge:** Enable users to **store, retrieve, and reason over long-term health data** across time and multiple formats, including text and images, while maintaining privacy and explainability.  

**Impact:** Improves healthcare continuity, reduces redundant testing, and empowers individuals with control over their health information.

---

## 2. Proposed Solution

**Swasthya** is a **personal health memory system** that allows users to:  

1. Upload prescriptions and medical reports (**PDF or image**)  
2. Record vitals (weight, height, blood pressure, etc.)  
3. Retrieve past records with **natural language queries**  
4. View trends (weight over time, vitals history)  
5. Perform **semantic search** across all stored data  

**Core Tech:**  
- **Qdrant**: Long-term vector memory engine  
- **SentenceTransformers**: Embeddings for text and OCRed image text  
- **FastAPI**: Backend server  
- **pypdf & pytesseract**: Extract text from PDFs and images  

---

## 3. System Architecture
                   +------------------------+
                   |    User Interface      |
                   |  (Swagger / Postman)   |
                   +-----------+------------+
                               |
                               v
                   +------------------------+
                   |     FastAPI Backend    |
                   +-----------+------------+
                               |
          -----------------------------------------
          |                                       |
          v                                       v
  +----------------+                     +----------------+
  | PDF Upload /   |                     | Image Upload / |
  | Prescription   |                     | Reports        |
  |   Processing   |                     |   Processing   |
  |   (pypdf OCR)  |                     | (pytesseract) |
  +--------+-------+                     +--------+-------+
           |                                      |
           | OCR Extracted Text                    | OCR Extracted Text
           +--------------------------------------+
                               |
                               v
                  +------------------------+
                  |  SentenceTransformer   |
                  |   (Text Embeddings)    |
                  +-----------+------------+
                              |
                              v
                  +------------------------+
                  |       Qdrant DB        |
                  |  (Vector Memory + Meta)|
                  +-----------+------------+
                              |
           -------------------------------------------
           |                 |                      |
           v                 v                      v
     Semantic Search      Trend Analysis       Evidence-Based
      (/ask endpoint)      (/trend endpoint)       Answers


---

## 4. Multimodal Strategy

| Data Type           | Handling Method                             |
|--------------------|--------------------------------------------|
| PDF prescriptions   | pypdf → text → embeddings                   |
| Images (prescriptions/reports) | pytesseract OCR → text → embeddings      |
| Vitals (weight, height, BP) | Query → text → embeddings                    |

- All embeddings stored **with metadata**: type, date, metric  
- Enables **semantic + time-aware search**  
- Multimodal support ensures both text and images are searchable  

---

## 5. Search, Memory, and Recommendation Logic

### Search
- **Semantic search** using vector similarity  
- Queries vectorized → matched with stored embeddings in Qdrant  
- Returns top 5 most relevant records  

### Memory
- **Persistent storage** in Qdrant  
- Records stored with timestamp, type, and metric  
- Supports evolving memory (e.g., weight changes over time)  

### Recommendations
- Trends generated (weight history, vitals patterns)  
- Evidence-based insights from retrieved records  
- No hallucination: answers always grounded in stored user data  

---

## 6. Ethical Considerations

- **No medical diagnosis**: Swasthya is a decision-support tool  
- **Privacy**: User data stored locally or securely; not shared  
- **Explainable AI**: All responses traceable to stored records  
- **Bias handling**: Only uses user’s own data, avoids external assumptions  

---

## 7. Expected Outcome / Demo

- Upload prescriptions and vitals  
- Query past medical data via `/ask`  
- View trends, e.g., `/trend/weight`  
- Retrieve **image-based prescriptions**  

**Example Response:**

```json
{
  "question": "What medicines am I taking?",
  "retrieved_records": [
    {
      "type": "prescription",
      "content": "Paracetamol 500mg, 1 tablet twice a day",
      "score": 0.91
    }
  ]
}
