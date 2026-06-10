from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from drf_spectacular.utils import extend_schema

from .serializers import QueryRequestSerializer, QueryResponseSerializer


class QueryView(APIView):
    @extend_schema(
        request=QueryRequestSerializer,
        responses={200: QueryResponseSerializer},
        summary="Query the RAG system",
        description="Ask a question against an ingested Qdrant collection. Returns an answer and source chunks.",
    )
    def post(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        collection_name = serializer.validated_data["collection_name"]
        top_k = serializer.validated_data["top_k"]

        from langchain_ollama import OllamaEmbeddings, OllamaLLM
        from langchain_qdrant import QdrantVectorStore
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough, RunnableParallel

        embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        llm = OllamaLLM(
            model=settings.OLLAMA_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

        vector_store = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            collection_name=collection_name,
        )
        retriever = vector_store.as_retriever(search_kwargs={"k": top_k})

        prompt = PromptTemplate.from_template(
            "Use the following context to answer the question.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = RunnableParallel(
            context=retriever,
            question=RunnablePassthrough(),
        ).assign(answer=lambda x: (prompt | llm | StrOutputParser()).invoke(
            {"context": format_docs(x["context"]), "question": x["question"]}
        ))

        result = chain.invoke(question)
        answer = result["answer"]
        source_docs = result["context"]

        sources = [
            {
                "page_content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "page": doc.metadata.get("page", 0),
            }
            for doc in source_docs
        ]

        response_data = {"answer": answer, "sources": sources}
        return Response(QueryResponseSerializer(response_data).data, status=status.HTTP_200_OK)
