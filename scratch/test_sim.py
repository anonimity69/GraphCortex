from graph_cortex.config.embedding import encode
import numpy as np

def _cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = np.dot(a, b)
    return float(dot / (np.linalg.norm(a) * np.linalg.norm(b)))

v1 = encode("Btw where did jason store his keys?")
v2 = encode("Jason")
v3 = encode("keys")
v4 = encode("Orilona")
v5 = encode("box")

print("Jason:", _cosine_similarity(v1, v2))
print("keys:", _cosine_similarity(v1, v3))
print("Orilona:", _cosine_similarity(v1, v4))
print("box:", _cosine_similarity(v1, v5))
