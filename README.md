**💼 CareerKit AI**
**AI-Powered Job Application & Career Portfolio Kit**

CareerKit AI is an AI-powered web application that helps candidates enhance their resumes, write tailored cover letters, build web portfolios, and generate video pitch scripts without fabricating false skills or experiences.

**✨ Features**
- AI Resume Studio: Upload resumes (PDF, DOCX, TXT) or paste text to improve structure and impact.
- Claim Verification: Automatically cross-checks resume statements against verified candidate facts.
- Tailored Cover Letters: Generates job-specific cover letters matched to job descriptions.
- Web Portfolio Generator: Creates a clean, responsive single-page portfolio layout.
- 30–60s Video Script: Generates an elevator pitch script with teleprompter timing markers.
- Download Documents: Export resumes and cover letters directly to ATS-friendly PDF and DOCX.
- Interactive Dashboard: Real-time candidate tracking, document history, and analytics.

**🛠️ Tech Stack**
- Programming Language: Python
- Backend / Web Framework: Flask
- Frontend / UI: HTML5, CSS3, JavaScript
- Database: SQLite
- AI Integration: Google Gemini API (gemini-3.5-flash-lite)
- Libraries: google-genai, pypdf, python-docx, reportlab, python-dotenv
- Deployment: Render & Gunicorn
- Version Control: GitHub

**⚙️ How It Works**
1. Create or select a candidate profile with verified skills and projects.
2. Upload or paste a resume in the Resume Studio.
3. Click Improve with AI to enhance wording and view verification claims.
4. Generate tailored cover letters, a web portfolio, and video pitch script.
5. Review and export documents in PDF or DOCX format.

**🚀 Run Locally**

1. Clone the repository
git clone https://github.com/thejaswinipanchatcharam-design/CareerKit-AI.git
cd CareerKit-AI

2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

3. Install dependencies
pip install -r requirements.txt

4. Configure your API key
Create a .env file in the project root:
SECRET_KEY=your_secret_key
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

5. Start the application
python app.py

Open in browser: http://127.0.0.1:5000/

**🔐 Security**
- Keep API keys private and store them in .env.
- Never commit .env or credentials to GitHub.
- Add GEMINI_API_KEY as an Environment Variable when deploying to Render.

**🌐 Live Demo**
Try CareerKit AI here: https://careerkit-ai-wahy.onrender.com


**📂 Source Code**
Explore the source code on GitHub: https://github.com/thejaswinipanchatcharam-design/CareerKit-AI

**👩‍💻 Developer**
Developed as a capstone project exploring Python web applications, generative AI integration, and trustworthy career tooling.

**🔮 Future Enhancements**
- AI mock technical interview practice.
- LinkedIn headline and bio generator.
- Voice recording for the video teleprompter script.
- Direct job application tracking.

Turn your verified skills into job-ready applications with CareerKit AI.
