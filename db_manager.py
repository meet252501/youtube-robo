import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "openshorts.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table: Tracks the overall processing of a source video
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        source_video_path TEXT,
        status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Clips table: Tracks individual splice segments (candidates generated from a project)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clips (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        start_time REAL,
        end_time REAL,
        score REAL,
        status TEXT DEFAULT 'pending', -- pending, accepted, rejected, rendering, qa_passed, qa_failed, completed
        metadata TEXT, -- JSON containing topics, transcript slice, etc.
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    # Render Tasks table: Tracks rendering of a specific clip
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS render_tasks (
        id TEXT PRIMARY KEY,
        clip_id TEXT,
        status TEXT DEFAULT 'pending', -- pending, rendering, completed, failed
        render_props TEXT, -- JSON containing ai_director output config
        output_path TEXT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (clip_id) REFERENCES clips (id)
    )
    ''')
    
    # QA Results table: Tracks visual QA results for a render task
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS qa_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        render_task_id TEXT,
        status TEXT, -- passed, failed
        details TEXT, -- JSON containing frame inspection results, overlap details
        inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (render_task_id) REFERENCES render_tasks (id)
    )
    ''')

    conn.commit()
    conn.close()

def execute_write(query: str, params: tuple = ()) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    last_row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_row_id

def execute_read(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def execute_read_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    rows = execute_read(query, params)
    return rows[0] if rows else None

# --- Project Operations ---

def create_project(source_video_path: str, project_id: str = None) -> str:
    if project_id is None:
        project_id = str(uuid.uuid4())
    query = "INSERT INTO projects (id, source_video_path) VALUES (?, ?)"
    execute_write(query, (project_id, source_video_path))
    return project_id

def update_project_status(project_id: str, status: str):
    query = "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    execute_write(query, (status, project_id))

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    row = execute_read_one("SELECT * FROM projects WHERE id = ?", (project_id,))
    return dict(row) if row else None

# --- Clip Operations ---

def add_clip(project_id: str, start_time: float, end_time: float, score: float = 0.0, metadata: Dict[str, Any] = None, clip_id: str = None) -> str:
    if clip_id is None:
        clip_id = str(uuid.uuid4())
    metadata_json = json.dumps(metadata) if metadata else "{}"
    query = "INSERT INTO clips (id, project_id, start_time, end_time, score, metadata) VALUES (?, ?, ?, ?, ?, ?)"
    execute_write(query, (clip_id, project_id, start_time, end_time, score, metadata_json))
    return clip_id

def update_clip_status(clip_id: str, status: str):
    query = "UPDATE clips SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
    execute_write(query, (status, clip_id))

def get_clips_for_project(project_id: str) -> List[Dict[str, Any]]:
    rows = execute_read("SELECT * FROM clips WHERE project_id = ? ORDER BY start_time ASC", (project_id,))
    return [dict(r) for r in rows]

def get_clip(clip_id: str) -> Optional[Dict[str, Any]]:
    row = execute_read_one("SELECT * FROM clips WHERE id = ?", (clip_id,))
    return dict(row) if row else None

# --- Render Task Operations ---

def create_render_task(clip_id: str, render_props: Dict[str, Any], task_id: str = None) -> str:
    if task_id is None:
        task_id = str(uuid.uuid4())
    render_props_json = json.dumps(render_props) if render_props else "{}"
    query = "INSERT INTO render_tasks (id, clip_id, render_props) VALUES (?, ?, ?)"
    execute_write(query, (task_id, clip_id, render_props_json))
    update_clip_status(clip_id, "rendering")
    return task_id

def update_render_task_status(task_id: str, status: str, output_path: str = None, error_message: str = None):
    query = "UPDATE render_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
    params = [status]
    if output_path is not None:
        query += ", output_path = ?"
        params.append(output_path)
    if error_message is not None:
        query += ", error_message = ?"
        params.append(error_message)
    query += " WHERE id = ?"
    params.append(task_id)
    execute_write(query, tuple(params))
    
    # Auto-update clip status based on render task completion
    task = get_render_task(task_id)
    if task:
        if status == 'completed':
            update_clip_status(task['clip_id'], "rendered")
        elif status == 'failed':
            update_clip_status(task['clip_id'], "failed")

def get_render_task(task_id: str) -> Optional[Dict[str, Any]]:
    row = execute_read_one("SELECT * FROM render_tasks WHERE id = ?", (task_id,))
    return dict(row) if row else None

def get_pending_render_tasks() -> List[Dict[str, Any]]:
    rows = execute_read("SELECT * FROM render_tasks WHERE status = 'pending' ORDER BY created_at ASC")
    return [dict(r) for r in rows]

# --- QA Operations ---

def add_qa_result(render_task_id: str, status: str, details: Dict[str, Any] = None) -> int:
    details_json = json.dumps(details) if details else "{}"
    query = "INSERT INTO qa_results (render_task_id, status, details) VALUES (?, ?, ?)"
    qa_id = execute_write(query, (render_task_id, status, details_json))
    
    task = get_render_task(render_task_id)
    if task:
        update_clip_status(task['clip_id'], f"qa_{status}")
        
    return qa_id

def get_qa_results_for_task(render_task_id: str) -> List[Dict[str, Any]]:
    rows = execute_read("SELECT * FROM qa_results WHERE render_task_id = ? ORDER BY inspected_at DESC", (render_task_id,))
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
