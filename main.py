import streamlit as st
import json
import os
import uuid
from datetime import date
import time
import pandas as pd

# --- FILE CONFIGURATION ---
USER_FILE = 'users.json'
PRAYER_RECORDS_FILE = 'namaz_records.json'

# --- SESSION STATE INITIALIZATION ---
if 'role' not in st.session_state:
    st.session_state.role = None
if 'page' not in st.session_state:
    st.session_state.page = 'role_selection'
if 'current_child_id' not in st.session_state:
    st.session_state.current_child_id = None
if 'current_child_name' not in st.session_state:
    st.session_state.current_child_name = None
if 'last_prayer_selected' not in st.session_state:
    st.session_state.last_prayer_selected = None

# --- FILE HANDLING FUNCTIONS ---

def load_user_data():
    """Loads user data (key and children) from the JSON file."""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Handle empty or corrupted file by returning an empty dict
            return {} 
    return {}

def save_user_data(data):
    """Saves user data to the JSON file."""
    with open(USER_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_prayer_records():
    """Loads prayer records from the JSON file."""
    if os.path.exists(PRAYER_RECORDS_FILE):
        try:
            with open(PRAYER_RECORDS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Handle empty or corrupted file by returning an empty dict
            return {}
    return {}

def save_prayer_records(records):
    """Saves prayer records to the JSON file."""
    with open(PRAYER_RECORDS_FILE, 'w') as f:
        json.dump(records, f, indent=4)

# --- UTILITY/NAVIGATION FUNCTIONS ---

def get_daily_prayer_times():
    """Returns dummy prayer times for the current date."""
    # Note: Times are dummy data, replace with API integration in final app
    return {
        "date": str(date.today()),
        "Fajr": "05:45 AM",
        "Dhuhr": "12:35 PM",
        "Asr": "03:45 PM",
        "Maghrib": "05:15 PM",
        "Isha": "07:00 PM"
    }

def set_role(selected_role):
    """Function to update the role and switch the page."""
    st.session_state.role = selected_role
    
    user_data = load_user_data()
    children_list = user_data.get('children', [])
    
    # --- UPDATED PARENT FLOW ---
    if selected_role == 'parent':
        if 'parent_key' in user_data and user_data['parent_key']:
            st.session_state.page = 'parent_login'
        else:
            st.session_state.page = 'parent_setup'
    # --- CHILD FLOW ---        
    elif selected_role == 'child':
        if children_list:
            st.session_state.page = 'child_selection' 
        else:
            st.session_state.page = 'child_not_registered' 
    
    st.rerun()

# ----------------------------------------------------------------------
# CHILD RENDER FUNCTIONS
# ----------------------------------------------------------------------

        

def render_child_tracker_page():
    
    child_id = st.session_state.current_child_id
    child_name = st.session_state.current_child_name

    # 1. Sidebar Navigation Setup
    st.sidebar.title("Namaz Tracker Menu")
    st.sidebar.markdown(f"**Current User:** **{child_name}**")
    st.sidebar.markdown("---")

    selected_option = st.sidebar.radio(
        "Select an Action:",
        ('Prayer Timings', 'Mark a Prayer'),
        key='sidebar_nav'
    )

    if st.sidebar.button('⬅️ Log Out'):
        st.session_state.page = 'role_selection'
        st.session_state.current_child_id = None
        st.session_state.current_child_name = None
        st.session_state.last_prayer_selected = None
        st.rerun()
        return

    st.title(f"Child Dashboard: {selected_option}")
    st.markdown("---")

    # 2. Render Page Content based on Sidebar Selection
    if selected_option == 'Prayer Timings':
        render_prayer_timings(child_id)
    
    elif selected_option == 'Mark a Prayer':
        render_mark_prayer(child_id)


def render_prayer_timings(child_id):
    """Displays today's prayer timings in a clean format."""
    st.header("Today's Prayer Schedule 🗓️")
    prayer_times = get_daily_prayer_times()
    today = prayer_times['date']
    
    records = load_prayer_records().get(child_id, {}).get(today, {})

    # Create the column headers
    col_names = st.columns(3)
    col_names[0].subheader("Prayer")
    col_names[1].subheader("Time")
    col_names[2].subheader("Status")

    st.markdown("---")

    for name in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        time_str = prayer_times[name]
        status_data = records.get(name)
        
        status_text = "⏳ Pending"
        color = "gray"
        
        if status_data:
            is_prayed = status_data.get('is_prayed')
            method = status_data.get('method')
            
            if is_prayed is True:
                if method in ["Alone", "Masjid"]:
                    status_text = f"✅ Prayed ({method})"
                    color = "green"
                elif method == 'Kaza':
                    status_text = "🟠 Kaza / Make-up"
                    color = "orange"
                    
            elif is_prayed is False and method == 'Missed':
                status_text = "❌ Missed Today"
                color = "red"
        
        with st.container(border=True):
            cols = st.columns(3)
            cols[0].markdown(f"**{name}**")
            cols[1].code(time_str) 
            cols[2].markdown(f":{color}[**{status_text}**]")
            
            

def render_mark_prayer(child_id):
    """Allows the child to log a prayer status with separated data fields."""
    st.header("Record Your Prayer 🙏")
    
    today = str(date.today())
    all_records = load_prayer_records()
    child_records = all_records.get(child_id, {})
    daily_records = child_records.get(today, {})
    
    # 1. Select the Prayer
    prayer_names = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    selected_prayer = st.selectbox(
        "Which prayer are you marking?",
        options=['-- Select Prayer --'] + prayer_names,
        key='prayer_select'
    )
    
    if selected_prayer != '-- Select Prayer --':
        st.info(f"You are recording status for **{selected_prayer}**.")
        
        # --- Session State Setup ---
        OVERWRITE_KEY = f'show_form_{selected_prayer}'
        JUST_SAVED_KEY = f'just_saved_{selected_prayer}'
        
        # --- State Reset on Prayer Change ---
        if 'last_prayer_selected' not in st.session_state or st.session_state.last_prayer_selected != selected_prayer:
            if OVERWRITE_KEY in st.session_state: del st.session_state[OVERWRITE_KEY]
            if JUST_SAVED_KEY in st.session_state: del st.session_state[JUST_SAVED_KEY]
            st.session_state.last_prayer_selected = selected_prayer
        
        # Check if we just saved the current prayer (Highest priority flag)
        just_saved = st.session_state.get(JUST_SAVED_KEY, False)
        
        if just_saved:
            daily_records_after_save = load_prayer_records().get(child_id, {}).get(today, {})
            
            st.success(f"Successfully recorded **{selected_prayer}**! Method: **{daily_records_after_save.get(selected_prayer, {}).get('method')}**")
            del st.session_state[JUST_SAVED_KEY]
            
            return
            
        # --- Check if marked and if form should be visible ---
        is_marked = selected_prayer in daily_records
        current_data = daily_records.get(selected_prayer, {})
        allow_overwrite = st.session_state.get(OVERWRITE_KEY, False)

        # 2. Handle Already Marked Scenario (Hide form unless overwrite is requested)
        if is_marked and not allow_overwrite:
            
            prayed_status = 'Prayed' if current_data.get('is_prayed') else 'Missed'
            
            st.warning(f"This prayer is **already marked**!")
            st.markdown(f"**Current Status:** {prayed_status} **({current_data.get('method', 'N/A')})** at {current_data.get('time', 'N/A')}")
            
            if st.button("🔄 **Change/Overwrite Status**", key=f'btn_overwrite_{selected_prayer}'):
                st.session_state[OVERWRITE_KEY] = True
                st.rerun()
            
            return
            
        # --- Form Rendering Logic (Only runs if not marked OR overwrite is allowed) ---
        
        if allow_overwrite:
            st.subheader("⚠️ Overwrite Mode Activated")
            
        # 3. Select Primary Status: Prayed or Missed?
        primary_status = st.radio(
            f"Was {selected_prayer} performed today?",
            options=['Yes, I prayed it.', 'No, I missed it.'],
            key='primary_status_select'
        )

        final_is_prayed = (primary_status == 'Yes, I prayed it.')
        final_method = None
        
        # 4. Conditional Secondary Selection
        if primary_status == 'Yes, I prayed it.':
            st.subheader("How was the prayer performed?")
            method_options = {
                "In Masjid (Congregation)": "Masjid",
                "Alone (Individual)": "Alone",
                "As Qada (Make-up)": "Kaza"
            }
            selected_method_key = st.radio(
                "Select the method:",
                options=list(method_options.keys()),
                key='method_select'
            )
            final_method = method_options[selected_method_key]
            
        elif primary_status == 'No, I missed it.':
            final_method = "Missed"

        
        # 5. Save Button and Logic
        if st.button(f'Record {selected_prayer} Status'):
            
            new_record = {
                "is_prayed": final_is_prayed,
                "method": final_method,
                "time": str(time.strftime("%H:%M")) if final_is_prayed else None 
            }
            
            if child_id not in all_records: all_records[child_id] = {}
            if today not in all_records[child_id]: all_records[child_id][today] = {}
            all_records[child_id][today][selected_prayer] = new_record
            save_prayer_records(all_records)
            
            # --- Set the "Just Saved" flag and clean up other flags ---
            st.session_state[JUST_SAVED_KEY] = True
            
            if OVERWRITE_KEY in st.session_state:
                del st.session_state[OVERWRITE_KEY]
            # --- End Flag Setting ---
            
            st.rerun()

# ----------------------------------------------------------------------
# PARENT RENDER FUNCTIONS
# ----------------------------------------------------------------------
import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
# NOTE: The load_prayer_records function is assumed to be defined elsewhere
# from your main script, as well as the prayer_records structure.

def render_weekly_performance_metrics(child_id):
    """
    Calculates and displays key performance metrics for the current calendar week, 
    starting Monday and accumulating up to today.
    """
    st.header("This Week's Performance 🚀")
    st.markdown("---")

    all_records = load_prayer_records()
    child_records = all_records.get(child_id, {})
    
    if not child_records:
        st.info("No records available for this child.")
        return

    today = date.today()
    
    # Calculate the start of the week (Monday is 0, Sunday is 6)
    # timedelta(days=today.weekday()) calculates how many days ago the last Monday was.
    start_date = today - timedelta(days=today.weekday())
    
    # Initialize counters
    total_prayed = 0
    total_missed = 0
    prayed_on_time = 0
    prayed_kaza = 0
    
    # Dynamic denominator based on the number of days from Monday up to today (inclusive)
    total_days_elapsed_this_week = 0

    current_date = start_date
    while current_date <= today:
        # This counter will be 1 on Monday, 2 on Tuesday, 3 on Wednesday, etc.
        total_days_elapsed_this_week += 1 
        
        date_str = str(current_date)
        daily_prayers = child_records.get(date_str, {})
        
        # Check all 5 expected prayers for the day
        for prayer_name in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
            data = daily_prayers.get(prayer_name)
            
            if data and 'method' in data:
                method = data['method']
                is_prayed = data.get('is_prayed')
                
                if is_prayed is False and method == 'Missed':
                    total_missed += 1
                elif is_prayed is True:
                    total_prayed += 1
                    if method in ["Masjid", "Alone"]:
                        prayed_on_time += 1
                    elif method == "Kaza":
                        prayed_kaza += 1
        
        current_date += timedelta(days=1)
        
    # --- DYNAMIC CALCULATION OF MAX POSSIBLE PRAYERS ---
    # Max possible is 5 * the number of days that have passed this week.
    MAX_POSSIBLE_PRAYERS = 5 * total_days_elapsed_this_week
    
    
    if MAX_POSSIBLE_PRAYERS > 0:
        # Calculate completion based on the current maximum possible prayers (e.g., 5, 10, 15...)
        average_completion = (total_prayed / MAX_POSSIBLE_PRAYERS) * 100
        
        # Combined on-time and Kaza breakdown (as a single metric)
        on_time_kaza_ratio = f"{prayed_on_time} / {prayed_kaza}"
        
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Average Weekly Completion",
                value=f"{average_completion:.1f}%",
                delta=f"Out of {MAX_POSSIBLE_PRAYERS} prayers possible" 
            )

        with col2:
            st.metric(
                label="Total Prayed (This Week)",
                value=total_prayed
            )
            
        with col3:
            st.metric(
                label="Total Prayers Missed",
                value=total_missed
            )

        with col4:
            st.metric(
                label="On Time / Kaza Breakdown",
                value=on_time_kaza_ratio,
                help="Prayed On Time (Masjid/Alone) / Kaza (Make-up)"
            )

    else:
        st.info("Start recording prayers to see weekly performance data.")

def render_parent_manage_child():
    st.title("Manage Child Profiles 👨‍👩‍👧‍👦")
    st.markdown("---")
    
    user_data = load_user_data()
    children = user_data.get('children', [])

    # 1. ADD CHILD SECTION (Calling the existing function logic)
    st.subheader("Add a New Child Profile")
    
    with st.form("add_child_form_manage", clear_on_submit=True):
        child_name = st.text_input('Child\'s Name', max_chars=30, key='new_child_name_input_manage')
        
        submit_button = st.form_submit_button('➕ Create Profile')

        if submit_button:
            if child_name:
                child_id = str(uuid.uuid4())[:8] 
                
                new_child = {"name": child_name.strip(), "id": child_id}
                
                if 'children' not in user_data:
                    user_data['children'] = []
                
                user_data['children'].append(new_child)
                save_user_data(user_data)
                
                st.success(f"Profile for **{child_name.strip()}** created! ID: `{child_id}`")
                
                # Rerun to update the list below
                st.session_state.page = 'parent_manage_child'
                st.rerun()
            else:
                st.error("Please enter a name for the child.")

    st.markdown("---")
    
    # 2. REMOVE CHILD SECTION
    st.subheader("Remove/View Existing Profiles")
    
    if not children:
        st.info("No child profiles have been created yet.")
    else:
        # Create a DataFrame for clear display
        df = pd.DataFrame(children)
        df.index = df.index + 1 # Start index at 1
        df.columns = ['Name', 'Login ID']
        st.dataframe(df, use_container_width=True)
        
        # Select box for deletion
        child_names_to_delete = {child['name']: child['id'] for child in children}
        
        child_to_delete_name = st.selectbox(
            "Select a profile to permanently delete:",
            options=['-- Select Child --'] + sorted(list(child_names_to_delete.keys())),
            key='delete_child_select'
        )
        
        if child_to_delete_name != '-- Select Child --':
            child_id_to_delete = child_names_to_delete[child_to_delete_name]
            
            if st.button(f'🗑️ Confirm Delete: {child_to_delete_name}'):
                # Filter out the child to be deleted
                user_data['children'] = [
                    child for child in children if child['id'] != child_id_to_delete
                ]
                save_user_data(user_data)
                
                st.warning(f"Profile for **{child_to_delete_name}** has been deleted.")
                
                # OPTIONAL: Also delete their prayer records for a clean sweep
                prayer_records = load_prayer_records()
                if child_id_to_delete in prayer_records:
                    del prayer_records[child_id_to_delete]
                    save_prayer_records(prayer_records)
                    st.info(f"Associated prayer records were also removed.")
                
                # Rerun to update the list
                st.session_state.page = 'parent_manage_child'
                st.rerun()

    st.markdown("---")
    if st.button('⬅️ Back to Dashboard'):
        st.session_state.page = 'parent_dashboard'
        st.rerun()

def render_parent_setup():
    st.title('Parent Setup: Create Secret Key 🔑')
    st.warning('This key will protect the parent settings. Keep it secure!')
    
    new_key = st.text_input('Enter New 4-Digit Secret Key (e.g., 1234)', type="password", max_chars=4, key='parent_setup_key_input')
    
    if st.button('Save Key and Continue'):
        if len(new_key) == 4 and new_key.isdigit():
            user_data = {'parent_key': new_key, 'children': []}
            save_user_data(user_data)
            st.success('Secret Key set successfully! Proceeding to the dashboard to add children.')
            st.session_state.page = 'parent_dashboard'
            st.rerun()
        else:
            st.error('Please enter a valid 4-digit key.')

def render_parent_login():
    st.title('Parent Login 🔒')
    
    entered_key = st.text_input('Enter Secret Key', type="password", max_chars=4, key='parent_login_key_input')
    
    if st.button('Login'):
        user_data = load_user_data()
        correct_key = user_data.get('parent_key')
        
        if entered_key == correct_key:
            st.session_state.page = 'parent_dashboard'
            st.rerun()
        else:
            st.error('Incorrect Secret Key. Please try again.')

import plotly.express as px # Import Plotly for advanced charting

import plotly.express as px

def render_daily_method_bar_chart(child_id, prayer_records):
    """
    Renders a stacked bar chart showing the count of each prayer method (Masjid, Alone, Missed, etc.) 
    for all 5 prayers on each day, across the entire tracked period.
    """
    st.subheader("Daily Prayer Method Breakdown")
    
    if not prayer_records:
        st.info("No records available to generate a daily method breakdown chart.")
        return

    method_data = []
    
    for date_str, daily_prayers in prayer_records.items():
        for prayer_name, data in daily_prayers.items():
            if data and 'method' in data:
                method_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Prayer': prayer_name,
                    'Method': data['method']
                })

    df_methods = pd.DataFrame(method_data)
    
    if df_methods.empty:
        st.info("No completed prayer records to display methods.")
        return

    # Count the occurrence of each method per day
    df_methods_grouped = df_methods.groupby(['Date', 'Method']).size().reset_index(name='Count')
    
    fig = px.bar(
        df_methods_grouped, 
        x='Date', 
        y='Count', 
        color='Method',
        title='Total Methods Used Per Day',
        labels={'Count': 'Number of Prayers', 'Date': 'Day'},
        # Order methods for better visualization
        category_orders={"Method": ["Masjid", "Alone", "Kaza", "Missed"]},
        height=400
    )
    
    fig.update_xaxes(dtick="D1", tickformat="%b %d") # Ensure one tick per day
    fig.update_layout(barmode='stack', legend_title_text='Method')
    
    st.plotly_chart(fig, use_container_width=True)
    
