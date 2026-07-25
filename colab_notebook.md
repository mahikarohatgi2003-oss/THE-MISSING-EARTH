# Running the pipeline in Google Colab (free, no local install)

If you don't want to install `geopandas`/`osmnx` locally, paste this into a
fresh Colab notebook:

```python
!pip -q install osmnx geopandas shapely mercantile requests

!git clone https://github.com/<you>/missing-earth.git
%cd missing-earth/pipeline

# Edit config.py's PLACE_NAME here if needed:
# !sed -i 's/PLACE_NAME = .*/PLACE_NAME = "Your District, State, Country"/' config.py

!python run_all.py
```

Then, in a second cell, download the results to commit back to GitHub:

```python
from google.colab import files
import shutil
shutil.make_archive('/content/site-data', 'zip', '../docs/data')
files.download('/content/site-data.zip')
```

Unzip that into your local repo's `docs/data/`, commit, and push — GitHub
Pages will pick it up automatically.
