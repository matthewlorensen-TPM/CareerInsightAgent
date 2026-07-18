import os
import base64
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# --- New Google Sheets Imports ---
import gspread
from google.oauth2.service_account import Credentials

# Use these exact, standard paths
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Page Configuration
st.set_page_config(
    page_title="Matthew 'Matt' Lorensen | AI Portfolio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# --- Security Gate (Hidden URL Parameter) ---
# Checks the URL for a specific token (e.g., your-app.streamlit.app/?token=hire_me_2026)
if st.query_params.get("token") != st.secrets.get("APP_PASSCODE", ""):
    st.warning("🔒 **Portfolio Locked:** This interactive agent is currently available by invitation only.")
    st.stop()

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
    /* Target standard text but avoid breaking icons by removing the * wildcard */
    html, body, p, h1, h2, h3, h4, h5, h6, li, a, div {{ 
        font-family: "Arial Nova Light", Arial, sans-serif !important; 
    }}
    
    /* Explicitly protect Streamlit's material icons from being overwritten */
    .stIcon, .material-symbols-rounded, .material-icons {{
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }}
    
    /* Your custom background and sidebar CSS (untouched) */
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

# --- Google Sheets Logger ---
def log_interaction(query, answer):
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = {
            "client_email": st.secrets["GCP_SA_EMAIL"],
            "private_key": st.secrets["GCP_SA_PRIVATE_KEY"].replace('\\n', '\n'),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = Credentials.from_service_account_info(credentials, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Matches your exact workbook name
        sheet = client.open("CIA_Portfolio_Logger").sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, query, answer])
    except Exception as e:
        print(f"Logging failed: {e}") # Fails silently in the background so the app doesn't crash for the user

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
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8}) 
    
    # Current Stable Model
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)    
    
    # 3. Prompt & Chain
system_prompt = (
        "You are the exclusive Interactive Career Agent for Matthew 'Matt' Lorensen, "
        "a Technical Program Manager and IT Operations Leader. Your primary objective is to "
        "accurately and compellingly articulate Matt's expertise in technical program leadership, "
        "infrastructure operations, incident triage, and cross-functional strategy based strictly on the provided context.\n\n"
        "CRITICAL DIRECTIVES FOR RESPONSE GENERATION:\n"
        "1. TONE & STYLE: Speak strictly in the third person. Adopt an executive-level, confident, and articulate "
        "tone. Completely avoid robotic AI opening fluff (e.g., 'Based on the context provided...', 'Sure, I can help with that!') "
        "and corporate AI clichés (e.g., 'delve', 'tapestry', 'testament', 'beacon'). Get straight to the data.\n"
        "2. STRUCTURAL HIERARCHY: When outlining career history, achievements, or project workflows, format the output "
        "using clean Markdown bullet points. Prioritize a strict reverse-chronological order for roles. Bold key metrics, "
        "technologies, and operational outcomes to ensure the response is easily scannable.\n"
        "3. STRICT GROUNDING GUARDRAILS: Rely entirely on the retrieved context. Do not extrapolate, assume, or fabricate "
        "professional details. If a user asks a question regarding a specific project, technology, or historical event that "
        "cannot be verified by the context, gracefully respond: 'That specific detail is not covered in the current portfolio repository. "
        "Please feel free to reach out to Matt directly via the LinkedIn or Email links in the sidebar to discuss this further.'\n"
        "4. ALIGNMENT TO CORE PILLARS: Dynamically frame responses around Matt's foundational strengths: driving structural efficiency in IT operations, "
        "managing high-stakes incident response, navigating strategic pivots, and translating complex technical realities into clear C-suite communication.\n"
        "5. PRE-PROGRAMMED RESPONSES (CRITICAL OVERRIDE): If the user asks about salary, compensation, references, compliance, or arbitrary personal trivia, "
        "search the context for the corresponding 'Ingestion Prompt Vector' or 'Standard Candidate Statement'. You MUST output that exact quote verbatim. "
        "Do not paraphrase it, and do not apply the third-person rule to it.\n\n"
        "Context:\n{context}"
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
    st.write("**Suggested Topics:**")
    st.write("🔹 IT Operations & Frameworks")
    st.write("🔹 Incident Response & Triage")
    st.write("🔹 Cross-functional Leadership")
    st.write("🔹 Strategic Pivots & C-Suite Comm")
    st.write("🔹 Behavioral Q&A & Problem Solving")
    st.write("🔹 Culture Fit & Outside Interests")

# --- Main Interface ---
st.title("Matthew Lorensen")
st.subheader("Interactive Career Insight Agent")

# Project Overview Expander
with st.expander("💡 About This Project"):
    st.write(
        "As a Technical Program Manager and IT Operations Leader, I built this AI agent to move beyond a static resume. "
        "This project demonstrates hands-on applied AI, offering a dynamic way to explore my professional background, "
        "incident response methodologies, and cross-functional leadership experience."
    )
    st.write("**Built with:** Python, Streamlit, LangChain, Chroma DB, and the Google Gemini API.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages and append feedback widgets to AI responses
for idx, message in enumerate(st.session_state.messages):
    avatar = "👤" if message["role"] == "user" else "💼"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            feedback_key = f"feedback_{idx}"
            st.feedback("thumbs", key=feedback_key)

if user_query := st.chat_input("Ask me about Matt's career..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="💼"):
        status_container = st.empty()
        with status_container.status("🧠 Analyzing extensive work history...", expanded=True) as status:
            try:
                response = chain.invoke({"input": user_query})
                answer = response["answer"]
            except Exception as e:
                import traceback
                status.update(label="🚨 System Error", state="error", expanded=False)
                st.error(f"Error Type: {type(e).__name__} | Message: {e}")
                with st.expander("Click to view full developer logs"):
                    st.code(traceback.format_exc())
                answer = None
        
        if answer:
            status_container.empty()
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # --- Trigger the logging function in the background ---
            log_interaction(user_query, answer)
            
            st.rerun() # Reruns the app to render the response and the feedback widget cleanly