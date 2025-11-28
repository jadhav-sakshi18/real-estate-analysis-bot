# Real Estate Analysis Chatbot

A web-based chatbot for analyzing real estate data. This project allows users to upload real estate datasets, query area-wise demand and price trends, and visualize the results with interactive charts and tables. It also supports comparing multiple areas for better decision-making.

---

## Features

- **Upload Excel Files:** Users can upload `.xlsx` or `.xls` files containing real estate data.
- **Interactive Chat:** Query data using natural-language-like commands.
- **Data Analysis:**
  - Area-wise demand trends
  - Price growth trends
  - Comparison between multiple areas
- **Visualizations:**
  - Interactive line charts for demand and price trends
  - Dynamic tables with download option (CSV)
- **User-Friendly Interface:** Simple chat-based interface for easy interaction.

---

## Technologies Used

- **Frontend:** React.js, Chart.js
- **Backend:** Django REST Framework
- **Database/Storage:** In-memory pandas DataFrame (from uploaded Excel)
- **Data Visualization:** Line charts using `react-chartjs-2`

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/jadhav-sakshi18/real-estate-analysis-bot.git
cd real-estate-analysis-bot
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# or
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# or
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

cd frontend
npm install
npm start

real-estate-analysis-bot/
│
├── backend/             # Django REST backend
│   ├── api/             # API endpoints for analysis and file upload
│   └── real_estate.xlsx # Sample dataset
│
├── frontend/            # React frontend
│   ├── src/
│   └── package.json
│
└── README.md            # Project documentation

