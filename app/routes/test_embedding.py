from app.services.embeddings import generate_embedding 
import numpy as np
 

text1 = "forget my password."
text2 = "reset my password."
text3 = "what is the weather today?"

emd1 = generate_embedding(text1)
emd2 = generate_embedding(text2)
emd3 = generate_embedding(text3)


def cosine_similarity(a,b):
    return np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b))

print("Similarity (1 vs 2):", cosine_similarity(emd1, emd2))
print("Similarity (1 vs 3):", cosine_similarity(emd1, emd3))
print("Similarity (2 vs 3):", cosine_similarity(emd2, emd3))
