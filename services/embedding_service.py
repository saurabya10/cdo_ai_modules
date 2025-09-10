import os
import chromadb
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from chromadb.utils import embedding_functions
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, config):
        self.config = config
        self.persist_directory = self.config.embedding.persist_directory
        self.collection_name = self.config.embedding.collection_name
        self.embedding_model = self.config.embedding.model
        self.source_directory = self.config.embedding.source_directory

    def _load_documents(self):
        docs = []
        logger.info(f"Loading documents from source directory: {self.source_directory}")
        if not os.path.exists(self.source_directory):
            logger.error(f"Source directory not found: {self.source_directory}")
            return docs

        for root, _, files in os.walk(self.source_directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if file.endswith(".pdf"):
                        logger.info(f"Loading PDF file: {file_path}")
                        loader = PyPDFLoader(file_path)
                        docs.extend(loader.load())
                    elif file.endswith(".txt"):
                        logger.info(f"Loading text file: {file_path}")
                        loader = TextLoader(file_path, encoding='utf-8')
                        docs.extend(loader.load())
                except Exception as e:
                    logger.error(f"Failed to load document {file_path}: {e}")
        
        logger.info(f"Loaded {len(docs)} documents.")
        return docs

    def _split_text(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)
        return chunks

    def create_and_store_embeddings(self):
        docs = self._load_documents()
        if not docs:
            logger.warning(f"No documents found in source directory: {self.source_directory}. Skipping embedding creation.")
            return

        chunks = self._split_text(docs)
        if not chunks:
            logger.warning("Document splitting resulted in no chunks. Skipping embedding creation.")
            return
        
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
        )
        
        client = chromadb.PersistentClient(path=self.persist_directory)
        collection = client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_function,
        )
        
        texts = [c.page_content for c in chunks]
        metadatas = [c.metadata for c in chunks]
        ids = [str(i) for i in range(len(texts))]
        
        collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def get_retriever(self, n_results=5):
        langchain_embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        client = chromadb.PersistentClient(path=self.persist_directory)
        
        langchain_chroma = Chroma(
            client=client,
            collection_name=self.collection_name,
            embedding_function=langchain_embeddings,
        )
        return langchain_chroma.as_retriever(
            search_type="similarity_score_threshold", 
            search_kwargs={"k": 10, "score_threshold": 0.2}
        )

if __name__ == '__main__':
    from cdo_ai_modules.config import load_config
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    
    config = load_config()
    embedding_service = EmbeddingService(config)
    embedding_service.create_and_store_embeddings()
    retriever = embedding_service.get_retriever()
    retrieved_docs = retriever.invoke("How to troubleshoot SAL logs?")
    print(f"\nFound {len(retrieved_docs)} relevant documents:\n")
    for i, doc in enumerate(retrieved_docs):
        print(f"--- Result {i+1} ---")
        print(f"Content: {doc.page_content[:500]}...")
        if doc.metadata:
            print(f"Metadata: {doc.metadata}")
        print("-" * 20 + "\n")
