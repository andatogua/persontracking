import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2
import numpy as np
from configuracion.conf import BASE_DIR, FRAME_HEIGHT, FRAME_WIDTH

class Detector(QThread):
    imagen_emit = pyqtSignal(np.ndarray,list,int)
    def __init__(self,indice):
        QThread.__init__(self)
        self.inidce_cam = indice
        #self.mutex = mutex
        #self.condition = condition

        #cargar etiquetas
        self.etiquetas = open(os.path.join(BASE_DIR,r"configuracion/coco.names")).read().strip().split('\n')

        #color verde por defecto para las personas
        self.color = (0,255,0)

        #cargar pesos y configuración de YOLOv3
        self.red = cv2.dnn.readNetFromDarknet(os.path.join(BASE_DIR,r'configuracion/yolov3.cfg'),os.path.join(BASE_DIR,r'configuracion/yolov3.weights'))

        #comprobar GPU
        self.indice_gpu = cv2.cuda.getDevice()
        if self.indice_gpu >= 0:
            self.red.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            self.red.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
            #imprimir información de GPU
            cv2.cuda.printCudaDeviceInfo(self.indice_gpu)
            
        # Obtener etiquetas de la red
        self.nombres_etiquetas = self.red.getLayerNames()
        self.nombres_etiquetas = [self.nombres_etiquetas[i[0] - 1] for i in self.red.getUnconnectedOutLayers()]

        #indicamos nivel de confianza
        self.confianza = 0.8

        #indicamos el nivel de umbral
        self.umbral = 0.35

    def extraer_cajas_confianzas_idsclases(self,salidas, confianza, ancho, alto):
        cajas = []
        lista_confianza = []
        ids_clases = []

        for salida in salidas:
            for deteccion in salida:            
                # Extraer los puntajes, los id de las clases, y la confianza de la predicción
                puntajes = deteccion[5:]
                id_clase = np.argmax(puntajes)
                conf = puntajes[id_clase]
                
                # se muestra sólo si supera el nivel de confianza establecido
                if conf > confianza and id_clase == 0:
                    # redimensionar la caja que enmarcará a la persona
                    caja = deteccion[0:4] * np.array([ancho, alto, ancho, alto])
                    centroX, centroY, _ancho, _alto = caja.astype('int')

                    # obtener las coordenadas superior izquierda para dibujar el rectángulo
                    x = int(centroX - (_ancho / 2))
                    y = int(centroY - (_alto / 2))

                    #las coordenadas se añaden a la lista de cajas
                    cajas.append([x, y, int(_ancho), int(_alto)])
                    
                    #se añaden los niveles de confianza obtenidos
                    lista_confianza.append(float(conf))
                    
                    #se añaden las identificaciones de las clases obtenidas
                    ids_clases.append(id_clase)

        return cajas, lista_confianza, ids_clases

    def dibujar_cajas(self,imagen, cajas, lista_confianza, ids_clases, idxs, color):
        if len(idxs) > 0:
            for i in idxs.flatten():
                # extraer las coordenadas de las cajas
                x, y = cajas[i][0], cajas[i][1]
                ancho, alto = cajas[i][2], cajas[i][3]
                cv2.circle(imagen,(int(x+(ancho/2)),int(y+(alto/2)-20)),10,(0,255,0),2)
            
        return imagen,len(idxs)

    def prediccion(self,red, nombres_etiquetas, imagen, confianza, umbral):
        alto, ancho = imagen.shape[:2]
        
        # crear blob desde la imagen
        blob = cv2.dnn.blobFromImage(imagen, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        
        red.setInput(blob)
        salidas = red.forward(nombres_etiquetas)

        # extraer elementos
        cajas, confianzas, idsclases = self.extraer_cajas_confianzas_idsclases(salidas, confianza, ancho, alto)

        # aplicar umbral
        idxs = cv2.dnn.NMSBoxes(cajas, confianzas, confianza, umbral)

        return cajas, confianzas, idsclases, idxs

    def inicio(self):
        video = cv2.VideoCapture(self.inidce_cam)                                     #iniciar captura de video
        video.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        video.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        return video

    def run(self):
        self.TheadActive = True
        video = self.inicio()
        while self.TheadActive:
            disponible, fotograma = video.read()
            if not disponible: sys.exit()

            self.cajas, self.confianzas, self.idclases, self.idxs = self.prediccion(self.red, self.nombres_etiquetas, fotograma, self.confianza, self.umbral)

            self.imagen, self.numper = self.dibujar_cajas(fotograma,self.cajas, self.confianzas, self.idclases, self.idxs, self.color )

            #enviar la señal a la aplicación con la imagen como argumento
            self.imagen = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2RGB)
            self.imagen = cv2.flip(self.imagen,1)
            self.imagenaplanada= cv2.flip(self.imagen,1)
            #qtImagen= QImage(self.imagenaplanada.data, self.imagenaplanada.shape[1], self.imagenaplanada.shape[0], QImage.Format_RGB888)
            #self.img= qtImagen.scaled(1077,746,Qt.KeepAspectRatio)
            self.imagen_emit.emit(self.imagenaplanada,self.cajas,self.numper)
            #self.condition.wait(self.mutex)
        

    def stop(self):
        self.TheadActive = False
        cv2.destroyAllWindows()
        self.quit()
