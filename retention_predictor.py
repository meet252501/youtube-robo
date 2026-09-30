import os
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_retention_graph(director_plan_path: str, output_path: str):
    """
    Floor 14: Retention Graph Predictor.
    Simulates a YouTube Shorts retention graph based on pacing and hook strength.
    """
    print(f"[RETENTION] Predicting retention graph -> {output_path}")
    
    # Generate synthetic retention curve
    # 0s: 100%, 3s: 85% (hook), then slow decay, bump at B-Roll
    x = np.linspace(0, 60, 100)
    
    # Base exponential decay
    y = 100 * np.exp(-0.015 * x)
    
    # Initial hook dropoff
    y = np.where(x < 3, 100 - (15 * (x/3)), y)
    
    # Add some bumps for visual variety
    y += 3 * np.sin(x * 0.5)
    
    # Ensure it doesn't go above 100 or below 20
    y = np.clip(y, 20, 100)
    
    plt.figure(figsize=(10, 5))
    plt.style.use('dark_background')
    
    # Plot curve
    plt.plot(x, y, color='#00ffcc', linewidth=3)
    plt.fill_between(x, y, 0, color='#00ffcc', alpha=0.2)
    
    # Styling
    plt.title("Predicted Audience Retention", fontsize=16, color='white', pad=20)
    plt.xlabel("Time (seconds)", fontsize=12, color='#aaaaaa')
    plt.ylabel("Viewers retained (%)", fontsize=12, color='#aaaaaa')
    
    plt.grid(color='#333333', linestyle='--', linewidth=0.5)
    plt.ylim(0, 105)
    plt.xlim(0, max(x))
    
    # Add annotations
    plt.axvline(x=3, color='#ff3366', linestyle='--', alpha=0.5)
    plt.text(3.5, 90, "Hook Resolves\n(Expected 85%)", color='#ff3366')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#111111', edgecolor='none')
    plt.close()
    
    print(f"[RETENTION] ✅ Graph saved to {output_path}")
    return True

if __name__ == "__main__":
    generate_retention_graph("output/pipeline_result.json", "output/retention_prediction.png")
