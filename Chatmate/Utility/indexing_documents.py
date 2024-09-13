import random
from sentence_transformers import SentenceTransformer
import faiss

from Chatmate.Utility.general_utility import generate_random_id

class Document:
    def __init__(self, id_, text):
        self.id_ = id_
        self.text = text

class DocumentChunk:
    def __init__(self, id_, chunk_id, embedding=None, text=''):
        self.id_ = id_
        self.chunk_id = chunk_id
        self.embedding = embedding
        self.text = text

# Initialize the model with proper error handling
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    raise RuntimeError(f"Error initializing the model: {str(e)}")

def chunk_text(text, chunk_size=100):
    """
    Splits text into chunks of approximately chunk_size words.
    """
    try:
        words = text.split()
        return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    except Exception as e:
        raise ValueError(f"Error chunking text: {str(e)}")

def process_documents(documents):
    """
    Processes each document into chunks and returns a list of DocumentChunk objects.
    """
    all_chunks = []
    try:
        for doc in documents:
            if "text" not in doc:
                raise KeyError(f"Document is missing the 'text' key: {doc}")
            chunks = chunk_text(doc["text"])
            for i, chunk in enumerate(chunks):
                all_chunks.append(DocumentChunk(id_=generate_random_id(), chunk_id=i, text=chunk))
    except Exception as e:
        raise RuntimeError(f"Error processing documents: {str(e)}")
    return all_chunks

def process_texts(texts):
    """
    Processes each text into chunks and returns a list of DocumentChunk objects.
    """
    all_chunks = []
    try:
        for i, text in enumerate(texts):
            chunks = chunk_text(text)
            for j, chunk in enumerate(chunks):
                all_chunks.append(DocumentChunk(id_=generate_random_id(), chunk_id=j, text=chunk))
    except Exception as e:
        raise RuntimeError(f"Error processing texts: {str(e)}")
    return all_chunks

def compute_embeddings(chunks):
    """
    Computes embeddings for each chunk and assigns them to the chunk objects.
    """
    try:
        texts = [chunk.text for chunk in chunks]
        embeddings = model.encode(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
    except Exception as e:
        raise RuntimeError(f"Error computing embeddings: {str(e)}")
    return embeddings

def create_index(embeddings):
    """
    Creates a FAISS index for the embeddings.
    """
    try:
        if len(embeddings) == 0:
            raise ValueError("No embeddings to index.")
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
    except Exception as e:
        raise RuntimeError(f"Error creating FAISS index: {str(e)}")
    return index

def retrieve_chunks(query, index, chunks, top_k=5):
    """
    Retrieves the most relevant chunks based on the query.
    """
    try:
        query_embedding = model.encode([query])
        distances, indices = index.search(query_embedding, top_k)
        
        # Retrieve the most relevant chunks based on indices
        relevant_chunks = [chunks[i] for i in indices[0]]
    except Exception as e:
        raise RuntimeError(f"Error retrieving chunks: {str(e)}")
    return relevant_chunks, distances
