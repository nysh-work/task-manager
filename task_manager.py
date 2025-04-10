import streamlit as st
import sqlite3
from datetime import datetime
import plotly.express as px
import requests
from dateutil.relativedelta import relativedelta
from datetime import timedelta


# Initialize database
conn = sqlite3.connect('tasks.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS tasks
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              description TEXT,
              category TEXT NOT NULL,
              project TEXT,
              area TEXT,
              resource TEXT,
              created_at TEXT,
              due_date TEXT,
              priority INTEGER DEFAULT 2,
              is_recurring INTEGER DEFAULT 0,
              recurrence_pattern TEXT,
              completed INTEGER DEFAULT 0,
              media_type TEXT,
              year TEXT,
              director TEXT,
              rating INTEGER,
              cover_url TEXT)''')

# Create subtasks table
c.execute('''CREATE TABLE IF NOT EXISTS subtasks
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              completed INTEGER DEFAULT 0,
              FOREIGN KEY(task_id) REFERENCES tasks(id))''')

# Create meetings table
c.execute('''CREATE TABLE IF NOT EXISTS meetings
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              summary TEXT,
              attendees TEXT,
              action_items TEXT,
              date TEXT,
              duration INTEGER,
              location TEXT,
              created_at TEXT)''')

# Create expenses table
c.execute('''CREATE TABLE IF NOT EXISTS expenses
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              description TEXT NOT NULL,
              amount REAL NOT NULL,
              category TEXT,
              receipt_image BLOB,
              date TEXT,
              created_at TEXT)''')

# Create voice_notes table
c.execute('''CREATE TABLE IF NOT EXISTS voice_notes
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              audio_data BLOB,
              transcript TEXT,
              created_at TEXT)''')



# Add due_date column if it doesn't exist
c.execute("PRAGMA table_info(tasks)")
columns = [column[1] for column in c.fetchall()]
if 'due_date' not in columns:
    c.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
    conn.commit()

# Add media metadata columns if they don't exist
for column in ['media_type', 'year', 'director', 'rating', 'cover_url']:
    if column not in columns:
        c.execute(f"ALTER TABLE tasks ADD COLUMN {column} TEXT")
        conn.commit()


# PARA categories with icons
CATEGORIES = {
    "Work": "💼",
    "Studies": "📚",
    "Personal": "🏠",
    "Media": "🎬",
    "Misc": "📦"
}

# Streamlit app
def delete_task(task_id):
    # Create new connection for thread safety
    local_conn = sqlite3.connect('tasks.db')
    local_c = local_conn.cursor()
    local_c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    local_c.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    local_conn.commit()
    local_conn.close()

def main():
    st.set_page_config(page_title="Tasker", page_icon="✅", layout="wide")
    
    # Modern CSS styling
    st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        color: #212529;
    }
    @media (max-width: 768px) {
        .stButton>button {
            padding: 12px 24px;
            font-size: 16px;
        }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            padding: 12px;
            font-size: 16px;
        }
        .stSelectbox>div>div>select, .stDateInput>div>div>input {
            padding: 12px;
            font-size: 16px;
        }
        .stRadio>div {
            flex-direction: column;
            gap: 10px;
        }
        .stMarkdown h1 { font-size: 24px; }
        .stMarkdown h2 { font-size: 20px; }
        .stMarkdown h3 { font-size: 18px; }
        .stContainer {
            padding: 15px;
            margin-bottom: 15px;
        }
    }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #4CAF50;
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        padding: 10px;
    }
    .stSelectbox>div>div>select {
        border-radius: 8px;
        padding: 8px;
    }
    .stDateInput>div>div>input {
        border-radius: 8px;
        padding: 8px;
    }
    .stRadio>div {
        flex-direction: row;
        gap: 20px;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #2c3e50;
    }
    .stContainer {
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Dark/light mode toggle
    if st.sidebar.checkbox('Dark Mode'):
        st.markdown("""<style>
        .main {background-color: #1e1e1e; color: white;}
        .stContainer {
            background-color: #2c3e50;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #ecf0f1;
        }
        </style>""", unsafe_allow_html=True)
    
    st.title("✅ Tasker")
    st.markdown("<h2 style='color: #4CAF50; margin-top: -20px;'>Personal Task Manager</h2>", unsafe_allow_html=True)

    # Sidebar for navigation
    menu = ["Add Task", "View Tasks", "Complete Task", "Gantt View", "Media Library", "Statistics", "Meetings", "Expenses", "Voice Notes"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    # Backup/Restore section
    st.sidebar.markdown("---")
    st.sidebar.subheader("Backup & Restore")
    
    if st.sidebar.button("Export Backup"):
        # Get all tasks and subtasks
        tasks = c.execute("SELECT * FROM tasks").fetchall()
        subtasks = c.execute("SELECT * FROM subtasks").fetchall()
        
        # Prepare data for export
        backup_data = {
            "tasks": tasks,
            "subtasks": subtasks,
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Convert to JSON
        backup_json = json.dumps(backup_data, indent=2)
        
        # Create download button
        st.sidebar.download_button(
            label="Download Backup",
            data=backup_json,
            file_name=f"tasker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    uploaded_file = st.sidebar.file_uploader("Import Backup", type=["json"])
    if uploaded_file is not None:
        if st.sidebar.button("Restore Backup"):
            try:
                # Read and parse the uploaded file
                backup_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                
                # Clear existing data
                c.execute("DELETE FROM tasks")
                c.execute("DELETE FROM subtasks")
                
                # Restore tasks
                for task in backup_data["tasks"]:
                    c.execute("""INSERT INTO tasks 
                        (id, title, description, category, project, area, resource, created_at, 
                        due_date, priority, is_recurring, recurrence_pattern, completed, 
                        media_type, year, director, rating, cover_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", task)
                
                # Restore subtasks
                for subtask in backup_data["subtasks"]:
                    c.execute("INSERT INTO subtasks (id, task_id, title, completed) VALUES (?, ?, ?, ?)", subtask)
                
                conn.commit()
                st.sidebar.success("Backup restored successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.sidebar.error(f"Failed to restore backup: {str(e)}")

    if choice == "Add Task":
        st.subheader("Add New Task")
        st.caption("Create new tasks with details like category, project, due date and priority.")
        
        with st.form(key='task_form'):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", CATEGORIES)
                project = st.text_input("Project")
                due_date = st.date_input("Due Date")
                
                # Additional fields for media items
                
            with col2:
                area = st.text_input("Area")
                resource = st.text_input("Resource")
                priority = st.selectbox("Priority", [("High", 1), ("Medium", 2), ("Low", 3)], format_func=lambda x: x[0])
                
                with st.expander("Recurring Task Settings"):
                    is_recurring = st.checkbox("This is a recurring task")
                    if is_recurring:
                        recurrence_pattern = st.selectbox("Recurrence Pattern", 
                            ["Daily", "Weekly", "Monthly", "Yearly"])
                
            submitted = st.form_submit_button("Save Task")
            
            if submitted:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Include media metadata if category is Media
                c.execute("INSERT INTO tasks (title, description, category, project, area, resource, created_at, due_date, priority, is_recurring, recurrence_pattern) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (title, description, category, project, area, resource, created_at, str(due_date), priority[1], 
                              1 if is_recurring else 0, recurrence_pattern if is_recurring else None))
                conn.commit()
                st.success(f"Task '{title}' added to {category}")
                
                # If recurring, create next instance
                if is_recurring and due_date:
                    next_date = None
                    due_date_obj = datetime.strptime(str(due_date), "%Y-%m-%d")
                    if recurrence_pattern == "Daily":
                        next_date = due_date_obj + timedelta(days=1)
                    elif recurrence_pattern == "Weekly":
                        next_date = due_date_obj + timedelta(weeks=1)
                    elif recurrence_pattern == "Monthly":
                        next_date = due_date_obj + relativedelta(months=+1)
                    elif recurrence_pattern == "Yearly":
                        next_date = due_date_obj + relativedelta(years=+1)
                        
                    if next_date:
                        c.execute("INSERT INTO tasks (title, description, category, project, area, resource, created_at, due_date, priority, is_recurring, recurrence_pattern) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                  (title, description, category, project, area, resource, created_at, str(next_date.date()), priority, 
                                  1 if is_recurring else 0, recurrence_pattern if is_recurring else None))
                        conn.commit()

    elif choice == "View Tasks":
        st.subheader("View Tasks")
        st.caption("Browse and manage your tasks. Filter by category, project, area or resource.")
        
        view_option = st.radio("View by:", ["All", "Category", "Project", "Area", "Resource", "Search"])
        show_completed = st.checkbox("Show completed tasks")
        
        if view_option == "All":
            tasks = c.execute("SELECT * FROM tasks WHERE completed = ?", (0 if not show_completed else 1,)).fetchall()
        elif view_option == "Category":
            selected_category = st.selectbox("Select Category", CATEGORIES)
            tasks = c.execute("SELECT * FROM tasks WHERE category = ? AND completed = ?", (selected_category, 0 if not show_completed else 1)).fetchall()
        elif view_option == "Project":
            projects = [item[0] for item in c.execute("SELECT DISTINCT project FROM tasks WHERE project IS NOT NULL").fetchall()]
            selected_project = st.selectbox("Select Project", projects)
            tasks = c.execute("SELECT * FROM tasks WHERE project = ? AND completed = ?", (selected_project, 0 if not show_completed else 1)).fetchall()
        elif view_option == "Area":
            areas = [item[0] for item in c.execute("SELECT DISTINCT area FROM tasks WHERE area IS NOT NULL").fetchall()]
            selected_area = st.selectbox("Select Area", areas)
            tasks = c.execute("SELECT * FROM tasks WHERE area = ? AND completed = ?", (selected_area, 0 if not show_completed else 1)).fetchall()
        elif view_option == "Resource":
            resources = [item[0] for item in c.execute("SELECT DISTINCT resource FROM tasks WHERE resource IS NOT NULL").fetchall()]
            selected_resource = st.selectbox("Select Resource", resources)
            tasks = c.execute("SELECT * FROM tasks WHERE resource = ? AND completed = ?", (selected_resource, 0 if not show_completed else 1)).fetchall()
        elif view_option == "Search":
            search_term = st.text_input("Search tasks")
            if search_term:
                tasks = c.execute("""SELECT * FROM tasks WHERE completed = ? AND 
                                    (title LIKE ? OR description LIKE ? OR category LIKE ? OR 
                                    project LIKE ? OR area LIKE ? OR resource LIKE ?)""", 
                                    (0 if not show_completed else 1, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                                    f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")).fetchall()
            else:
                tasks = []
        
        for task in tasks:
            with st.container():
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    if task[12]:  # Completed task
                        st.markdown(f"### ✅ ~~{CATEGORIES[task[3]]} {task[1]}~~")
                        st.caption(f"**Completed on:** {task[7]}")
                if not task[12]:
                    st.markdown(f"### {CATEGORIES[task[3]]} {task[1]}")
                st.caption(f"**Category:** {task[3]}")
                if task[4]: st.caption(f"**Project:** {task[4]}")
                if task[5]: st.caption(f"**Area:** {task[5]}")
                if task[6] and task[6] != 'None': st.caption(f"**Resource:** {task[6]}")
                st.caption(f"Added: {task[7]}")
                if task[8]: st.caption(f"**Due:** {task[8]}")
                priority_text = {1: "🔥 High", 2: "⚡ Medium", 3: "🐢 Low"}.get(task[9], "⚡ Medium")
                st.caption(f"**Priority:** {priority_text}")
                with col2:
                    st.button("✓", key=f"complete_{task[0]}")
                    if st.button("🗑️", key=f"delete_{task[0]}", on_click=lambda: delete_task(task[0])):
                        st.experimental_rerun()
                if st.button("➕", key=f"subtask_{task[0]}"):
                    with st.expander(f"Add subtask to: {task[1]}"):
                        with st.form(key=f'subtask_form_{task[0]}'):
                            subtask_title = st.text_input("Subtask Title")
                            submitted = st.form_submit_button("Add Subtask")
                            if submitted:
                                c.execute("INSERT INTO subtasks (task_id, title) VALUES (?, ?)",
                                          (task[0], subtask_title))
                                conn.commit()
                                st.success(f"Subtask '{subtask_title}' added")
                    
                    # Show existing subtasks
                    subtasks = c.execute("SELECT * FROM subtasks WHERE task_id = ?", (task[0],)).fetchall()
                    if subtasks:
                        st.write("Subtasks:")
                        for subtask in subtasks:
                            st.checkbox(subtask[2], value=bool(subtask[3]), 
                                       key=f"subtask_{subtask[0]}", 
                                       on_change=lambda x=subtask[0]: 
                                           c.execute("UPDATE subtasks SET completed = ? WHERE id = ?", 
                                                     (x, subtask[0])) and conn.commit())
                st.divider()

    elif choice == "Complete Task":
        st.subheader("Mark Task as Complete")
        st.caption("Mark tasks as completed to track your progress.")
        
        incomplete_tasks = c.execute("SELECT id, title FROM tasks WHERE completed = 0").fetchall()
        task_dict = {task[1]: task[0] for task in incomplete_tasks}
        
        selected_task = st.selectbox("Select Task to Complete", list(task_dict.keys()))
        
        if st.button("Complete Task"):
            task_id = task_dict[selected_task]
            c.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
            conn.commit()
            st.success(f"Task '{selected_task}' marked as complete")
    
    elif choice == "Gantt View":
        st.subheader("Task Timeline View")
        st.caption("Visualize your tasks on a timeline to understand deadlines and workload.")
        
        # Get all tasks with due dates (both completed and incomplete)
        tasks = c.execute("SELECT id, title, category, due_date, completed FROM tasks WHERE due_date IS NOT NULL").fetchall()
        
        if tasks:
            # Prepare data for Gantt chart
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    "Task": f"{CATEGORIES[task[2]]} {task[1]}",
                    "Start": datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"),
                    "End": datetime.strptime(task[3], "%Y-%m-%d"),
                    "Category": task[2],
                    "Completed": bool(task[4])
                })
            
            # Color map for completed vs incomplete tasks
            color_discrete_map = {
                "Work": "#2ecc71",
                "Studies": "#3498db",
                "Personal": "#9b59b6",
                "Media": "#e67e22",
                "Misc": "#34495e"
            }
            
            # Create Gantt chart
            fig = px.timeline(
                tasks_data,
                x_start="Start",
                x_end="End",
                y="Task",
                color="Category",
                title="Task Timeline",
                color_discrete_map=color_discrete_map,
                opacity=0.7
            )
            
            # Style completed tasks differently
            for i, task in enumerate(tasks_data):
                if task["Completed"]:
                    fig.data[0].marker.line.width[i] = 0
                    fig.data[0].marker.opacity[i] = 0.3
            
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tasks with due dates found.")

    elif choice == "Media Library":
        st.subheader("Media Library")
        st.caption("Track movies, shows, books and other media you want to consume.")
        
        # Add new media item form
        with st.expander("Add New Media Item"):
            with st.form(key='media_form'):
                title = st.text_input("Title")
                description = st.text_area("Description")
                media_type = st.selectbox("Media Type", ["Movie", "TV Show", "Book", "Music", "Other"])
                year = st.text_input("Year of Release")
                director = st.text_input("Director/Author")
                rating = st.slider("Your Rating", 1, 5, 3)
                project = st.text_input("Project")
                area = st.text_input("Area")
                resource = st.text_input("Resource")
                
                submitted = st.form_submit_button("Save Media Item")
                if submitted:

                    
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO tasks (title, description, category, project, area, resource, created_at, media_type, year, director, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (title, description, "Media", project, area, resource, created_at, media_type, year, director, rating))
                    conn.commit()
                    st.success(f"Media item '{title}' added")
        
        # Get all media tasks (both completed and incomplete)
        media_tasks = c.execute("SELECT * FROM tasks WHERE category = 'Media'").fetchall()
        
        if media_tasks:
            for task in media_tasks:
                with st.container():
                    col1, col2 = st.columns([0.9, 0.1])
                    with col1:
                        status_icon = "✅" if task[12] else "📺"
                        st.markdown(f"### {status_icon} {task[1]}")
                        
                        # Display cover image if available
                        if len(task) > 17 and task[17]:  # cover_url
                            st.image(task[17], width=150)
                        elif task[13] and task[1]:  # If no cover but has media type and title
                            with st.spinner("Fetching cover..."):
                                try:
                                    if task[13] in ["Movie", "TV Show"]:
                                        # Try OMDB API for movies/TV shows
                                        omdb_api_key = st.secrets.get("OMDB_API_KEY", "")
                                        if omdb_api_key:
                                            response = requests.get(f"http://www.omdbapi.com/?t={task[1]}&y={task[14] or ''}&apikey={omdb_api_key}")
                                            if response.status_code == 200 and response.json().get("Poster"):
                                                cover_url = response.json()["Poster"]
                                                c.execute("UPDATE tasks SET cover_url = ? WHERE id = ?", (cover_url, task[0]))
                                                conn.commit()
                                                st.image(cover_url, width=150)
                                    elif task[13] == "Book":
                                        # Try OpenLibrary API for books
                                        response = requests.get(f"https://openlibrary.org/search.json?title={task[1]}&author={task[15] or ''}")
                                        if response.status_code == 200 and response.json().get("docs"):
                                            book = response.json()["docs"][0]
                                            if book.get("cover_i"):
                                                cover_url = f"https://covers.openlibrary.org/b/id/{book['cover_i']}-M.jpg"
                                                c.execute("UPDATE tasks SET cover_url = ? WHERE id = ?", (cover_url, task[0]))
                                                conn.commit()
                                                st.image(cover_url, width=150)
                                except Exception as e:
                                    st.error(f"Failed to fetch cover: {str(e)}")
                        
                        st.caption(f"**Type:** {task[4] if len(task) > 4 and task[4] else 'N/A'}")
                        if len(task) > 13 and task[13]: st.caption(f"**Media Type:** {task[13]}")
                        if len(task) > 14 and task[14]: st.caption(f"**Year:** {task[14]}")
                        if len(task) > 15 and task[15]: st.caption(f"**Director:** {task[15]}")
                        if len(task) > 16 and task[16]: st.caption(f"**Rating:** {'⭐' * int(task[16])}")
                        if len(task) > 5 and task[5]: st.caption(f"**Area:** {task[5]}")
                        if task[6] and task[6] != 'None': st.caption(f"**Resource:** {task[6]}")
                        st.caption(f"Added: {task[7]}")
                        if task[8]: st.caption(f"**Completed:** {task[12]}")
                    with col2:
                        if not task[12]:
                            st.button("✓", key=f"complete_media_{task[0]}")
                        if st.button("🗑️", key=f"delete_media_{task[0]}", on_click=lambda: delete_task(task[0])):
                            st.experimental_rerun()
                    st.divider()
        else:
            st.info("No media tasks found.")
            
    elif choice == "Statistics":
        st.subheader("Task Statistics")
        st.caption("Visual analytics of your task management patterns.")
        
        # Get all tasks
        tasks = c.execute("SELECT * FROM tasks").fetchall()
        
        if tasks:
            # Prepare data for charts
            df = pd.DataFrame(tasks, columns=["id", "title", "description", "category", "project", "area", "resource", 
                                            "created_at", "due_date", "priority", "is_recurring", "recurrence_pattern", 
                                            "completed", "media_type", "year", "director", "rating", "cover_url"])
            
            # Completion rate chart
            completed_count = df["completed"].sum()
            total_count = len(df)
            completion_rate = (completed_count / total_count) * 100 if total_count > 0 else 0
            
            fig1 = px.pie(names=["Completed", "Pending"], 
                         values=[completed_count, total_count - completed_count],
                         title=f"Completion Rate: {completion_rate:.1f}%",
                         color_discrete_sequence=["#4CAF50", "#F44336"])
            st.plotly_chart(fig1, use_container_width=True)
            
            # Category distribution chart
            category_counts = df["category"].value_counts()
            fig2 = px.bar(category_counts, 
                         x=category_counts.index, 
                         y=category_counts.values,
                         title="Tasks by Category",
                         color=category_counts.index,
                         labels={"x":"Category", "y":"Count"})
            st.plotly_chart(fig2, use_container_width=True)
            
            # Priority breakdown chart
            priority_counts = df["priority"].value_counts().sort_index()
            priority_labels = {1:"High", 2:"Medium", 3:"Low"}
            fig3 = px.pie(priority_counts, 
                         names=priority_counts.index.map(priority_labels), 
                         values=priority_counts.values,
                         title="Tasks by Priority",
                         color_discrete_sequence=["#F44336", "#FFC107", "#4CAF50"])
            st.plotly_chart(fig3, use_container_width=True)
            
            # Overdue tasks
            if 'due_date' in df.columns:
                today = datetime.now().date()
                df['due_date'] = pd.to_datetime(df['due_date']).dt.date
                overdue_tasks = df[(df['completed'] == 0) & (df['due_date'] < today)]
                
                if not overdue_tasks.empty:
                    st.warning(f"You have {len(overdue_tasks)} overdue tasks!")
                    st.dataframe(overdue_tasks[["title", "category", "due_date", "priority"]].sort_values("due_date"))
        else:
            st.info("No tasks found to display statistics.")
        st.caption("View completion rates and task distribution by category.")
        
    elif choice == "Meetings":
        st.subheader("Meeting Records")
        st.caption("Record and review your meeting summaries.")
        
        with st.form(key='meeting_form'):
            title = st.text_input("Meeting Title")
            summary = st.text_area("Summary")
            attendees = st.text_input("Attendees (comma separated)")
            action_items = st.text_area("Action Items")
            
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date")
                duration = st.number_input("Duration (minutes)", min_value=1)
            with col2:
                location = st.text_input("Location")
                
            submitted = st.form_submit_button("Save Meeting")
            if submitted:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO meetings (title, summary, attendees, action_items, date, duration, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (title, summary, attendees, action_items, str(date), duration, location, created_at))
                conn.commit()
                st.success(f"Meeting '{title}' recorded")
        
        # Display existing meetings
        meetings = c.execute("SELECT * FROM meetings ORDER BY date DESC").fetchall()
        for meeting in meetings:
            with st.expander(f"{meeting[1]} - {meeting[5]}"):
                st.write(f"**Attendees:** {meeting[3]}")
                st.write(f"**Duration:** {meeting[6]} minutes")
                st.write(f"**Location:** {meeting[7]}")
                st.write(f"**Summary:** {meeting[2]}")
                st.write(f"**Action Items:** {meeting[4]}")
                
    elif choice == "Expenses":
        st.subheader("Expense Tracking")
        st.caption("Track expenses for reimbursement.")
        
        with st.form(key='expense_form'):
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
            category = st.text_input("Category")
            receipt = st.file_uploader("Upload Receipt", type=["png", "jpg", "jpeg"])
            date = st.date_input("Date")
            
            submitted = st.form_submit_button("Save Expense")
            if submitted:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                receipt_data = receipt.read() if receipt else None
                c.execute("INSERT INTO expenses (description, amount, category, receipt_image, date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                          (description, amount, category, receipt_data, str(date), created_at))
                conn.commit()
                st.success(f"Expense '{description}' recorded")
        
        # Display existing expenses
        expenses = c.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
        for expense in expenses:
            with st.expander(f"{expense[1]} - ${expense[2]:.2f}"):
                st.write(f"**Category:** {expense[3]}")
                st.write(f"**Date:** {expense[5]}")
                if expense[4]:
                    st.image(expense[4], width=200)
                
    elif choice == "Voice Notes":
        st.subheader("Voice Notes")
        st.caption("Record and review quick voice memos.")
        
        audio_bytes = None
        title = st.text_input("Note Title")
        
        if st.button("Start Recording"):
            try:
                st.warning("Recording... Click Stop when done")
                # Create a unique filename for each recording
                recording_file = f"voice_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                # Use Streamlit's audio recorder component with proper file handling
                audio_bytes = st.audio(recording_file, format="audio/wav")
                if audio_bytes:
                    # Read the audio file data
                    with open(recording_file, "rb") as f:
                        audio_data = f.read()
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO voice_notes (title, audio_data, created_at) VALUES (?, ?, ?)",
                              (title, audio_data, created_at))
                    conn.commit()
                    # Clean up the temporary file
                    os.remove(recording_file)
                    st.success(f"Voice note '{title}' saved")
                else:
                    st.error("No audio data recorded. Please try again.")
            except Exception as e:
                st.error(f"Failed to record audio: {str(e)}")
                # Clean up if file was created but operation failed
                if 'recording_file' in locals() and os.path.exists(recording_file):
                    os.remove(recording_file)
        
        # Display existing voice notes
        notes = c.execute("SELECT * FROM voice_notes ORDER BY created_at DESC").fetchall()
        for note in notes:
            with st.expander(note[1]):
                st.write(f"**Created:** {note[4]}")
                if note[2]:
                    st.audio(note[2], format='audio/wav')
        
        # Completion rate
        total_tasks = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed_tasks = c.execute("SELECT COUNT(*) FROM tasks WHERE completed = 1").fetchone()[0]
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Tasks by category
        category_stats = c.execute("""
            SELECT category, 
                   COUNT(*) as total, 
                   SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM tasks
            GROUP BY category
        """).fetchall()
        
        if category_stats:
            categories = [stat[0] for stat in category_stats]
            totals = [stat[1] for stat in category_stats]
            completed = [stat[2] for stat in category_stats]
            
            fig = px.bar(
                x=categories,
                y=totals,
                title="Tasks by Category",
                labels={'x':'Category', 'y':'Count'},
                color=categories
            )
            fig.add_bar(x=categories, y=completed, name="Completed")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()