def render_parent_dashboard():
    st.title('Parent Dashboard 📊')
    
    if st.button('Manage Child Profiles'):
        st.session_state.page = 'parent_manage_child'
        st.rerun()
    
    
    user_data = load_user_data()
    children = user_data.get('children', [])
    
    # ... (Sidebar and Child Selection logic remains the same) ...
    
    child_names_map = {child['name']: child['id'] for child in children}
    selected_child_name = st.sidebar.selectbox(
        'Select Child to View Progress:',
        options=['-- Select Child --'] + sorted(list(child_names_map.keys())),
        key='parent_child_select'
    )
    
    if selected_child_name != '-- Select Child --':
        child_id = child_names_map[selected_child_name]
        st.header(f"Progress Report for {selected_child_name}")
        st.markdown("---")
        
        prayer_records = load_prayer_records().get(child_id, {})
        
        if not prayer_records:
            st.info(f"No prayer records found for **{selected_child_name}** yet. Ask them to mark a prayer!")
            
        else:
            # ... (Code to create and display the 'Daily Prayer History' DataFrame remains the same) ...
            
            # --- START OF CHARTING SECTION ---
            render_weekly_performance_metrics(child_id)
            st.subheader("Summary of Prayer Methods")
            # Aggregate method counts across all days    
            all_methods = [
                prayer['method'] 
                for date_records in prayer_records.values() 
                for prayer in date_records.values() 
                if prayer and 'method' in prayer
            ]
            
            method_counts = pd.Series(all_methods).value_counts().rename('Count')
            
            if not method_counts.empty:
                st.bar_chart(method_counts)
            
            st.markdown("---") # Visual separator between charts

            # --- CALL THE NEW LINE CHART FUNCTION HERE ---
            render_daily_method_bar_chart(child_id, prayer_records)
            
    st.sidebar.markdown("---")
    if st.sidebar.button('⬅️ Log Out / Change Role'):
        st.session_state.page = 'role_selection'
        st.session_state.role = None
        st.rerun()  
