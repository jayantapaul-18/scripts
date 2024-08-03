import streamlit as st
from streamlit_option_menu import option_menu

# Set page configuration
st.set_page_config(
    page_title="Streamlit Layout App",
    layout="wide"
)

# Custom CSS to style the app
st.markdown("""
    <style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    .css-1d391kg { 
        padding: 1rem; 
    }
    .css-18e3th9 { 
        flex-direction: row; 
        justify-content: space-around;
    }
    .css-1d3hvh { 
        flex-direction: row; 
        justify-content: space-around;
    }
    </style>
    """, unsafe_allow_html=True)

# Create a top menu
selected_top = option_menu(
    menu_title=None, 
    options=["Home", "Settings", "About"], 
    icons=["house", "gear", "info-circle"], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f5f5f5"},
        "icon": {"color": "orange", "font-size": "18px"},
        "nav-link": {"font-size": "18px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "green"},
    }
)

# Create a sidebar (left menu)
with st.sidebar:
    selected_left = option_menu(
        menu_title="Main Menu", 
        options=["Option 1", "Option 2", "Option 3"], 
        icons=["list-task", "clipboard-data", "card-checklist"], 
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#f5f5f5"},
            "icon": {"color": "blue", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "blue"},
        }
    )

# Main content based on the selected top menu
if selected_top == "Home":
    st.title("Home")
    st.write("Welcome to the Home page!")
elif selected_top == "Settings":
    st.title("Settings")
    st.write("Here you can adjust your settings.")
else:
    st.title("About")
    st.write("Learn more about this app.")

# Additional content based on the selected left menu
if selected_left == "Option 1":
    st.write("You selected Option 1 from the sidebar.")
elif selected_left == "Option 2":
    st.write("You selected Option 2 from the sidebar.")
else:
    st.write("You selected Option 3 from the sidebar.")

# Arrange buttons
st.subheader("Button Arrangement")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("Button 1")
with col2:
    st.button("Button 2")
with col3:
    st.button("Button 3")
