from sentence_transformers import SentenceTransformer


model=SentenceTransformer('all-MiniLM-L6-v2')

def generate_embeddings(texts):
    return model.encode(texts).tolist()


def generate_embedding_batch(texts: list):
    return model.encode(texts).tolist()


def generate_embedding(text: str):
    return generate_embeddings([text])[0]

 
