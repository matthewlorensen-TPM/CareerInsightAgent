import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def build_vector_database():
    print("Loading markdown files from the data folder...")
    data_dir = "data"
    
    # 1. Read files and check if they are empty
    documents = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                text = file.read().strip()
                if text:
                    documents.append(Document(page_content=text, metadata={"source": filename}))
                else:
                    print(f"  -> WARNING: {filename} is completely empty!")
    
    if not documents:
        print("\nERROR: No text found in your files. Please paste the text back into them and save.")
        return

    print(f"Loaded {len(documents)} files with text. Splitting text...")
    
    # 2. Split text
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    
    if not chunks:
        print("\nERROR: Text splitting failed. Chunks list is empty.")
        return

    print(f"Created {len(chunks)} chunks. Testing Google API connection...")
    
    # 3. Use the newly required gemini-embedding-001 model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    try:
        test_embed = embeddings.embed_query("Test connection")
        print("API connection successful!")
    except Exception as e:
        print(f"\nAPI ERROR: Could not generate embeddings. Check your .env file and API key.\nDetails: {e}")
        return

    # 4. Save to Chroma
    print("Saving to ChromaDB...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    
    print("\nSuccess! Your career data has been vectorized and stored in ChromaDB.")

if __name__ == "__main__":
    build_vector_database()