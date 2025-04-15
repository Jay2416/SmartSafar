import streamlit as st
from pymongo import MongoClient
import hashlib
import requests
import markdown
import logging
from typing import TypedDict, List, Union
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# ----------------- MongoDB Connection -----------------
client = MongoClient("mongodb://localhost:27017")
db = client["travelapp"]
users_collection = db["users"]

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------- User Authentication -----------------
def verify_user(identifier, password):
    hashed = hash_password(password)
    user = users_collection.find_one({
        "$or": [{"username": identifier}, {"email": identifier}],
        "password": hashed
    })
    return user

def register_user(firstname, lastname, username, email, mobile, password):
    if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
        return False, "⚠️ Username or Email already exists."
    users_collection.insert_one({
        "firstname": firstname,
        "lastname": lastname,
        "username": username,
        "email": email,
        "mobile": mobile,
        "password": hash_password(password)
    })
    return True, "✅ Registration successful! You can now log in."


# ----------------- Initialize AI Model -----------------
class PlannerState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]
    city: str
    interests: List[str]
    itinerary: str

llm = ChatGroq(
    temperature=0.7,
    groq_api_key="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",
    model_name="llama-3.3-70b-versatile"
)

logging.basicConfig(
    filename="system_interaction.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_interaction(user_input, response):
    logging.info(f"User Input: {user_input} | Response: {response}")

# ----------------- Travel Planning Functions -----------------
def input_city(city: str, state: PlannerState) -> PlannerState:
    return {
        **state,
        "city": city,
        "messages": state["messages"] + [HumanMessage(content=f"City: {city}")]
    }

def input_interests(interests: str, state: PlannerState) -> PlannerState:
    interest_list = [interest.strip() for interest in interests.split(",")]
    return {
        **state,
        "interests": interest_list,
        "messages": state["messages"] + [HumanMessage(content=f"Interests: {', '.join(interest_list)}")]
    }

def create_itinerary(state: PlannerState) -> str:
    itinerary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a smart travel agent who creates engaging, fun, and optimized day trip itineraries for {city}. \
        Tailor recommendations based on the user's interests: {interests}. \
        Include hidden gems, famous spots, and local cuisine. Keep it structured, with timestamps. \
        Suggest budget ranging from afforable to luxurious accommodations near the city, along with their approximate price range. \
        Also, provide the best season to visit this place for the best experience.'"),
        ("human", "Plan my perfect trip, including budget stays and best season recommendations!")
    ])

    response = llm.invoke(itinerary_prompt.format_messages(city=state["city"], interests=', '.join(state["interests"])))
    itinerary_markdown = response.content
    return markdown.markdown(itinerary_markdown)

def get_weather(city: str) -> str:
    api_key = "b787841c42e84b32b70235141251102"
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=no"
    try:
        response = requests.get(url)
        data = response.json()
        if "current" in data:
            weather_desc = data["current"]["condition"]["text"]
            temp = data["current"]["temp_c"]
            return f"🌤 **Current weather in {city}:** {weather_desc}, {temp}°C"
        else:
            return "⚠️ Weather data unavailable."
    except:
        return "❌ Error fetching weather."

def fun_fact(city: str) -> str:
    fun_fact_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a knowledgeable travel guide. Share an interesting and unique fun fact about {city} that most travelers don’t know."),
        ("human", "Tell me a fun fact about {city}!")
    ])

    response = llm.invoke(fun_fact_prompt.format_messages(city=city))
    return f"🎉 **Fun Fact:** {response.content}"

from urllib.parse import urlparse, parse_qs
import time 

# ----------------- Streamlit Functions -----------------

def get_current_tab():
    query_params = st.query_params
    return query_params.get("tab", ["login"])[0]

def is_valid_password(p):
    import re
    return (
        len(p) >= 8 and
        re.search(r"[A-Z]", p) and  # Uppercase
        re.search(r"[a-z]", p) and  # Lowercase
        re.search(r"\d", p) and     # Digit
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", p)  # Special char
    )

def is_valid_phone(num):
    return (num.isdigit() and len(num)==10)

def switch_tab(tab_name):
    js = f"""
    <script>
    // Find all tab buttons and click the specified tab
    const tabs = parent.document.querySelectorAll('button[role="tab"]');
    tabs.forEach(tab => {{
        if (tab.innerText.includes('{tab_name}')) {{
            tab.click();
        }}
    }});
    </script>
    """
    st.components.v1.html(js)

def check_user_exists(identifier):
    """Check if username/email exists in database"""
    return users_collection.find_one({
        "$or": [{"username": identifier}, {"email": identifier}]
    })

def update_password(identifier, new_password):
    """Update password in database"""
    hashed = hash_password(new_password)
    users_collection.update_one(
        {"$or": [{"username": identifier}, {"email": identifier}]},
        {"$set": {"password": hashed}}
    )
    
