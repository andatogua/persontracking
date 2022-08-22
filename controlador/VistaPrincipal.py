#libreiras principales
from datetime import datetime
import sys
from unittest.mock import patch
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *

import os
import numpy
import cv2

from configuracion.conf import BASE_DIR, DB_NAME, MARGIN, SERVER
from controlador.Detector import Detector
from modelo.db import BaseDatos
from .tracker import CentroidTracker

#clase principal que vincula la interfaz realizada en designer con el controlador python
#en esta clase se integran todas las funcionalidades de la aplicación


class VentanaPrincipal(QMainWindow):
    #constructor
    def __init__(self):
        QMainWindow.__init__(self)                                                      #se inicializa el constructor
        path_ui = os.path.join(BASE_DIR,r"vista\\main.ui")                               #se obtiene el directorio de la vista
        uic.loadUi(path_ui,self)                                                        #se carga la vista
        self.showMaximized()                                                            #siempre se muestra maximizado
        self.capturar.clicked.connect(self.capturarevidencia)
        self.abrirdirectorio.mousePressEvent = self.abrirevidencias

        self.statusBar().setStyleSheet("color:gray")
        self.statusBar().showMessage("Seleccione una cámara para comenzar")

        #self.mutex = QMutex()
        #self.mutex.lock()
        #self.condition = QWaitCondition()

        self.camaras_disponibles = QCameraInfo.availableCameras()                       #se detectan las cámaras conectadas
        if not self.camaras_disponibles:
            sys.exit()                                                                  #si no hay cámaras conectadas se cierra el sistema

        self.combo_cam.setToolTip("Seleccione una cámara para iniciar")
        self.combo_cam.addItems(["{}: {}".format(index,cam.description()) 
                                for index,cam in enumerate(self.camaras_disponibles)])             #se llena la lista de cámaras conectadas
        self.combo_cam.currentIndexChanged.connect(self.conectar_cam)


        self.videos = [None for i in range(len(self.camaras_disponibles))]
        self.indice_cam = None
        self.imagen_label.mousePressEvent = self.getPos


        #tracker
        self.ct = CentroidTracker()
        self.objetos = None
        self.trayectoria = []
        
        #coordenadas tracking
        self.xt, self.yt = 0,0
        self.track = False
        self.margen_x = self.margen_y = False

        #evidencia
        self.captura = None
        self.rostro = None
        self.inicio = None
        self.final = None
        self.numpersonas = 0
        self.numcamaras = len(self.camaras_disponibles)
        self.detallecam = None


        try:
            self.db = BaseDatos(DB_NAME,SERVER)
            self.db.init()
            self.num_detecciones_hoy.setText(str(self.db.getregistrodiario()))
        except:
            print("error")

    def conectar_cam(self, index):
        self.statusBar().showMessage("Video iniciado")
        self.detallecam = self.camaras_disponibles[index].description()
        self.track = False
        self.trayectoria = []
        self.margen_x = self.margen_y = False
        if index == self.indice_cam: return
        
        self.videos[index] = Detector(index)
        self.videos[index].imagen_emit.connect(self.cargar_video)

        if self.indice_cam == None:
            self.videos[index].start()
        elif self.indice_cam != index and self.indice_cam != None: 
            self.videos[self.indice_cam].terminate()
            if self.videos[self.indice_cam].wait():
                self.videos[index].start()
        self.indice_cam = index

    def cargar_video(self,imagen,cajas,numper):
        #self.mutex.lock()
        c0 = c1 = c2 = c3 = 0
        self.numpersonas = numper
        self.numper_label.setText(str(self.numpersonas))
        try:
            if len(cajas)>0 and self.track:
                for index,caja in enumerate(cajas):
                    cx,cy = int(caja[0]+(caja[2]/2)),int(caja[1]+(caja[3]/2))
                    self.margen_x = cx-MARGIN < self.xt < cx+MARGIN
                    self.margen_y = cy-MARGIN < self.yt < cy+MARGIN
                    if self.margen_x and self.margen_y:
                        self.objetos = self.ct.update([cajas[index]])
                        self.xt, self.yt = cx, cy
                        self.trayectoria.append((caja[0]+caja[2],caja[1]+caja[3]))
                        c0,c1,c2,c3 = caja[0],caja[1],caja[2],caja[3]
                        break

                if self.objetos:
                    for (id_objeto, centroide) in self.objetos.items():

                        cv2.rectangle(imagen,(centroide[0],centroide[1]),(centroide[0]+centroide[2],centroide[1]+centroide[3]),(0,0,255),2)
                    if len(self.trayectoria)>3:
                        for i in range(0, len(self.trayectoria)-1):
                            cv2.line(imagen,(self.trayectoria[i][0],self.trayectoria[i][1]),(self.trayectoria[i+1][0],self.trayectoria[i+1][1]),(0,0,255),2)
            qtImagen= QImage(imagen.data, imagen.shape[1], imagen.shape[0], QImage.Format_RGB888)
            self.img= qtImagen.scaled(self.imagen_label.width(),self.imagen_label.height(),Qt.KeepAspectRatio)
            self.imagen_label.setPixmap(QPixmap.fromImage(self.img))

            self.captura = QPixmap.fromImage(self.img)

            if self.track:
                self.imagenR = qtImagen.copy(QRect(c0,c1,c2,c2))
                self.rostro = QPixmap.fromImage(self.imagenR)
                self.imgR= self.imagenR.scaled(self.face.width(),self.face.width(),Qt.KeepAspectRatio)
                self.face.setPixmap(QPixmap.fromImage(self.imgR))


        except:
            print("error")
        #self.mutex.unlock()
        #self.condition.wakeAll()


    def getPos(self , event):
        """
        obtener la posición dentro de la imagen restando coordenadas dentro 
        de la aplicación
        """
        self.objetos = None

        x = event.pos().x()
        y = event.pos().y() 
        cx = x - self.imagen_label.x()
        cy = y - self.imagen_label.y()

        #cx = (cx*self.imagen_label.width())/1280
        #cy = (cy*self.imagen_label.height())/720

        self.trayectoria = []
        self.xt, self.yt = 0,0
        self.track = True
        self.xt, self.yt = int(cx), int(cy)

        #fecha inicio tracking
        self.inicio = str(datetime.now())

        """
        esta función es asincrona y permite obtener la posición de la persona
        dentro del video y tener la referencia a seguir
        """


    def capturarevidencia(self):
        if not self.rostro: return
        fecha = str(datetime.now())
        self.final = fecha
        nombre1 = "evidencia-" + fecha.replace(":","-")
        nombre2 = "evidenciarostro-" + fecha.replace(":","-")
        carpeta = "evidencias"
        dir = os.path.join(BASE_DIR,carpeta)
        if not os.path.exists(dir):
            os.mkdir(dir)
        self.captura.save(dir+"/"+nombre1+".png")
        self.rostro.save(dir+"/"+nombre2+".png")
        

        try:
            self.db.guardarregistro(
                self.inicio,
                self.final,
                self.numpersonas,
                self.numcamaras,
                self.detallecam
            )
        except:
            print("error")

    def abrirevidencias(self,event):
        carpeta = "evidencias"
        dir = os.path.join(BASE_DIR,carpeta)
        if not os.path.exists(dir):
            return
        os.system(f'start {os.path.realpath(dir)}')
