import logging
import fitz  # PyMuPDF
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def ingest_document(
    self, document_id: int, file_path: str, collection_name: str
):
    from .models import Document
    from langchain_community.document_loaders import PyMuPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_ollama import OllamaEmbeddings
    from langchain_qdrant import QdrantVectorStore
    from langchain_core.documents import Document as LCDocument
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    doc = Document.objects.get(pk=document_id)
    doc.status = Document.Status.PROCESSING
    doc.save(update_fields=["status", "updated_at"])

    try:
        # 1. Load PDF
        loader = PyMuPDFLoader(file_path)
        pages = loader.load()

        total_text = sum(len(p.page_content.strip()) for p in pages)
        logger.info(
            "PDF loaded: %d pages, %d chars total", len(pages), total_text
        )

        # 2. OCR fallback for scanned / image-only PDFs
        if total_text == 0:
            logger.info("No text layer found — falling back to OCR")
            pdf = fitz.open(file_path)
            pages = []
            for i, page in enumerate(pdf):
                ocr_text = (
                    page.get_textpage_ocr(flags=0, language="eng+lao")
                    .extractText()
                )
                if ocr_text.strip():
                    pages.append(LCDocument(
                        page_content=ocr_text,
                        metadata={"source": file_path, "page": i},
                    ))
            pdf.close()
            total_text = sum(len(p.page_content.strip()) for p in pages)
            logger.info(
                "OCR extracted %d chars from %d pages",
                total_text,
                len(pages),
            )

        if not pages:
            raise ValueError(
                "Could not extract any text from the PDF "
                "(text layer and OCR both empty)."
            )

        # 3. Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )
        chunks = splitter.split_documents(pages)

        if not chunks:
            raise ValueError(
                "PDF text was extracted but produced 0 chunks after splitting."
            )

        # 4. Embed
        embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

        # 5. Upsert into Qdrant
        client = QdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )

        existing = [c.name for c in client.get_collections().collections]
        if collection_name not in existing:
            sample_vector = embeddings.embed_query("test")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=len(sample_vector), distance=Distance.COSINE
                ),
            )

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=collection_name,
            embedding=embeddings,
        )
        vector_store.add_documents(chunks)

        doc.status = Document.Status.DONE
        doc.chunk_count = len(chunks)
        doc.save(update_fields=["status", "chunk_count", "updated_at"])
        logger.info(
            "Ingested %d chunks for document %d", len(chunks), document_id
        )

    except Exception as exc:
        logger.exception("Ingestion failed for document %d", document_id)
        doc.status = Document.Status.FAILED
        doc.error_message = str(exc)
        doc.save(update_fields=["status", "error_message", "updated_at"])
        raise