# ----------------- Streamlit UI -----------------
st.title("✈️ SmartSafar")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --------- LOGIN / REGISTER PAGE ---------
if not st.session_state.logged_in:
    current_tab = get_current_tab()
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    if current_tab == "register":
        active_tab = tab2
    else:
        active_tab = tab1
        if "show_forgot_password" not in st.session_state:
            st.session_state.show_forgot_password = False

    with tab1:
        st.subheader("User Login")
        identifier = st.text_input("Username/Email", key="login_identifier")
        password = st.text_input("Password", type="password", key="login_password")

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Forgot Password?"):
                st.session_state.show_forgot_password = True
        with col2:
            if st.button("New user? Register now"):
                switch_tab("Register")

        if st.session_state.show_forgot_password:
            with st.popover("Reset Password", use_container_width=True):
                st.subheader("Reset Your Password")
                reset_identifier = st.text_input("Username/Email", key="reset_identifier")
                new_password = st.text_input("New Password", type="password", key="new_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                st.markdown(
                    """
                    <span style="font-size:13px; color:gray;">
                    <b>Password Requirements:</b>
                    <ul>
                        <li>Minimum 8 characters</li>
                        <li>At least one uppercase letter (A-Z)</li>
                        <li>At least one lowercase letter (a-z)</li>
                        <li>At least one digit (0-9)</li>
                        <li>At least one special character (!@#$%^&*(),.?\":{}|<>)</li>
                    </ul>
                    </span>
                    """,
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns([1,1])
                with col2:
                    if st.button("Close"):
                        st.session_state.show_forgot_password = False
                        st.rerun()
                with col1:
                    if st.button("Confirm Reset"):
                        if not reset_identifier:
                            st.error("Please enter your username/email")
                        elif not is_valid_password(new_password):
                            st.error("Password doesn't meet the required criteria")
                        elif not new_password or not confirm_password:
                            st.error("Please enter and confirm your new password")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif not is_valid_password(new_password):
                            st.error("Password doesn't meet requirements")
                        else:
                            user_exists = check_user_exists(reset_identifier)
                            if not user_exists:
                                st.error("Username/Email not found")
                            else:
                                update_password(reset_identifier, new_password)
                                st.success("Password updated successfully!")
                                time.sleep(1)
                                st.session_state.show_forgot_password = False
                                st.rerun()

        login_error_placeholder = st.empty()
        if 'login_failed' in st.session_state and st.session_state.login_failed:
            login_error_placeholder.warning("❌ Invalid credentials. Please try again.")

        if st.button("Login"):
            user = verify_user(identifier, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
                st.success(f"✅ Welcome {user['firstname']}! Redirecting to SmartSafar...")
                st.session_state.login_failed = False
                st.rerun()
            else:
                st.session_state.login_failed = True
                st.rerun()

    with tab2:
        st.subheader("User Registration")
        fname = st.text_input("First Name", key="reg_fname")
        lname = st.text_input("Last Name", key="reg_lname")
        uname = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        phone = st.text_input("Phone Number", key="reg_phone")
        pwd = st.text_input("Password", type="password", key="reg_password")

        st.markdown(
            """
            <span style="font-size:13px; color:gray;">
            <b>Password Requirements:</b>
            <ul>
                <li>Minimum 8 characters</li>
                <li>At least one uppercase letter (A-Z)</li>
                <li>At least one lowercase letter (a-z)</li>
                <li>At least one digit (0-9)</li>
                <li>At least one special character (!@#$%^&*(),.?\":{}|<>)</li>
            </ul>
            </span>
            """,
            unsafe_allow_html=True
        )

        if st.button("Old User? Login"):
            switch_tab("Login")
        
        phone_placeholder = st.empty()
        password_placeholder = st.empty()

        if st.button("Register"):
            if not is_valid_phone(phone):
                phone_placeholder.error("❌ Enter valid Phone Number.")
            if not is_valid_password(pwd):
                password_placeholder.error("❌ Password doesn't meet the required criteria.")
            else:
                success, message = register_user(fname, lname, uname, email, phone, pwd)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.experimental_set_query_params(tab="login")
                    st.rerun()
                else:
                    st.error(message)

# --------- TRAVEL PLANNER PAGE ---------
else:
    st.sidebar.subheader(f"👤 Logged in as: {st.session_state.username}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.subheader("🌍 Plan Your Next Trip!")
    
    city = st.text_input("Enter the city for your trip", placeholder="e.g., Ahmedabad", key="trip_city")
    interests = st.text_input("Enter your interests (comma-separated)", placeholder="e.g., Food, Culture, Adventure", key="trip_interests")

    if st.button("Generate Itinerary"):
        state = {"messages": [], "city": "", "interests": [], "itinerary": ""}
        state = input_city(city, state)
        state = input_interests(interests, state)

        itinerary = create_itinerary(state)
        weather = get_weather(city)
        fact = fun_fact(city)

        log_interaction(f"City: {city}, Interests: {interests}", f"Itinerary: {itinerary}, Weather: {weather}, Fun Fact: {fact}")

        st.markdown(itinerary, unsafe_allow_html=True)
        st.write(weather)
        st.write(fact)
