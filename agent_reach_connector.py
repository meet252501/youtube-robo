import os
import subprocess
import json
from typing import Optional, Dict, Any, List

class AgentReachConnector:
    """
    A utility class to connect OpenShorts (our bot) to Agent-Reach tools.
    This enables the Multimodal AI Director and B-Roll engine to pull live data
    from the internet, Reddit, Twitter, and YouTube seamlessly.
    """
    
    @staticmethod
    def read_webpage(url: str) -> str:
        """
        Uses jina.ai reader to extract readable markdown from any URL.
        """
        try:
            cmd = ["curl", "-s", f"https://r.jina.ai/{url}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error reading webpage: {e}"

    @staticmethod
    def fetch_youtube_captions(youtube_url: str) -> str:
        """
        Extracts subtitles from a YouTube video using yt-dlp.
        """
        try:
            cmd = [
                "yt-dlp",
                "--write-auto-sub",
                "--sub-lang", "en",
                "--skip-download",
                "--print", "after_move:filepath",
                youtube_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error fetching YouTube captions: {e}"

    @staticmethod
    def get_trending_topics_context(topic: str) -> str:
        """
        A combined internet sweep for a specific topic to inject context into the Multimodal Director.
        Could be hooked up to Exa search or RSS feeds via Agent-Reach.
        """
        # Placeholder for deeper Agent-Reach integration via exa/opencli
        # We can implement specific CLI calls here (e.g. `twitter search`, `rdt search`)
        return f"[Agent-Reach Context for {topic}]: No active cookies provided yet, using simulated fallback."

# Example usage within OpenShorts:
# from agent_reach_connector import AgentReachConnector
# transcript = AgentReachConnector.fetch_youtube_captions("https://youtube.com/watch?v=...")
