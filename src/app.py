import os
import base64
import streamlit as st
from dotenv import load_dotenv

# Use these exact, standard paths
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Page Configuration
st.set_page_config(
    page_title="Matthew 'Matt' Lorensen | AI Portfolio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# --- CSS / Styling ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

img_base64 = get_base64_of_bin_file('src/Screenshot 2026-07-17 070620.png')
bg_css = f"""
<style>
    * {{ font-family: "Arial Nova Light", Arial, sans-serif !important; }}
    .stApp {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover; background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(15, 23, 42, 0.85); z-index: 0;
    }}
    .stApp > header, .stApp > .main {{ position: relative; z-index: 1; }}
    [data-testid="stSidebar"] {{ background-color: #1e293b; border-right: 1px solid #334155; }}
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px; padding: 15px 20px; margin-bottom: 15px;
        backdrop-filter: blur(8px); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
</style>
"""
st.markdown(bg_css, unsafe_allow_html=True)

# --- AI Setup ---
@st.cache_resource
def load_ai_components():
    # 1. API Key Setup
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("GOOGLE_API_KEY not found in Streamlit secrets!")
        st.stop()
    
    # 2. Components
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8}) 
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)
    
    # 3. Prompt & Chain
    system_prompt = (
        "You are Matthew Lorensen's professional portfolio assistant. "
        "Highlight Matt's technical leadership, operations, and program management. "
        "Speak in the third person. Use reverse-chronological order for roles. "
        "Do not use robotic AI phrases. Rely strictly on context."
        "\n\nContext: {context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)

# This now returns the built chain
chain = load_ai_components()

# --- Sidebar ---
with st.sidebar:
    st.write("Technical Program Manager | Operations Leader")
    st.write("🔹 IT Operations\n🔹 Incident Response\n🔹 Strategy")
    st.markdown("[🔗 LinkedIn](https://www.linkedin.com/in/matthewlorensen/)")
    st.markdown("[📧 Contact Me](mailto:matthew.lorensen@gmail.com)")
    st.markdown("---")
    st.write("**Ask me about:**")
    st.write("🔹 IT Operations & Frameworks")
    st.write("🔹 Incident Response & Triage")
    st.write("🔹 Cross-functional Leadership")
    st.write("🔹 Strategic Pivots & C-Suite Comm")
    st.write("🔹 Behavioral Q&A & Problem Solving")
    st.write("🔹 Culture Fit & Outside Interests")

# --- Main Interface ---
st.title("Matthew Lorensen")
st.subheader("Interactive Career Agent")
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "💼"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if user_query := st.chat_input("Ask about Matt's career..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="💼"):
        status_container = st.empty()
        with status_container.status("🧠 Analyzing extensive workhistory...", expanded=True) as status:
            try:
                response = chain.invoke({"input": user_query})
                answer = response["answer"]
            except Exception as e:
                status.update(label="🚨 System Error", state="error", expanded=False)
                st.error(f"Something went wrong: {e}")
                answer = None
        
        if answer:
            status_container.empty()
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})