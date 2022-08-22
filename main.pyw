from unicodedata import name
from PyQt5.QtWidgets import QApplication

import sys
from configuracion.conf import DB_NAME, SERVER

from controlador.VistaPrincipal import VentanaPrincipal

def main():
    aplicacion = QApplication(sys.argv)
    aplicacion.setStyle('fusion')
    
    principal = VentanaPrincipal()
    principal.show()

    sys.exit(aplicacion.exec_())


if __name__ == "__main__":
    main()