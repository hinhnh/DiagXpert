# build_sample_database.py

from vector_db import VectorDatabase

# 1. Sample documents to index into the vector database
sample_documents = [
    "Engine failure detected in module A",
    "Please check the spark plugs and ignition",
    "Battery is low or malfunctioning",
    "Oil pressure warning light is on",
    "Brake fluid level is too low",
    "Coolant temperature is too high",
    "Tire pressure sensor reports underinflation",
    "Transmission fluid leak detected",
    "Air filter needs replacement",
    "Fuel injector might be clogged"
]

# 2. Initialize and build the vector database
vdb = VectorDatabase()
vdb.build(sample_documents)

# 3. Save the vector index and corresponding documents to disk
vdb.save("faiss_index.pkl", "docs.pkl")

print("✅ Sample vector database created and saved successfully.")
