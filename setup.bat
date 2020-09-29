REM call conda env create -f environment.yml
call conda activate NAM-Dash
call ipython kernel install --user --name=NAM-Dash
call jupyter labextension install @jupyter-widgets/jupyterlab-manager bqplot jupyter-vue jupyter-vuetify jupyter-leaflet
call jupyter labextension install jupyter-leaflet
call jupyter trust "GUI/New AutoMotive.ipynb"
pause