def authenticate_child(child_id: str, child_pass: str, children_list):
    """
    Checks if the provided ID and Password match any child record.
    Returns True if successful, otherwise False.
    """
    for child in children_list:
        if child["id"] == child_id and child["pass"] == child_pass:
            return True
    return False

# ----------------------------------------------------------------------
# CHILD LOGIN FUNCTION
# ----------------------------------------------------------------------

def render_child_login():
    """
    Renders the password input form for the selected child and handles authentication.
    """
    child_name = st.session_state.current_child_name
    child_id = st.session_state.current_child_id
    
    st.header(f'Login for {child_name}')
    
    # Input field for the password
    password = st.text_input(
        "Enter your password:", 
        type="password", 
        key='child_login_password'
    )
    
    # Login button
    if st.button(f'Log in as {child_name}'):
        user_data = load_user_data()
        children_list = user_data.get('children', [])
        
        # Perform authentication
        if authenticate_child(child_id, password, children_list):
            st.session_state.logged_in = True
            st.session_state.role = 'child'
            st.session_state.page = 'child_tracker'
            st.success(f"Welcome back, {child_name}! Redirecting to tracker...")
            # Use st.rerun() to immediately transition to the tracker page
            st.rerun()
        else:
            st.error("❌ Incorrect password. Please try again.")
            
    # Back button to select a different profile
    if st.button('⬅️ Select a different profile'):
        # Clear sensitive session state and go back to selection
        del st.session_state.current_child_id
        del st.session_state.current_child_name
        st.session_state.page = 'child_selection'
        st.rerun()          

