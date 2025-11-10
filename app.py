from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import requests
import google.generativeai as genai
from groq import Groq
import PyPDF2
from docx import Document
from gtts import gTTS
import speech_recognition as sr
from PIL import Image
import pytesseract
import pdfplumber
from io import BytesIO
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-me')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('static/audio', exist_ok=True)

# API Keys from environment variables
INDIAN_KANOON_API_KEY = os.getenv('INDIAN_KANOON_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Validate that API keys are loaded
if not all([INDIAN_KANOON_API_KEY, GEMINI_API_KEY, GROQ_API_KEY]):
    raise ValueError("Missing required API keys. Please check your .env file.")

# Configure APIs
genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# In-memory storage (replace with database in production)
users_db = {'admin': generate_password_hash('admin')}
cases_db = []
feedback_db = {}
chat_history = {}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        # Fallback to PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    doc = Document(file_path)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_image(file_path):
    """Extract text from image using OCR"""
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

def search_indian_kanoon(query, category):
    """Search Indian Kanoon API for relevant cases"""
    try:
        url = "https://api.indiankanoon.org/search/"
        params = {
            'formInput': f'{category} {query}',
            'pagenum': 0
        }
        headers = {
            'Authorization': f'Token {INDIAN_KANOON_API_KEY}'
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Indian Kanoon API Error: {e}")
        return None

def generate_verdict_with_gemini(plaintiff_statement, defendant_statement, category, case_law_context=""):
    """Generate verdict using Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""You are an AI legal assistant analyzing a {category} case. Based on the following information, provide a structured legal verdict.

Category: {category}

Plaintiff's Statement:
{plaintiff_statement}

Defendant's Statement:
{defendant_statement}

Relevant Case Law Context:
{case_law_context}

Please provide a comprehensive verdict with the following structure:

1. SUMMARY OF ARGUMENTS
   - Plaintiff's key arguments
   - Defendant's key arguments

2. FINDINGS OF FACT
   - Analysis of evidence and statements
   - Applicable legal principles
   - Relevant precedents

3. FINAL ORDER (VERDICT)
   - Clear decision
   - Reasoning
   - Recommendations

Format your response clearly with these three sections."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return """⚠️ API QUOTA EXCEEDED

We apologize for the inconvenience. The AI service has temporarily reached its usage limit.

TEMPORARY VERDICT ANALYSIS:

1. SUMMARY OF ARGUMENTS
   
   Plaintiff's Arguments:
   - The plaintiff has presented their case with supporting evidence and legal grounds.
   
   Defendant's Arguments:
   - The defendant has provided their counter-arguments and defense.

2. FINDINGS OF FACT
   
   Analysis:
   Due to API limitations, we cannot provide a full AI-generated analysis at this moment. 
   Please try again in a few minutes, or contact support for assistance.
   
   Note: This is a temporary limitation and will be resolved shortly.

3. FINAL ORDER
   
   Status: ANALYSIS PENDING
   Reason: API rate limit reached
   Recommendation: Please retry your request after 1-2 minutes.
   
For immediate assistance, please consult with a legal professional.

Error Details: API quota exceeded. Service will resume shortly."""
        
        print(f"Gemini API Error: {e}")
        return f"Error generating verdict: Unable to connect to AI service. Please try again in a few moments.\n\nTechnical details: {error_msg[:200]}"

@app.route('/')
def index():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users_db and check_password_hash(users_db[username], password):
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users_db:
            return render_template('register.html', error='Username already exists')
        
        users_db[username] = generate_password_hash(password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/trial-simulation', methods=['GET', 'POST'])
def trial_simulation():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        category = request.form.get('category')
        plaintiff_statement = request.form.get('plaintiff_statement')
        defendant_statement = request.form.get('defendant_statement')
        
        # Handle file upload
        file_context = ""
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract text based on file type
                ext = filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    file_context = extract_text_from_pdf(filepath)
                elif ext in ['docx', 'doc']:
                    file_context = extract_text_from_docx(filepath)
                elif ext in ['png', 'jpg', 'jpeg']:
                    file_context = extract_text_from_image(filepath)
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        file_context = f.read()
        
        # Search for relevant case law
        case_law = search_indian_kanoon(f"{plaintiff_statement} {defendant_statement}", category)
        case_law_context = json.dumps(case_law)[:2000] if case_law else ""
        
        # Generate verdict
        verdict = generate_verdict_with_gemini(
            plaintiff_statement, 
            defendant_statement, 
            category,
            case_law_context
        )
        
        # Store case
        case_record = {
            'id': len(cases_db) + 1,
            'username': session['username'],
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'plaintiff_statement': plaintiff_statement,
            'defendant_statement': defendant_statement,
            'verdict': verdict
        }
        cases_db.append(case_record)
        
        return render_template('verdict.html', verdict=verdict, category=category)
    
    return render_template('trial_simulation.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    feedback = {
        'username': session['username'],
        'category': request.form.get('category'),
        'rating': request.form.get('rating'),
        'remarks': request.form.get('remarks'),
        'timestamp': datetime.now().isoformat()
    }
    feedback_db.append(feedback)
    
    return jsonify({'success': True, 'message': 'Feedback submitted successfully'})

@app.route('/lawyer-up', methods=['GET', 'POST'])
def lawyer_up():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if session['username'] not in chat_history:
        chat_history[session['username']] = []
    
    if request.method == 'POST':
        user_input = request.form.get('user_input', '').strip()
        
        if user_input:
            chat_history[session['username']].append({'role': 'user', 'content': user_input})
            
            try:
                legal_context = search_indian_kanoon(user_input, "general")
                context_text = json.dumps(legal_context)[:1500] if legal_context else ""
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""You are Nyay Mitra, a friendly and knowledgeable legal assistant for Indian law. 

IMPORTANT: Keep your response CONCISE and to the point (2-4 paragraphs maximum). Be direct and clear.

User question: {user_input}

Relevant legal context from Indian case law:
{context_text}

Provide helpful, accurate legal guidance in a conversational tone. Focus on:
1. Direct answer to the question
2. Key legal points only
3. Most relevant laws or precedents (if applicable)

Keep it brief and easy to understand. Avoid lengthy explanations unless specifically asked for details."""

                response = model.generate_content(prompt)
                bot_message = response.text
                
                chat_history[session['username']].append({'role': 'assistant', 'content': bot_message})
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    bot_message = "⚠️ I apologize, but I've reached my usage limit temporarily. Please try again in 1-2 minutes. The service will resume automatically."
                else:
                    bot_message = f"I apologize, but I encountered an error. Please try again. If the issue persists, please contact support."
                chat_history[session['username']].append({'role': 'assistant', 'content': bot_message})
    
    return render_template('lawyer_up.html', chat_history=chat_history[session['username']], username=session['username'])

@app.route('/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_message = request.json.get('message')
    username = session['username']
    
    if username not in chat_history:
        chat_history[username] = []
    
    # Add user message to history
    chat_history[username].append({'role': 'user', 'content': user_message})
    
    try:
        # Search for relevant legal information
        legal_context = search_indian_kanoon(user_message, "general")
        context_text = json.dumps(legal_context)[:1500] if legal_context else ""
        
        # Generate response using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""You are Nyay Mitra, a friendly and knowledgeable legal assistant for Indian law.

IMPORTANT: Keep your response CONCISE and to the point (2-4 paragraphs maximum). Be direct and clear.

User question: {user_message}

Relevant legal context from Indian case law:
{context_text}

Provide helpful, accurate legal guidance in a conversational tone. Focus on:
1. Direct answer to the question
2. Key legal points only
3. Most relevant laws or precedents (if applicable)

Keep it brief and easy to understand. Avoid lengthy explanations unless specifically asked for details."""

        response = model.generate_content(prompt)
        bot_message = response.text
        
        # Add bot response to history
        chat_history[username].append({'role': 'assistant', 'content': bot_message})
        
        return jsonify({
            'message': bot_message,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai-assistant')
def ai_assistant():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('ai_assistant.html')

@app.route('/voice-chat', methods=['POST'])
def voice_chat():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    user_input = data.get('text', '')
    model_name = data.get('model', 'llama-3.1-8b-instant')
    complexity = data.get('complexity', 'intermediate')
    
    try:
        # Search Indian Kanoon for context
        legal_context = search_indian_kanoon(user_input, "general")
        context_text = json.dumps(legal_context)[:1000] if legal_context else ""
        
        # Prepare system message based on complexity
        complexity_prompts = {
            'basic': 'Explain legal concepts in very simple terms, as if talking to someone with no legal background.',
            'intermediate': 'Provide clear legal explanations with some technical terms when necessary.',
            'complex': 'Provide detailed legal analysis with proper citations and technical language.'
        }
        
        system_message = f"""You are a legal AI assistant specializing in Indian law. {complexity_prompts[complexity]}

Relevant legal context:
{context_text}

Also reference the Indian Constitution when applicable."""
        
        # Generate response using Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=1024
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Generate audio response
        tts = gTTS(text=response_text, lang='en', slow=False)
        audio_filename = f"response_{datetime.now().timestamp()}.mp3"
        audio_path = os.path.join('static/audio', audio_filename)
        tts.save(audio_path)
        
        return jsonify({
            'text': response_text,
            'audio_url': f'/static/audio/{audio_filename}',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process-voice-file', methods=['POST'])
def process_voice_file():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'document')
    model_name = request.form.get('model', 'llama-3.1-8b-instant')
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract content based on file type
        content = ""
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'pdf':
            content = extract_text_from_pdf(filepath)
        elif ext in ['docx', 'doc']:
            content = extract_text_from_docx(filepath)
        elif ext in ['png', 'jpg', 'jpeg']:
            content = extract_text_from_image(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Analyze with Groq
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a legal AI assistant. Analyze the provided document and provide legal insights."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this document:\n\n{content[:4000]}"
                }
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=1024
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Generate audio
        tts = gTTS(text=response_text, lang='en', slow=False)
        audio_filename = f"file_response_{datetime.now().timestamp()}.mp3"
        audio_path = os.path.join('static/audio', audio_filename)
        tts.save(audio_path)
        
        return jsonify({
            'text': response_text,
            'audio_url': f'/static/audio/{audio_filename}',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    # Prepare statistics
    stats = {
        'total_users': len(users_db) - 1,  # Exclude admin
        'total_cases': len(cases_db),
        'total_feedback': len(feedback_db),
        'users': [u for u in users_db.keys() if u != 'admin'],
        'recent_cases': cases_db[-10:] if cases_db else [],
        'recent_feedback': feedback_db[-10:] if feedback_db else []
    }
    
    # Category distribution
    category_counts = {}
    for case in cases_db:
        cat = case['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    stats['category_distribution'] = category_counts
    
    return render_template('admin.html', stats=stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
