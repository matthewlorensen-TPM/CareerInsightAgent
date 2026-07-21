# --- SQLite3 Patch for Streamlit Cloud ---
# This must remain at the very top of the script before any other imports
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import base64
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# --- Google Sheets Imports ---
import gspread

# --- LangChain Imports ---
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# 1. Page Configuration
st.set_page_config(
    page_title="Matthew 'Matt' Lorensen | Career Insight Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# --- Security Gate (Hidden URL Parameter) ---
if st.query_params.get("token") != st.secrets.get("APP_PASSCODE", ""):
    st.warning("🔒 **Portfolio Locked:** This interactive agent is currently available by invitation only. If you need access, please contact the owner. matthewlorensen@gmail.com")
    st.stop()

# --- CSS / Styling ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

# Load all local images into memory for rendering
main_bg_base64 = get_base64_of_bin_file('src/Screenshot 2026-07-17 070620.png')
sidebar_bg_base64 = get_base64_of_bin_file('src/sidebar.jpg')
profile_pic_base64 = get_base64_of_bin_file('src/profile.png') 

# Load SVGs
github_icon_base64 = get_base64_of_bin_file('src/github.svg')
gmail_icon_base64 = get_base64_of_bin_file('src/gmail.svg')
linkedin_icon_base64 = get_base64_of_bin_file('src/linkedin.svg') 
reset_icon_base64 = get_base64_of_bin_file('src/resetconvo.svg')
resume_icon_base64 = get_base64_of_bin_file('src/myresume.svg') 

bg_css = f"""
<style>
    /* HIDE SPECIFIC STREAMLIT NATIVE UI ELEMENTS */
    #MainMenu {{visibility: hidden !important;}}
    footer {{visibility: hidden !important;}}
    .stAppDeployButton {{display: none !important;}}

    html, body, p, h1, h2, h3, h4, h5, h6, li, a, div {{ 
        font-family: "Arial Nova Light", Arial, sans-serif !important; 
    }}
    
    .stIcon, .material-symbols-rounded, .material-icons {{
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }}
    
    /* Main App Background */
    .stApp {{
        background-image: url("data:image/png;base64,{main_bg_base64}");
        background-size: cover; background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background-color: rgba(15, 23, 42, 0.85); z-index: 0;
    }}
    .stApp > header, .stApp > .main {{ position: relative; z-index: 1; }}
    
    /* Kill Streamlit's massive default sidebar padding */
    [data-testid="stSidebarUserContent"] {{
        padding-top: 2rem !important;
    }}
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {{ 
        background-image: url("data:image/jpg;base64,{sidebar_bg_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        border-right: 1px solid #334155; 
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: rgba(15, 23, 42, 0.7);
    }}

    /* Profile Picture Custom Styling */
    .profile-pic {{
        width: 130px;
        height: 130px;
        border-radius: 50%;
        object-fit: cover; 
        border: 3px solid rgba(255, 255, 255, 0.15);
        margin: 0 auto 10px auto; 
        display: block;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}

    /* Custom Chat Message Styling */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px; padding: 15px 20px; margin-bottom: 15px;
        backdrop-filter: blur(8px); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    /* Custom Sidebar Social Buttons */
    .social-icons-container {{
        display: flex; flex-direction: row; justify-content: center; gap: 15px; margin-bottom: 15px;
    }}
    .social-btn {{
        display: flex; align-items: center; justify-content: center;
        background-color: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        text-decoration: none;
        width: 55px; height: 55px; 
        transition: all 0.3s ease;
    }}
    .social-btn:hover {{
        background-color: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.4);
        transform: translateY(-2px);
    }}
    .social-btn img {{
        width: 28px; height: 28px; 
        object-fit: contain;
    }}

    /* Custom HTML Resume Link Styling */
    .resume-custom-link {{
        background-image: url("data:image/svg+xml;base64,{resume_icon_base64}");
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
        
        /* Matched to social buttons */
        background-color: rgba(255, 255, 255, 0.03); 
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 14px;
        
        height: 110px;
        width: 50%;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 0px; 
        display: block;
    }}
    .resume-custom-link:hover {{
        background-color: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.4);
        transform: translateY(-2px);
    }}
    
    /* Image-Based RESET Button Styling (Direct Streamlit target) */
    [data-testid="stSidebarUserContent"] div[data-testid="stButton"] button {{
        background-image: url("data:image/svg+xml;base64,{reset_icon_base64}") !important;
        background-size: contain !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        
        /* Matched to social buttons */
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        
        box-shadow: none !important;
        height: 110px !important; 
        width: 50% !important;
        transition: all 0.3s ease !important;
        padding: 0 !important;
    }}
    
    /* Hide the native text inside the Reset button */
    [data-testid="stSidebarUserContent"] div[data-testid="stButton"] button div,
    [data-testid="stSidebarUserContent"] div[data-testid="stButton"] button p,
    [data-testid="stSidebarUserContent"] div[data-testid="stButton"] button span {{
        display: none !important; 
    }}
    
    [data-testid="stSidebarUserContent"] div[data-testid="stButton"] button:hover {{
        background-color: rgba(255, 255, 255, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-2px) !important;
    }}
</style>
"""
st.markdown(bg_css, unsafe_allow_html=True)

# --- Google Sheets Logger ---
def log_interaction(query, answer):
    try:
        credentials_dict = {
            "type": "service_account",
            "project_id": "gen-lang-client-0424821963",
            "client_email": st.secrets["GCP_SA_EMAIL"],
            "private_key": st.secrets["GCP_SA_PRIVATE_KEY"].replace('\\n', '\n'),
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        client = gspread.service_account_from_dict(credentials_dict)
        sheet = client.open("CIA_Portfolio_Logger").sheet1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, query, answer])
        
    except Exception as e:
        st.error(f"Google Sheets Error Type: {type(e).__name__} | Message: {e}")
        st.stop()

