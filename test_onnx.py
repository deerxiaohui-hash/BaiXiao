import onnxruntime
print(f"onnxruntime version: {onnxruntime.__version__}")

import chromadb
print(f"chromadb version: {chromadb.__version__}")

from chromadb.utils import embedding_functions
default_ef = embedding_functions.DefaultEmbeddingFunction()
print("Default embedding function loaded successfully")
