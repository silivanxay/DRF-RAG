# DRF-RAG

ລະບົບ RAG (Retrieval-Augmented Generation) ທີ່ສ້າງດ້ວຍ Django REST Framework, Ollama, Qdrant, ແລະ Celery — ໃຊ້ສຳລັບອັບໂຫລດໄຟລ໌ PDF ແລ້ວຖາມຄຳຖາມໂດຍໃຊ້ AI ທີ່ລັນຢູ່ໃນເຄື່ອງຂອງທ່ານເອງ.

---

## ສິ່ງທີ່ລະບົບສາມາດເຮັດໄດ້

- **ອັບໂຫລດ PDF**: ອັບໂຫລດໄຟລ໌ PDF ຜ່ານ REST API
- **ດຶງຂໍ້ຄວາມອັດຕະໂນມັດ**: ດຶງຂໍ້ຄວາມຈາກ PDF ປົກກະຕິ ຫຼື PDF ທີ່ເປັນຮູບພາບ (ໃຊ້ OCR ຮອງຮັບທັງ ອັງກິດ ແລະ ລາວ)
- **ຕັດຂໍ້ຄວາມເປັນ chunk**: ຕັດໄຟລ໌ PDF ເປັນສ່ວນໆ ແລ້ວ embed ດ້ວຍ Ollama
- **ເກັບໃນ Vector Store**: ບັນທຶກ embeddings ໃນ Qdrant
- **ຖາມ-ຕອບ**: ຖາມຄຳຖາມກ່ຽວກັບເນື້ອໃນໃນ PDF ແລ້ວໄດ້ຮັບຄຳຕອບຈາກ LLM ພ້ອມກັບ source chunk

---

## Tech Stack

| ສ່ວນ | ເຕັກໂນໂລຊີ |
|---|---|
| Web API | Django 4.2+, Django REST Framework |
| Task Queue | Celery 5 + Redis |
| Vector Store | Qdrant |
| LLM & Embedding | Ollama (llama3.1, nomic-embed-text) |
| PDF Parsing | PyMuPDF (ຮອງຮັບ OCR ພາສາລາວ) |
| API Docs | drf-spectacular (OpenAPI/Swagger) |
| Database | SQLite |

---

## ຂໍ້ກຳນົດກ່ອນຕິດຕັ້ງ

- Python 3.11+
- [Ollama](https://ollama.com) ລັນຢູ່ `localhost:11434`
- [Qdrant](https://qdrant.tech) ລັນຢູ່ `localhost:6333`
- Redis ລັນຢູ່ `localhost:6379`

### ດາວໂຫລດ model Ollama

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

---

## ການຕິດຕັ້ງ

### 1. Clone ໂປຣເຈັກ

```bash
git clone <repo-url>
cd DRF-RAG
```

### 2. ສ້າງ virtual environment ແລ້ວຕິດຕັ້ງ dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. ຕັ້ງຄ່າ environment variables

```bash
cp .env.example .env
```

ແກ້ໄຟລ໌ `.env` ແລ້ວໃສ່ຄ່າ:

```env
SECRET_KEY=your-secret-key-here   # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

CELERY_BROKER_URL=redis://localhost:6379/0

QDRANT_HOST=localhost
QDRANT_PORT=6333

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### 4. ລັນ database migration

```bash
python manage.py migrate
```

---

## ການລັນໂປຣເຈັກ

ຕ້ອງການ 3 terminal ທີ່ລັນພ້ອມກັນ:

**Terminal 1 — Django server**
```bash
python manage.py runserver
```

**Terminal 2 — Celery worker**
```bash
celery -A config worker -l info
```

**Terminal 3 — Qdrant** (ຖ້າໃຊ້ Docker)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

## API Endpoints

| Method | URL | ຄຳອະທິບາຍ |
|---|---|---|
| `POST` | `/api/documents/ingest/` | ອັບໂຫລດ PDF ແລ້ວເລີ່ມ ingest |
| `GET` | `/api/documents/` | ລາຍການ document ທັງໝົດ |
| `GET` | `/api/documents/<id>/` | ລາຍລະອຽດ document ດຽວ |
| `POST` | `/api/query/` | ຖາມຄຳຖາມກ່ຽວກັບ document |
| `GET` | `/api/schema/swagger-ui/` | Swagger UI |
| `GET` | `/api/schema/redoc/` | ReDoc |

---

## ຕົວຢ່າງການໃຊ້ງານ

### ອັບໂຫລດ PDF

```bash
curl -X POST http://localhost:8000/api/documents/ingest/ \
  -F "file=@/path/to/document.pdf" \
  -F "collection_name=documents"
```

ຈະໄດ້ຮັບ response ແບບນີ້ (status 202):

```json
{
  "id": 1,
  "filename": "document.pdf",
  "status": "pending",
  "chunk_count": 0,
  "created_at": "2026-06-10T10:00:00Z"
}
```

### ກວດສອບສະຖານະ

```bash
curl http://localhost:8000/api/documents/1/
```

```json
{
  "id": 1,
  "filename": "document.pdf",
  "status": "done",
  "chunk_count": 42
}
```

### ຖາມຄຳຖາມ

```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ໃນເອກະສານນີ້ມີເນື້ອໃນກ່ຽວກັບຫຍັງ?",
    "collection_name": "documents",
    "top_k": 5
  }'
```

```json
{
  "answer": "...",
  "sources": [
    {
      "page_content": "...",
      "source": "/path/to/document.pdf",
      "page": 1
    }
  ]
}
```

---

## ໂຄງສ້າງໂຟລເດີ

```
DRF-RAG/
├── config/             # Django settings, URLs, Celery config
├── documents/          # ແອັບ upload + ingest PDF
│   ├── models.py       # Document model (status tracking)
│   ├── views.py        # IngestView, DocumentListView, DocumentDetailView
│   ├── tasks.py        # Celery task: ດຶງຂໍ້ຄວາມ, embed, ບັນທຶກ Qdrant
│   └── serializers.py
├── query/              # ແອັບ RAG query
│   ├── views.py        # QueryView: ຖາມ-ຕອບດ້ວຍ LLM
│   └── serializers.py
├── templates/          # Minimal HTML template
├── media/uploads/      # ໄຟລ໌ PDF ທີ່ອັບໂຫລດ
├── .env.example        # ຕົວຢ່າງ environment variables
├── requirements.txt
└── manage.py
```

---

## ໝາຍເຫດ

- ໄຟລ໌ PDF ທີ່ເປັນຮູບພາບ (scanned) ຈະໃຊ້ OCR ອັດຕະໂນມັດ ຮອງຮັບທັງພາສາ **ອັງກິດ** ແລະ **ລາວ**
- ສະຖານະ document ມີ 4 ຂັ້ນຕອນ: `pending` → `processing` → `done` / `failed`
- ສາມາດໃຊ້ collection ຫຼາຍອັນເພື່ອແຍກ document ຕ່າງໆ ອອກຈາກກັນ