# --- AI Setup ---
@st.cache_resource
def load_ai_components():
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("GOOGLE_API_KEY not found in Streamlit secrets!")
        st.stop()
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8}) 
    
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)    
    
    # 1. Contextualize Question Prompt
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 2. Main Response Prompt
    system_prompt = (
        "You are the exclusive Interactive Career Agent for Matthew 'Matt' Lorensen, "
        "a Technical Program Manager and IT Operations Leader. Your primary objective is to "
        "accurately and compellingly articulate Matt's expertise in technical program leadership, "
        "infrastructure operations, incident triage, and cross-functional strategy based strictly on the provided context.\n\n"
        "CRITICAL DIRECTIVES FOR RESPONSE GENERATION:\n"
        "1. TONE & STYLE: Speak strictly in the third person as Matt's AI assistant. Keep responses short, concise, and highly conversational. "
        "Write with a natural, straightforward writing style—avoid overly formal 'executive' rigidity, and completely ban robotic AI fluff "
        "(e.g., 'Here is the information...', 'delve', 'tapestry'). Talk to the user like a helpful peer who knows Matt's career inside and out.\n"
        "2. STRUCTURAL HIERARCHY: When outlining career history, achievements, or project workflows, format the output "
        "using clean Markdown bullet points. Prioritize a strict reverse-chronological order for roles. Bold key metrics, "
        "technologies, and operational outcomes to ensure the response is easily scannable.\n"
        "3. STRICT GROUNDING GUARDRAILS & PARTIAL MATCHES: Rely entirely on the retrieved context. Do not extrapolate, assume, or fabricate "
        "professional details. If a user asks for a specific example, story, or metric, and that exact scenario is not explicitly detailed in the context, "
        "you MUST output the fallback statement immediately. Do not attempt to substitute generic framework details for a specific requested example. "
        "Fallback Statement: 'That specific detail is not covered in the current portfolio repository. "
        "Please feel free to reach out to Matt directly via the LinkedIn or Email links in the sidebar to discuss this further.'\n"
        "4. ALIGNMENT TO CORE PILLARS: Dynamically frame responses around Matt's foundational strengths: driving structural efficiency in IT operations, "
        "managing high-stakes incident response, navigating strategic pivots, and translating complex technical realities into clear C-suite communication.\n"
        "5. PRE-PROGRAMMED RESPONSES (CRITICAL OVERRIDE): If the user asks about salary, compensation, references, compliance, or arbitrary personal trivia, "
        "search the context for the corresponding 'Ingestion Prompt Vector' or 'Standard Candidate Statement'. You MUST output that exact quote verbatim. "
        "Do not paraphrase it, and do not apply the third-person rule to it.\n"
        "6. PREDICTED FOLLOW-UPS & CALL TO ACTION: At the very end of your response, skip a line and provide 2 to 3 highly relevant follow-up questions "
        "the user could ask next to learn more about Matt's qualifications. Below the questions, always include a polite prompt to schedule a conversation "
        "if they have no further questions. Format the end of your response exactly like this:\n\n"
        "**Suggested Follow-Ups:**\n"
        "*   *[Insert question 1]*\n"
        "*   *[Insert question 2]*\n\n"
        "*Or, if you have no further questions, please use the CTAs in the sidebar to connect with Matt directly.*\n\n"
        "Context:\n{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)

chain = load_ai_components()

# --- UPGRADED SIDEBAR ---
with st.sidebar:
    # Render the circular profile picture
    if profile_pic_base64:
        st.markdown(f'<img src="data:image/png;base64,{profile_pic_base64}" class="profile-pic">', unsafe_allow_html=True)
        
    st.markdown("<div style='text-align: center;'><h2 style='margin-top: -10px; margin-bottom: 0px; font-size: 22pt;'>Matt Lorensen</h2></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><h4 style='margin-top: 0px; margin-bottom: 8px; color: #cbd5e1;'>Technical Program Leader</h4></div>", unsafe_allow_html=True)
    
    st.markdown(
        "<div style='text-align: center; font-size: 0.82em; font-style: italic; line-height: 1.4; color: #e2e8f0;'>"
        "Bridging the gap between high-level strategy and technical execution. "
        "I build resilient systems, optimize cloud infrastructure, and foster team development."
        "</div>", 
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    # 1. Resume Download Button (Nuclear Option: Base64 Embedded)
    pdf_file_path = "static/Matthew_Lorensen_Resume.pdf"
    if not os.path.exists(pdf_file_path):
        pdf_file_path = "src/Matthew_Lorensen_Resume.pdf"
        
    try:
        with open(pdf_file_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        resume_html = f"""
        <a href="data:application/octet-stream;base64,{pdf_base64}" download="Matthew_Lorensen_Resume.pdf" style="text-decoration: none;">
            <div class="resume-custom-link"></div>
        </a>
        """
        st.markdown(resume_html, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("⚠️ Resume file not found. Please verify it is named 'Matthew_Lorensen_Resume.pdf'")
    
    st.markdown("---")
    
    # 2. Reset Conversation Button (Uses native targeting)
    if st.button("invisible_reset_text", use_container_width=True):
        st.session_state.messages = []
        st.rerun()    
    cta_buttons_html = f"""
    <div class="social-icons-container">
        <a href="https://www.linkedin.com/in/matthewlorensen/" target="_blank" class="social-btn">
            <img src="data:image/svg+xml;base64,{linkedin_icon_base64}">
        </a>
        <a href="https://github.com/matthewlorensen-TPM/CareerInsightAgent" target="_blank" class="social-btn">
            <img src="data:image/svg+xml;base64,{github_icon_base64}">
        </a>
        <a href="mailto:matthew.lorensen@gmail.com" target="_blank" class="social-btn">
            <img src="data:image/svg+xml;base64,{gmail_icon_base64}">
        </a>
    </div>
    """
    st.markdown(cta_buttons_html, unsafe_allow_html=True)
    
# --- Main Interface ---
st.title("Matthew Lorensen")
st.subheader("Interactive Career Insight Agent")

st.markdown(
    """
    <div style="background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); 
                border-radius: 12px; padding: 15px 20px; margin-bottom: 20px; color: #ffffff; 
                backdrop-filter: blur(8px); box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);">
        <div style="margin-bottom: 10px;"><b>About This Project</b></div>
        <div style="margin-bottom: 10px; font-size: 0.95em; line-height: 1.5;">
            As a Technical Program Manager and IT Operations Leader, I built this AI agent to move beyond a static resume. 
            This project demonstrates hands-on applied AI, offering a dynamic way to explore my professional background, 
            incident response methodologies, and cross-functional leadership experience.
        </div>
        <div style="margin-bottom: 10px; font-size: 0.95em; line-height: 1.5;">
            <b>Note on Accuracy:</b> The model's temperature is strictly locked at 0.1. This guarantees that every response is intentional, highly deterministic, and completely grounded in my actual professional experience rather than AI hallucination.
        </div>
        <div style="font-size: 0.95em;">
            <b>Built with:</b> Python, Streamlit, LangChain, Chroma DB, and the Google Gemini API.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for idx, message in enumerate(st.session_state.messages):
    avatar = "🧑" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            feedback_key = f"feedback_{idx}"
            st.feedback("thumbs", key=feedback_key)

if user_query := st.chat_input("Ask me about Matt's career..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="🚀"):
        status_container = st.empty()
        with status_container.status("🚀 Pulling calculations and context...", expanded=True) as status:
            try:
                chat_history = []
                history_window = st.session_state.messages[-5:-1]
                
                for msg in history_window:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    else:
                        chat_history.append(AIMessage(content=msg["content"]))

                response = chain.invoke({"input": user_query, "chat_history": chat_history})
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
            log_interaction(user_query, answer)
            st.rerun()