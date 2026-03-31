import openai
import ast
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from core.knowledge_graph.knowledgeGraph import KnowledgeGraph
from core.openai_model import default_chat_model

def extract_triples_from_text(text: str, openai_key: str, 
                             doc_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str, str]]:
    """
    Extract subject-predicate-object triples from text using OpenAI.
    
    Args:
        text: The text to extract triples from
        openai_key: OpenAI API key
        doc_metadata: Optional document metadata to include in the prompt
        
    Returns:
        List of (subject, predicate, object) tuples
    """
    openai.api_key = openai_key
    
    # Include document metadata in the prompt if available
    metadata_str = ""
    if doc_metadata:
        metadata_str = "Document metadata:\n"
        for k, v in doc_metadata.items():
            metadata_str += f"- {k}: {v}\n"
    
    prompt = f"""
You are an information extraction agent. From the following text, extract all relevant factual relationships and output them as subject-predicate-object triples.

{metadata_str}
Text:
{text}

Output format (Python list of tuples):
[("subject1", "predicate1", "object1"), ("subject2", "predicate2", "object2"), ...]
Only output valid Python list syntax. No explanations.
"""

    try:
        response = openai.ChatCompletion.create(
            model=default_chat_model(),
            messages=[
                {"role": "system", "content": "You extract structured triples from text."},
                {"role": "user", "content": prompt}
            ]
        )
        
        triples_text = response['choices'][0]['message']['content'].strip()
        
        try:
            return ast.literal_eval(triples_text)
        except Exception as e:
            print("Triple parsing error:", e)
            print("Raw response:", triples_text)
            return []
            
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return []

def ingest_triples_into_kg(triples, source="openai", doc_id="unknown", 
                          doc_metadata=None) -> KnowledgeGraph:
    """
    Add extracted triples to a knowledge graph.
    
    Args:
        triples: List of (subject, predicate, object) tuples
        source: Source of the triples
        doc_id: Document identifier
        doc_metadata: Additional document metadata
        
    Returns:
        Updated knowledge graph
    """
    kg = KnowledgeGraph()
    extracted_at = datetime.utcnow().isoformat()
    
    # Create metadata dictionary
    metadata = {
        "extracted_at": extracted_at,
        "doc_id": doc_id,
    }
    
    # Add document metadata if available
    if doc_metadata:
        for k, v in doc_metadata.items():
            metadata[f"doc_{k}"] = v
    
    for subj, pred, obj in triples:
        # Try to infer entity types based on predicate
        subject_type = infer_entity_type(subj, pred, "subject")
        object_type = infer_entity_type(obj, pred, "object")
        
        kg.add_relation(
            subj, pred, obj,
            subject_type=subject_type,
            object_type=object_type,
            confidence=1.0,
            source=source,
            metadata=metadata
        )
    
    return kg

def infer_entity_type(entity: str, predicate: str, position: str) -> str:
    """
    Attempt to infer entity type based on predicate and position.
    This is a simple heuristic and could be improved with ML.
    
    Args:
        entity: The entity text
        predicate: The relation predicate
        position: Either "subject" or "object"
        
    Returns:
        Inferred entity type
    """
    # Simple heuristics - could be expanded
    if predicate in ["is a", "is an", "type of", "instance of"] and position == "object":
        return "Class"
    
    if predicate in ["located in", "based in"] and position == "object":
        return "Location"
        
    if predicate in ["created by", "authored by"] and position == "object":
        return "Person"
        
    if predicate in ["founded", "created", "developed"] and position == "subject":
        return "Organization"
    
    # Default fallback
    return "Entity"
