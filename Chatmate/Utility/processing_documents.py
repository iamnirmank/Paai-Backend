from Chatmate.Utility.parsing_utility import document_parser, link_parser, read_file
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compare_chunks(chunk1, chunk2):
    """
    Compare two chunks based on their text fields.
    Returns True if the text fields are similar, otherwise False.
    """
    print("chunk1:: ", chunk1.get('text'))
    return chunk1.get('text') == chunk2.get('text')

def load_documents(document_ids):
    """Load documents from the database, extract text from files and links, and combine results."""
    try:
        from Chatmate.models import Documents
        # documents = Documents.objects.filter(id__in=document_ids)
        documents = Documents.objects.all()

        logger.info(f"Loaded {len(documents)} documents from the database.")

        all_chunks = []
        for doc in documents:
            if doc.file:
                try:
                    file_chunks = read_file(doc.file.path)
                    all_chunks.extend(file_chunks) 
                except Exception as e:
                    logger.error(f"Error parsing document at {doc.file.path}: {str(e)}")
            if doc.link:
                try:
                    link_chunks = link_parser(doc.link)
                    all_chunks.extend(link_chunks)
                except Exception as e:
                    logger.error(f"Error parsing links: {str(e)}")
                

        # Ensure all_chunks only contains JSON-serializable data
        all_chunks = [chunk_to_dict(chunk) for chunk in all_chunks]

        return all_chunks

    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        return []

def chunk_to_dict(chunk):
    """Convert chunk to a JSON-serializable dictionary if it's not already."""
    try:
        if isinstance(chunk, dict):
            return chunk
        elif hasattr(chunk, '__dict__'):
            return chunk.__dict__
        else:
            raise TypeError(f'Object of type {chunk.__class__.__name__} is not JSON serializable')
    except Exception as e:
        logger.error(f"Error converting chunk to dict: {str(e)}")
        return {}

def update_combined_chunks(document_ids, delete=False):
    from Chatmate.models import CombinedChunk
    try:
        print("document_ids:: ", document_ids)  
        print("delete:: ", delete)
        all_chunks = load_documents(document_ids)
        combined_chunk_instance, created = CombinedChunk.objects.get_or_create(id=1, defaults={'chunks': all_chunks})
        # print("all_chunks:: ", all_chunks)
        # print("combined_chunk_instance:: ", combined_chunk_instance.chunks)
        if delete:
            # Filter out chunks from combined_chunk_instance that are similar to any in all_chunks
            new_chunks = [
                chunk for chunk in combined_chunk_instance.chunks
                if not any(compare_chunks(chunk, ac) for ac in all_chunks)
            ]
            # print("new_chunks:: ", new_chunks)
                        
            # Update the chunks field only if there's a change
            if len(new_chunks) != len(combined_chunk_instance.chunks):
                combined_chunk_instance.chunks = new_chunks
                combined_chunk_instance.save()
                logger.info("Deleted similar chunks from combined chunks successfully.")
            else:
                logger.info("No matching chunks found for deletion.")
                
        if not created:
            combined_chunk_instance.chunks = all_chunks
            combined_chunk_instance.save()
            logger.info("Combined chunks updated successfully.")
        else:
            logger.info("Combined chunks created successfully.")
    except Exception as e:
        logger.error(f"Error updating combined chunks: {str(e)}")
