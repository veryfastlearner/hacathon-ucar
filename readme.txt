=== UCAR SMART QUERY ENGINE - SETUP & DEPLOYMENT GUIDE ===

1. LOCAL SETUP
--------------
A. Prerequisites:
   - Python 3.10+
   - Node.js (for the frontend)

B. Installation:
   1. Install Python dependencies:
      pip install -r requirements.txt
   
   2. Configure environment:
      - Fill in your .env file with:
        GROQ_API_KEY=your_key
        TAVILY_API_KEY=your_key

C. Running Locally:
   - OPTION 1 (Terminal Only):
     python agents.py
   
   - OPTION 2 (Full Web Experience):
     1. Start Backend API:
        python server.py
     2. Start Frontend:
        cd front
        npm install
        npm run dev
     3. Open http://localhost:5173 in browser.


2. RAILWAY DEPLOYMENT (BACKEND)
-------------------------------
To deploy the Python API (server.py) to Railway:

A. Preparation:
   1. Ensure 'gunicorn' is in your requirements.txt (Added already).
   2. Create a file named 'Procfile' in the root directory with:
      web: gunicorn server:app

B. Railway Steps:
   1. Link your GitHub repository to Railway.
   2. Railway will detect the Python environment.
   3. Add variables in "Variables" tab:
      - GROQ_API_KEY
      - TAVILY_API_KEY
      - PORT=5000 (Railway usually provides this automatically)
   4. Deployment should start automatically.

Note: In the React 'App.jsx', you will need to change the API URL from 
'http://localhost:5000' to your Railway deployment URL.


3. RAILWAY DEPLOYMENT (FRONTEND)
--------------------------------
The 'front' folder can be deployed separately:
1. In Railway, click 'New' > 'GitHub Repo' > Select Same Repo.
2. In 'Roots and Paths', set the 'Root Directory' to 'front'.
3. Set Build Command: npm run build
4. Set Publish Directory: dist
5. Set the 'VITE_API_BASE_URL' environment variable to your 
   Backend's Railway URL.


4. TROUBLESHOOTING
------------------
- If you get "Lock Error" with Qdrant: Make sure you aren't running 
  multiple Python processes at once. However, current version uses 
  in-memory mode which is safer.
- If data is missing: Ensure your PDFs are in the /data folder. 
  The system embeds them on startup.
