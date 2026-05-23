# Player Images

This folder does not contain copyrighted player photos.

Run:

```bash
python scripts/fetch_player_images.py
```

The script searches Wikidata for cricketer entities, reads the Wikimedia Commons P18 image property, and stores open-source image URLs plus attribution metadata in:

```text
data/processed/player_image_map.csv
```

If no image is found for a player, the Streamlit app shows a professional initials/silhouette fallback and marks the image as unavailable.
