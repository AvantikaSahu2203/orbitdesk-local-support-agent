from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM

print("Downloading embedding model...")
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("Embedding model downloaded!")

print("Downloading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
print("Tokenizer downloaded!")

print("Downloading language model...")
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-0.5B-Instruct"
)
print("Language model downloaded!")