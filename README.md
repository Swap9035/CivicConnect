CivicConnect

AI-Powered Grievance Redressal Platform

Overview

CivicConnect is an AI-based system that improves public grievance handling by automating complaint analysis, prioritization, routing, and tracking.

Built during the Vibe Coding Hackathon by Team Byteblazers.

Problem

Current systems are:

Unstructured (text, voice, mixed inputs)
Slow due to manual processing
Inefficient in routing
Lacking transparency
Solution

The platform uses AI to:

Classify complaints
Assign priority
Route to correct departments
Track resolution status
Features
AI-based complaint intake (text, voice, image)
Automatic routing
Priority scoring
Image-based verification
Tech Stack

Frontend: React, Vite, TailwindCSS
Backend: FastAPI, Python
Database: MongoDB
AI: Mistral AI, LangChain, LangGraph
Auth: JWT, bcrypt

Setup
Prerequisites

Node.js, Python, MongoDB, Git

Installation
git clone https://github.com/Swap9035/CivicConnect.git
cd CivicConnect

Backend
cd backend
python -m venv myenv
source myenv/bin/activate   # or myenv\Scripts\activate (Windows)
pip install -r requirements.txt

Create .env:

MONGO_URI=mongodb://localhost:27017/grievance_db
MISTRAL_API_KEY=your_api_key
JWT_SECRET_KEY=your_secret_key

Run:
python main.py

Frontend
cd ..
npm install

Create .env:
VITE_API_BASE_URL=http://localhost:8000

Run:
npm run dev

Usage

Citizen: submit and track complaints
Officer: manage and resolve tickets
Admin: manage users and system

Admin Login

Email: superadmin@gov.in

Password: TempAdmin@123

Contributors

Swap9035, Himanshu-code1, khanaa4, Adityapandey6969

License

MIT License
