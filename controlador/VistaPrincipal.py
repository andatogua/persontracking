#libreiras principales
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

import os
import numpy

from configuracion.conf import BASE_DIR
from controlador.Detector import Detector

#clase principal que vincula la interfaz realizada en designer con el controlador python
#en esta clase se integran todas las funcionalidades de la aplicación


class VentanaPrincipal(QMainWindow):
    #constructor
    def __init__(self):
        QMainWindow.__init__(self)                                                      #se inicializa el constructor
        path_ui = os.path.join(BASE_DIR,r"vista\main.ui")                               #se obtiene el directorio de la vista
        uic.loadUi(path_ui,self)                                                        #se carga la vista

        self.showMaximized()                                                            #siempre se muestra maximizado
        #self.setWindowFlag(Qt.WindowMaximizeButtonHint,False)        

        self.camaras_disponibles = QCameraInfo.availableCameras()                       #se detectan las cámaras conectadas
        if not self.camaras_disponibles:
            sys.exit()                                                                  #si no hay cámaras conectadas se cierra el sistema

        self.combo_cam.setToolTip("Seleccione una cámara para iniciar")
        self.combo_cam.addItems(["{}: {}".format(index,cam.description()) 
                                for index,cam in enumerate(self.camaras_disponibles)])             #se llena la lista de cámaras conectadas
        self.combo_cam.currentIndexChanged.connect(self.conectar_cam)


        self.videos = [None for i in range(len(self.camaras_disponibles))]
        self.indice_cam = None
        self.imagen_label.setText("Cargando..!!")

    def conectar_cam(self, index):
        if index == self.indice_cam: return
        
        self.videos[index] = Detector(index)
        self.videos[index].imagen_emit.connect(self.cargar_video)

        if self.indice_cam == None:
            self.videos[index].start()
        elif self.indice_cam != index and self.indice_cam != None: 
            self.videos[self.indice_cam].terminate()
            print(f'cambiando a {index}')
            if self.videos[self.indice_cam].wait():
                self.videos[index].start()
        self.indice_cam = index

    def cargar_video(self,imagen):
        if imagen: 
            self.imagen_label.setPixmap(QPixmap.fromImage(imagen))
        else:
            print('fin')
            sys.exit()
