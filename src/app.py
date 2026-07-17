import os
import base64
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Page Configuration (Must be first)
st.set_page_config(
    page_title="Matthew 'Matt' Lorensen | AI Portfolio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the API key
load_dotenv()

# --- Custom CSS for Technical Background & Styling ---
# 1. Function to encode the local image securely
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        # Failsafe: If the image isn't found, return empty string so the app doesn't crash
        return ""

# 2. Read the image file (Ensure the name matches your file exactly)
img_base64 = get_base64_of_bin_file('src/Screenshot 2026-07-17 070620.png')

# 3. Inject the CSS using the encoded image
if img_base64:
    bg_css = f"""
    <style>
        /* Changes the global font to Arial Nova Light */
        * {{
            font-family: "Arial Nova Light", Arial, sans-serif !important;
        }}
        
        /* Applies the image as the background - updated for PNG */
        .stApp {{
            background-image: url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Adds a dark tint over the image so chat text remains readable */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(15, 23, 42, 0.85); /* 85% dark slate tint */
            z-index: 0;
        }}
        
        /* Keeps the actual chat interface above the dark tint */
        .stApp > header, .stApp > .main {{
            position: relative;
            z-index: 1;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: #1e293b;
            border-right: 1px solid #334155;
        }}
        
        .stChatInputContainer {{
            padding-bottom: 20px;
        }}
        
        /* Adds a sleek, semi-transparent bubble around user and AI messages */
        [data-testid="stChatMessage"] {{
            background-color: rgba(255, 255, 255, 0.06); /* Faint light fill */
            border: 1px solid rgba(255, 255, 255, 0.15); /* Soft, glowing edge */
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 15px;
            backdrop-filter: blur(8px); /* Blurs the background behind the bubble */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); /* Slight drop shadow for depth */
        }}
    </style>
    """
else:
    # Failsafe CSS just in case the image is missing
    bg_css = """
    <style>
        * {
            font-family: "Arial Nova Light", Arial, sans-serif !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #1e293b;
            border-right: 1px solid #334155;
        }
        .stChatInputContainer {
            padding-bottom: 20px;
        }
        
        [data-testid="stChatMessage"] {
            background-color: rgba(255, 255, 255, 0.06); 
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 15px;
            backdrop-filter: blur(8px); 
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
    </style>
    """

st.markdown(bg_css, unsafe_allow_html=True)

# 2. Build the Professional Sidebar
with st.sidebar:
    # Keeping title and location here, moved name to main header
    st.write("Technical Program Manager | Operations Leader ")
    st.write("📍 Denver, CO")
    st.write("🌎 Global Remote Leadership")
    st.markdown("[🔗 LinkedIn Profile](https://www.linkedin.com/in/matthewlorensen/)")
    st.markdown("[📧 Email Me](mailto:matthew.lorensen@gmail.com)")
    st.markdown("[🟢 WhatsApp: +1 (989) 390-2024](https://wa.me/19893902024)")
    
    st.markdown("---")
    st.write("**Ask about my experience with:**")
    st.write("🔹 IT Operations & Frameworks")
    st.write("🔹 Incident Response & Triage")
    st.write("🔹 Cross-functional Leadership")
    st.write("🔹 Strategic Pivots & C-Suite Comm")
    st.write("🔹 Behavioral Q&A & Problem Solving")
    st.write("🔹 Culture Fit & Outside Interests")
    

# 3. Main Chat Header
st.title("Matthew Lorensen")
st.subheader("Interactive Career Agent")
st.write("""
Welcome to my interactive portfolio! I built this custom **Retrieval-Augmented Generation (RAG)** agent to provide a dynamic way to explore my professional history. 

**🛠️ The Tech Stack & Process:**
* **Frontend UI:** Built with pure Python using **Streamlit**.
* **Data Ingestion & Orchestration:** Powered by **LangChain** to parse and chunk my career history documents.
* **Vector Database:** Data is embedded using Google's `gemini-embedding-001` and stored locally in **ChromaDB**.
* **LLM Engine:** The logic and conversational generation is driven by **Google Gemini 1.5 Pro**.

Go ahead and ask the agent about my experience, leadership skills, or operational achievements!
""")
st.markdown("---")

# --- AI Setup ---
@st.cache_resource
def load_ai_components():
    # 1. Load the exact same embedding model used for ingestion
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 2. Connect to the local Chroma database (Increased k to 8 for timelines)
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8}) 
    
    # 3. Initialize the Gemini Chat model (Updated to working 1.5 Pro model)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)
    
    # 4. Give the AI its persona and rules
    system_prompt = (
        "You are Matthew Lorensen's professional portfolio assistant and career advocate. "
        "Your goal is to warmly, naturally, and persuasively represent Matt's value to recruiters and hiring managers, "
        "highlighting why his technical leadership, operational framework building, and program management skills make him an exceptional hire.\n\n"
        "TONE & PERSPECTIVE:\n"
        "- Be engaging, professional, and confident in Matt's abilities.\n"
        "- Speak in the third person (use 'Matt', 'Matthew', 'he', 'his'). If a user asks a question using 'I' or 'my' "
        "(e.g., 'Summarize my experience'), answer objectively as his assistant (e.g., 'Matt's experience demonstrates...').\n"
        "- FORBIDDEN PHRASES: Never use robotic AI phrases like 'According to the provided context', 'Based on the documents', "
        "or 'As stated in the text'. Speak naturally, as if you simply know his background inside and out.\n\n"
        "TIMELINE RULE:\n"
        "- When summarizing Matt's career history or listing multiple roles, ALWAYS present the information in strict "
        "reverse-chronological order (most recent first).\n\n"
        "ACCURACY RULE:\n"
        "- You must strictly rely on the provided Context. Do not invent, guess, or hallucinate metrics, roles, or skills. "
        "- If asked a question that isn't covered in the Context, deflect gracefully and positively. For example: "
        "'I don't have that specific metric on hand, but I can tell you about Matt's proven ability to...' and pivot to a relevant strength.\n\n"
        "Context: {context}"
    )
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    # 5. Build the chain
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

chain = load_ai_components()

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 1. Render history with custom avatars
for message in st.session_state.messages:
    # Assign a professional icon depending on who is speaking
    avatar = "👤" if message["role"] == "user" else "💼"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if user_query := st.chat_input("E.g., What did Matthew do at Hansen Technologies?"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # 2. Render user input with custom avatar
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_query)

    # 3. Render AI response with custom avatar
    with st.chat_message("assistant", avatar="💼"):
        
        # Create an empty container that we can delete later
        status_container = st.empty()
        
        with status_container.status("🧠 Analyzing career history...", expanded=True) as status:
            st.write("🔍 Scanning vector database, thanks for your patience...")
            try:
                response = chain.invoke({"input": user_query})
                answer = response["answer"]
            except Exception as e:
                # Your custom exception messages
                status.update(label="🚨 Incident Response Triggered!", state="error", expanded=False)
                st.error(f"🔔 Well this is awkward. It appears I've encountered a brief system error. Let's pretend this is a high-level C-Suite meeting and circle back to this question in a moment. (Try asking again!){e}")
                answer = None
                
        # 4. If successful, delete the status box entirely and print the clean answer
        if answer:
            status_container.empty() # Poof! The loading box vanishes.
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})