import simulations.apply_watermarks as aw

# Remplace les images cibles par les nouvelles générations
# Le script apply_watermarks attend des chemins relatifs à PROJECT_ROOT
aw.TARGET_IMAGES = [
    "images/heatmap_low_fee_3pct.png",
    "images/heatmap_low_fee_5pct.png",
    "images/heatmap_low_fee_8pct.png"
]

print("Applying watermarks to low fee heatmaps...")
aw.apply_watermark()
print("Done.")
