import os
#directorio raiz
BASE_DIR = os.getcwd()

#proporción del video
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

#margen de error en pixeles para tracking
MARGIN = 100

#tipo de BD
SERVER = "QSQLITE"
DB_NAME = "tracking.sqlite"