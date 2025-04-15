# 🌍 SmartSafar – AI-Based Travel Itinerary Planner

SmartSafar is an AI-powered travel itinerary planning web application built using **Streamlit**. It creates personalized travel plans based on your interests and destination using **Large Language Models (LLMs)**. With a secure login system and MongoDB integration, SmartSafar ensures a smooth and tailored experience for every user.

---

## ✨ Features

- 🔐 **Authenticated Login System**
  - User registration and login with SHA-256 hashed passwords.

- 🧠 **AI Itinerary Generator**
  - Uses **Groq’s LLaMA 3.3 70B** via **LangChain** for generating travel plans based on city and interests.

- 🌦 **Live Weather Updates**

- 🏨 **Accommodation Suggestions**

- 📅 **Seasonal Tips**

- 🎉 **Fun Facts**

- 🧾 **System Logs**
  - Logs user interactions in `system_interaction.log` for monitoring and debugging.

---

## 🧰 Tech Stack

| Component        | Tech Used                         |
|------------------|-----------------------------------|
| Frontend/Backend | Streamlit                         |
| AI Integration   | LangChain + Groq (LLM API)        |
| Database         | MongoDB (travelapp > users)       |
| Authentication   | SHA-256 password hashing          |
| Weather API      | WeatherAPI                        |
| Logging          | Python `logging` module           |

---

## 📁 Folder Structure

```
SmartSafar/
│
├── travel_app.py             # Main Streamlit app
├── requirements.txt          # Dependencies list
├── system_interaction.log    # Logs for user actions
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Jay2416/SmartSafar.git
cd SmartSafar
```

### 2. Set Up Virtual Environment (Optional)
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. MongoDB Setup

- Make sure MongoDB is running locally at:
  ```
  mongodb://localhost:27017
  ```
- Database name: `travelapp`
- Collection: `users`

To create a sample document, you can run:
```bash
mongoimport --db travelapp --collection users --file sample_data.json
```

### 5. Run the App
```bash
streamlit run travel_app.py
```

---

## 📚 Future Scope

- 📅 Multi-day trip planning
- 🗺 Interactive maps with POI markers
- 📧 Email itinerary as PDF
- 🌐 Deploy to cloud with persistent sessions