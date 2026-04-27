from sentence_transformers import SentenceTransformer


_model = None


def _get_model():
    """Lazily load the model on first use to avoid timeout during app startup."""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def generate_embeddings(texts):
    model = _get_model()
    embeddings=model.encode(texts, batch_size=32, show_progress_bar=False)
    return embeddings.tolist()
    # return model.encode(texts, batch_size=32, show_progress_bar=False).tolist()


def generate_embedding_batch(texts: list):
    """Generate embeddings with multiprocessing for large batches."""
    # model = _get_model()
    # # Agar text bohot zyada hai to pool use kiya hai, warna normal encode
    # if len(texts) > 100:
    #     pool = model.start_multi_process_pool()
    #     embeddings = model.encode_multi_process(texts, pool, batch_size=64)
    #     model.stop_multi_process_pool(pool)
    #     return embeddings.tolist()
    # else:
    #     # Choti files ke liye normal encode
    #     return model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    return generate_embeddings(texts)


def generate_embedding(text: str):
    return generate_embeddings([text])[0]

 
