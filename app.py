import streamlit as st
import pandas as pd
import predictor
import pdf_generator
import io
import base64
import random
import string

st.set_page_config(
    page_title="CCMT Admission Predictor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1a237e;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #3949ab;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 5px solid #1a237e;
        padding: 1rem;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #1a237e;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #3949ab;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .download-btn {
        text-decoration: none;
        background-color: #4CAF50;
        color: white !important;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        text-align: center;
    }
    .download-btn:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎓 CCMT Admission Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Predict your M.Tech admission chances based on 2024 & 2025 cutoff data</div>', unsafe_allow_html=True)

# Load Data
@st.cache_data
def get_data():
    return predictor.load_data()

try:
    df = get_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar Inputs
st.sidebar.header("🎯 Your Details")

gate_score = st.sidebar.number_input("GATE Score", min_value=0, max_value=1000, value=500, step=10)

papers = predictor.get_gate_papers()
gate_paper = st.sidebar.selectbox("GATE Paper", options=papers)

categories = predictor.get_categories(df)
category = st.sidebar.selectbox("Category", options=categories)

rounds = predictor.get_rounds(df)
round_name = st.sidebar.selectbox("CCMT Round", options=rounds)

# Program Multi-Select based on GATE paper
available_programs = predictor.get_programs_for_paper(gate_paper, df)
selected_programs = st.sidebar.multiselect(
    "Preferred M.Tech Programs (Optional)", 
    options=available_programs,
    help="Leave blank to search all programs eligible for your GATE paper."
)
if not selected_programs:
    selected_programs_filter = available_programs
else:
    selected_programs_filter = selected_programs

st.sidebar.markdown("---")
top_n = st.sidebar.number_input("Number of Recommendations", min_value=1, max_value=10000, value=25, step=5, help="Increase this to see more recommendations")

if st.sidebar.button("Predict Colleges 🚀", use_container_width=True):
    with st.spinner("Analyzing past trends..."):
        results_df = predictor.predict(
            gate_score=gate_score,
            gate_paper=gate_paper,
            category=category,
            round_name=round_name,
            selected_programs=selected_programs_filter,
            df=df,
            top_n=top_n
        )
        
    if results_df.empty:
        st.warning("No colleges found matching your criteria. Try relaxing your program filters or selecting a different round/category.")
    else:
        st.success(f"Found {len(results_df)} top recommendations for you!")
        
        # Display Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card"><strong>Highest Chance</strong><br><span style="font-size:1.5rem;color:#2e7d32">{results_df["Probability"].max()}%</span></div>', unsafe_allow_html=True)
        with col2:
            safe_count = sum(results_df["Chance"].str.contains("Safe"))
            st.markdown(f'<div class="metric-card"><strong>Safe Options</strong><br><span style="font-size:1.5rem;color:#1a237e">{safe_count}</span></div>', unsafe_allow_html=True)
        with col3:
            avg_2025 = pd.to_numeric(results_df['Close_2025'], errors='coerce').mean()
            st.markdown(f'<div class="metric-card"><strong>Avg Cutoff (2025)</strong><br><span style="font-size:1.5rem;color:#e65100">{avg_2025:.1f}</span></div>', unsafe_allow_html=True)
            
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Display Table
        st.subheader(f"🏛️ Top {top_n} Recommendations")
        
        # Style the dataframe for display
        def highlight_chance(val):
            if "Extremely" in str(val) or "Very Safe" in str(val):
                return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold;'
            elif "Safe" in str(val):
                return 'background-color: #f1f8e9; color: #33691e; font-weight: bold;'
            elif "Moderate" in str(val):
                return 'background-color: #fff8e1; color: #f57f17; font-weight: bold;'
            elif "Dream" in str(val):
                return 'background-color: #ffebee; color: #b71c1c; font-weight: bold;'
            return ''
            
        display_cols = ["Institute", "Program", "Close_2025", "Close_2024", "Probability", "Chance"]
        styled_df = results_df[display_cols].style.map(highlight_chance, subset=['Chance'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600,
            column_config={
                "Institute": st.column_config.TextColumn("Institute", width="large"),
                "Program": st.column_config.TextColumn("Program", width="medium"),
                "Close_2025": st.column_config.NumberColumn("Closing (2025)"),
                "Close_2024": st.column_config.NumberColumn("Closing (2024)"),
                "Probability": st.column_config.NumberColumn("Admission Prob (%)", format="%.1f%%"),
                "Chance": st.column_config.TextColumn("Admission Chance"),
            }
        )
        
        # Export Options
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📥 Download Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # PDF Generation
            try:
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                pdf_password = "".join(random.choices(alphabet, k=16))
                pdf_bytes = pdf_generator.generate_pdf(
                    gate_score=gate_score,
                    gate_paper=gate_paper,
                    category=category,
                    round_name=round_name,
                    result_df=results_df,
                    password=pdf_password
                )
                b64 = base64.b64encode(pdf_bytes).decode()
                st.info(f"🔒 PDF Password: **{pdf_password}** (Copy this before downloading)")
                href = f'<a href="data:application/pdf;base64,{b64}" download="CCMT_Admission_Report.pdf" class="download-btn">📄 Download PDF Report</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")
                
        with col2:
            # Excel Generation
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                results_df.to_excel(writer, index=False, sheet_name='Predictions')
            b64_excel = base64.b64encode(buffer.getvalue()).decode()
            href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="CCMT_Predictions.xlsx" class="download-btn" style="background-color:#217346;">📊 Download Excel Data</a>'
            st.markdown(href_excel, unsafe_allow_html=True)

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.info(
    "**Disclaimer:** This is a predictive model based on past data (2024 & 2025). "
    "Actual cutoffs may vary. Always refer to official CCMT guidelines."
)
