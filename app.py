import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from datetime import datetime
from PIL import Image

# 1. PAGE CONFIGURATION (The Title)
st.set_page_config(page_title="My AI Finance Tracker", layout="wide", page_icon="💰")

# 2. SETUP DATA STORAGE (Memory)
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# 3. SIDEBAR (The Control Panel)
with st.sidebar:
    st.title("💸 FinanceAI")
    st.markdown("---")
    
    # Secure Password Field for API Key
    api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.markdown("---")
    view = st.radio("Navigate", ["Dashboard", "Log Expense", "Receipt Scanner"])
    
    st.markdown("---")
    if st.button("Clear All Data"):
        st.session_state.transactions = []
        st.rerun()

# 4. AI FUNCTIONS (The Logic)
def analyze_receipt_image(image_file, key):
    """Sends image to Gemini to read the receipt"""
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Analyze this receipt image. Extract all items purchased.
    Return ONLY a JSON list. For each item, find:
    - description (what is it?)
    - amount (number only)
    - category (Food, Transport, Tech, Utilities, Other)
    - date (YYYY-MM-DD)
    """
    
    try:
        img = Image.open(image_file)
        response = model.generate_content([prompt, img])
        # Clean up the AI response to get just the JSON data
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return []

def get_dashboard_insights(data, key):
    """Sends data to Gemini for financial advice"""
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Here is my recent spending data: {json.dumps(data)}
    Give me 3 short, bullet-pointed tips to save money based on this.
    Be direct and helpful.
    """
    response = model.generate_content(prompt)
    return response.text

# 5. THE MAIN SCREEN LOGIC

if not api_key:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar to start!")
    st.stop()

# --- VIEW 1: DASHBOARD ---
if view == "Dashboard":
    st.header("📊 Financial Overview")
    
    if len(st.session_state.transactions) > 0:
        # Calculate Totals
        df = pd.DataFrame(st.session_state.transactions)
        total_spent = df['amount'].sum()
        
        # Display Big Numbers
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Spent", f"${total_spent:.2f}")
        col1.metric("Transactions", len(df))
        
        # Charts
        st.subheader("Spending by Category")
        st.bar_chart(df, x="category", y="amount")
        
        # Recent List
        st.subheader("Recent History")
        st.dataframe(df, use_container_width=True)
        
        # AI Insights
        st.markdown("---")
        st.subheader("🤖 AI Financial Advisor")
        if st.button("Generate New Insights"):
            with st.spinner("Analyzing your spending habits..."):
                advice = get_dashboard_insights(st.session_state.transactions, api_key)
                st.success("Analysis Complete!")
                st.markdown(advice)
    else:
        st.info("No data yet. Go to 'Log Expense' or 'Receipt Scanner' to add some!")

# --- VIEW 2: LOG EXPENSE (Manual) ---
elif view == "Log Expense":
    st.header("📝 Add Transaction")
    
    with st.form("manual_add"):
        desc = st.text_input("Description (e.g., Coffee)")
        amt = st.number_input("Amount ($)", min_value=0.01, format="%.2f")
        cat = st.selectbox("Category", ["Food", "Transport", "Tech", "Utilities", "Other"])
        date = st.date_input("Date")
        
        if st.form_submit_button("Add Expense"):
            new_tx = {
                "description": desc,
                "amount": amt,
                "category": cat,
                "date": str(date)
            }
            st.session_state.transactions.append(new_tx)
            st.success("Added successfully!")

# --- VIEW 3: RECEIPT SCANNER (AI Vision) ---
elif view == "Receipt Scanner":
    st.header("📸 AI Receipt Scanner")
    st.write("Upload a photo of a receipt, and AI will type it in for you.")
    
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        # Show the image
        st.image(uploaded_file, caption="Uploaded Receipt", width=300)
        
        if st.button("Analyze Receipt"):
            with st.spinner("AI is reading the receipt..."):
                items = analyze_receipt_image(uploaded_file, api_key)
                
                if items:
                    st.write("### I found these items:")
                    # Allow user to edit before saving
                    edited_df = st.data_editor(pd.DataFrame(items), num_rows="dynamic")
                    
                    if st.button("Save These Items"):
                        # Convert back to list and save
                        new_items = edited_df.to_dict('records')
                        st.session_state.transactions.extend(new_items)
                        st.success(f"Saved {len(new_items)} items to your database!")
