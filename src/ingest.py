import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

def build_vector_database():
    file_path = "data/portfolio_context.txt"
    print(f"Loading portfolio context from {file_path}...")
    
    # Check if file actually exists
    if not os.path.exists(file_path):
        print(f"ERROR: Could not find {file_path}. Make sure the data folder and text file exist.")
        return

    # 1. Read the file
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    
    if not documents or not documents[0].page_content.strip():
        print(f"\nERROR: {file_path} is completely empty! Please paste the text back into it and save.")
        return

    print("Loaded file successfully. Splitting text...")
    
    # 2. Split text
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    
    if not chunks:
        print("\nERROR: Text splitting failed. Chunks list is empty.")
        return

    print(f"Created {len(chunks)} chunks. Testing Google API connection...")
    
    # 3. Check Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
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
    
    print("\n✅ Success! Your career data has been vectorized and stored in ChromaDB.")

if __name__ == "__main__":
    build_vector_database()