# ----------------------------------------------------------------------
# MAIN PAGE RENDERING BLOCK
# ----------------------------------------------------------------------

if st.session_state.page == 'role_selection':
    st.title('Welcome to the Namaz Tracker! 🕌')
    st.header('Who is using the app?')
    
    user_choice = st.radio(
        "Please select your role:",
        ('Parent', 'Child'),
        index=None,
        key='user_role_select'
    )

    if user_choice:
        if st.button(f'Continue as {user_choice}'):
            set_role(user_choice.lower())

# ----------------------------------------------------------------------
# PARENT PAGES
# ----------------------------------------------------------------------
elif st.session_state.page == 'parent_setup':
    render_parent_setup()
elif st.session_state.page == 'parent_login':
    render_parent_login()
elif st.session_state.page == 'parent_dashboard':
    render_parent_dashboard()
elif st.session_state.page == 'parent_manage_child':
    render_parent_manage_child()

# ----------------------------------------------------------------------
# CHILD PAGES
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# CHILD PAGES (REVISED FLOW)
# ----------------------------------------------------------------------
elif st.session_state.page == 'child_selection':
    st.title('Select Your Profile 👧🏽')
    
    user_data = load_user_data()
    children_list = user_data.get('children', [])
    
    # Create a dictionary for mapping names to IDs
    child_names = {child['name']: child['id'] for child in children_list}
    
    selected_name = st.selectbox(
        'Who are you?',
        options=['-- Select Name --'] + sorted(list(child_names.keys()))
    )
    
    if selected_name != '-- Select Name --':
        # Store selected child info in session state
        st.session_state.current_child_id = child_names[selected_name]
        st.session_state.current_child_name = selected_name
        
        # Button to move to the password screen
        if st.button(f'Continue as {selected_name}'):
             # Change page state to dedicated login page
            st.session_state.page = 'child_password_login' 
            st.rerun()

# ----------------------------------------------------------------------
# NEW CHILD PASSWORD LOGIN PAGE
# ----------------------------------------------------------------------
elif st.session_state.page == 'child_password_login':
    # Call the new function to render the login form
    render_child_login()
    
elif st.session_state.page == 'child_not_registered':
    st.title('You Need to Register! 🛑')
    # ... (rest of the child_not_registered code)
    
elif st.session_state.page == 'child_tracker':
    render_child_tracker_page()    
