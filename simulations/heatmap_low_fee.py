import sys
import os

# S'assure que le répertoire racine est dans le PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from simulations.generate_profile_heatmaps import generate_profile_heatmap

if __name__ == "__main__":
    profiles = [
        (0.03, "heatmap_low_fee_3pct.png", "Profil Prudent (3%) : AV 0.39% frais", 0.0039),
        (0.05, "heatmap_low_fee_5pct.png", "Profil Équilibré (5%) : AV 0.39% frais", 0.0039),
        (0.08, "heatmap_low_fee_8pct.png", "Profil Dynamique (8%) : AV 0.39% frais", 0.0039),
    ]
    
    print("Generating heatmaps for 0.39% AV fees...")
    for yld, fname, title, fees in profiles:
        generate_profile_heatmap(yld, fname, title, frais_av=fees)
    print("Done. Images saved in 'images/'.")
