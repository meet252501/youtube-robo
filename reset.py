import sqlite3
db = sqlite3.connect('openshorts.db')
db.execute("UPDATE render_tasks SET status='pending'")
db.commit()
