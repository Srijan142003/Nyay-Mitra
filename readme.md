# Legal Study Platform - Flask Web Application

A comprehensive legal case study platform with AI-powered features including court trial simulation, chat consultation, and voice assistant.

## Features

### 1. **Court Trial Simulation** ⚖️
- Simulate court cases with AI-generated verdicts
- Support for multiple legal categories (Criminal, Civil, Family, Corporate, Property, Constitutional)
- Upload supporting documents (PDF, DOCX, images)
- Detailed verdicts with summary, findings, and final order
- Integrated feedback system

### 2. **Lawyer Up - Nyay Mitra** 💬
- Interactive chat interface with AI legal assistant
- Real-time legal consultation
- Case law research integration
- Conversational AI for legal guidance

### 3. **AI Voice Assistant** 🎙️
- Voice-based interaction with AI
- Multiple AI model options (Llama 3.1, Gemma)
- Text-to-speech responses
- Document upload and analysis
- Adjustable complexity levels (Basic, Intermediate, Complex)
- Full conversation transcript

### 4. **Admin Dashboard** 📊
- User registration tracking
- Case statistics and analytics
- Feedback monitoring
- Category distribution analysis

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Tesseract OCR (for image text extraction)

### Installing Tesseract OCR

**Windows:**
```bash
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR
```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Setup Steps

1. **Clone or download the project**

2. **Create project structure:**
```
legal_study_platform/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── home.html
│   ├── trial_simulation.html
│   ├── verdict.html
│   ├── lawyer_up.html
│   ├── ai_assistant.html
│   └── admin.html
├── static/
│   └── audio/
├── uploads/
└── data/
    └── constitution.pdf (optional)
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create necessary directories:**
```bash
mkdir templates static static/audio uploads data
```

5. **Place all HTML templates in the `templates` folder**

6. **(Optional) Add Indian Constitution PDF:**
   - Download the Indian Constitution PDF
   - Place it in the `data/` folder as `constitution.pdf`

## Running the Application

1. **Start the Flask server:**
```bash
python app.py
```

2. **Access the application:**
   - Open your browser and navigate to: `http://localhost:5000`

3. **Login credentials:**
   - Admin: username=`admin`, password=`admin`
   - Or register a new account

## API Keys

The application uses the following APIs (keys are already included):
- **Indian Kanoon API**: For case law research
- **Google Gemini API**: For AI verdict generation and chat
- **Groq API**: For voice assistant AI models

## Features Usage

### Court Trial Simulation
1. Select case category
2. Enter plaintiff and defendant statements
3. Optionally upload supporting documents
4. Click "Generate Verdict" to receive AI analysis
5. Submit feedback on verdict quality

### Lawyer Up Chat
1. Access from home page
2. Type legal questions or concerns
3. Receive AI-powered legal guidance
4. Chat history is maintained per session

### AI Voice Assistant
1. Select AI model and complexity level
2. Click "Press to Speak" and speak your question
3. Or upload documents for analysis
4. Receive voice and text responses
5. View full conversation transcript

### Admin Dashboard
1. Login as admin (username: admin, password: admin)
2. View user statistics
3. Monitor case submissions
4. Review feedback and ratings
5. Analyze category distribution

## Browser Compatibility

- **Best Experience**: Chrome, Edge (for voice recognition)
- **Voice Features**: Requires browser with WebKit Speech Recognition
- **File Upload**: All modern browsers supported

## Security Notes

⚠️ **Important for Production:**
1. Change the Flask secret key in `app.py`
2. Use a proper database instead of in-memory storage
3. Implement proper authentication and session management
4. Use environment variables for API keys
5. Add HTTPS/SSL encryption
6. Implement rate limiting
7. Add input validation and sanitization

## Troubleshooting

### Voice Recognition Not Working
- Ensure you're using Chrome or Edge browser
- Grant microphone permissions when prompted
- Check browser console for errors

### File Upload Issues
- Verify file size is under 16MB
- Check file extension is supported
- Ensure `uploads` folder exists and has write permissions

### API Errors
- Verify API keys are valid
- Check internet connection
- Review Flask console for detailed error messages

### Tesseract OCR Not Found
- Ensure Tesseract is installed
- Add Tesseract to system PATH
- On Windows, set path in code if needed:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

## Project Structure

```
app.py                      # Main Flask application
requirements.txt            # Python dependencies
templates/                  # HTML templates
├── base.html              # Base template with common elements
├── login.html             # Login page
├── register.html          # Registration page
├── home.html              # Main dashboard
├── trial_simulation.html  # Court simulation form
├── verdict.html           # Verdict display and feedback
├── lawyer_up.html         # Chat interface
├── ai_assistant.html      # Voice assistant interface
└── admin.html             # Admin dashboard
static/                    # Static files
└── audio/                 # Generated audio responses
uploads/                   # Uploaded user files
data/                      # Reference documents
```

## Technologies Used

- **Backend**: Flask (Python)
- **AI/ML**: Google Gemini, Groq (Llama, Gemma models)
- **APIs**: Indian Kanoon API for case law
- **Text Processing**: PyPDF2, python-docx, pdfplumber
- **OCR**: Tesseract, pytesseract
- **TTS**: gTTS (Google Text-to-Speech)
- **Speech Recognition**: Web Speech API

## Contributing

This is an educational project. Feel free to:
- Report bugs
- Suggest features
- Improve documentation
- Enhance UI/UX

## License

This project is for educational purposes. Ensure compliance with API terms of service when using.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Flask and API documentation
3. Check browser console for errors
4. Verify all dependencies are installed

---

**Note**: This application is designed for educational and research purposes. Always consult qualified legal professionals for actual legal advice.
