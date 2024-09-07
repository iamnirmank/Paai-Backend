import os
import numpy as np
import faiss
import logging

from Chatmate.Utility.groq_response import generate_response_with_llama
from Chatmate.Utility.indexing_documents import compute_embeddings, create_index, process_documents, process_texts, retrieve_chunks
from Chatmate.models import CombinedChunk, Query, Rooms

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_query(query, room_name):
    """Process a user query by retrieving relevant documents and generating a response."""
    try:
        context = context_extraction(query, room_name)
        previous_context = process_history(room_name)
        additional_note = (
            "Provide a detailed and thorough answer. "
            "Use a natural and conversational tone, "
            "and ensure the response feels engaging and human-like."
        )
        combined_input = (
            f"Context: {context}\n\n"
            f"Chat History: {previous_context}\n\n"
            f"Question: {query}\n\n"
            f"Additional Note: {additional_note}\n\n"
            "Answer:"
        )
        response = generate_response_with_llama(combined_input)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        response = "An error occurred while processing your query. Please try again later."
    return response


def context_extraction(query, room_name):
    """Index the documents into Milvus using LlamaIndex."""
    try:
        chunk = CombinedChunk.objects.get(room=room_name).chunks
        if not chunk:
            return "No documents found."
        chunks = process_documents(chunk)
        embeddings = compute_embeddings(chunks)
        index = create_index(np.array(embeddings))
        faiss.write_index(index, "chunks_index.faiss")

        index = faiss.read_index("chunks_index.faiss")
        relevant_chunks, distances = retrieve_chunks(query, index, chunks)

        os.remove("chunks_index.faiss")

        context = "\n".join([chunk.text for chunk in relevant_chunks])
    except CombinedChunk.DoesNotExist:
        logger.warning("CombinedChunk with id=1 does not exist.")
        context = "No documents found."
    except Exception as e:
        logger.error(f"Error extracting context: {e}")
        context = "An error occurred while extracting context."
    return context

def process_history(room_name):
    """Process the chat history to extract the context."""
    try:
        prev_queries = Query.objects.filter(room=room_name)
        if not prev_queries.exists():
            return "No chat history found."
        chats = []

        for query in prev_queries:
            chats.append(query.query_text + "\n" + query.response_text)
        
        chunks = process_texts(chats)
        embeddings = compute_embeddings(chunks)
        index = create_index(np.array(embeddings))
        faiss.write_index(index, "history_index.faiss")

        index = faiss.read_index("history_index.faiss")
        relevant_chunks, distances = retrieve_chunks("", index, chunks)

        os.remove("history_index.faiss")

        context = "\n".join([chunk.text for chunk in relevant_chunks])
    except Exception as e:
        logger.error(f"Error processing history: {e}")
        context = "An error occurred while processing chat history."
    return context
