import sys
from db_manager import create_project

def main():
    if len(sys.argv) < 2:
        print("Usage: python add_project.py <path_to_video>")
        sys.exit(1)
        
    video_path = sys.argv[1]
    project_id = create_project(video_path)
    
    print(f"Project created successfully!")
    print(f"Project ID: {project_id}")
    print(f"Source Video: {video_path}")
    print("The queue_worker.py will pick this up automatically.")

if __name__ == "__main__":
    main()
