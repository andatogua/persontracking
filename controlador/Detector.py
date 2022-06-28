import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2

class Detector(QThread):
    imagen_emit = pyqtSignal(QImage)
    def __init__(self,indice):
        QThread.__init__(self)
        self.inidce_cam = indice

    def inicio(self):
        video = cv2.VideoCapture(self.inidce_cam)                                     #iniciar captura de video
        video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return video

    def run(self):
        self.TheadActive = True
        video = self.inicio()
        while self.TheadActive:
            disponible, fotograma = video.read()
            if not disponible: sys.exit()
            #enviar la señal a la aplicación con la imagen como argumento
            imagen = cv2.cvtColor(fotograma, cv2.COLOR_BGR2RGB)
            imagen = cv2.flip(imagen,1)
            imagenaplanada= cv2.flip(imagen,1)
            qtImagen= QImage(imagenaplanada.data, imagenaplanada.shape[1], imagenaplanada.shape[0], QImage.Format_RGB888)
            img= qtImagen.scaled(1280,720,Qt.KeepAspectRatio)
            self.imagen_emit.emit(img)
        

    def stop(self):
        self.TheadActive = False
        cv2.destroyAllWindows()
        self.quit()
