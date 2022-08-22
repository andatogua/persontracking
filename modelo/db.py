from datetime import date
from ntpath import join
import os
from PyQt5.QtSql import *
from PyQt5.QtWidgets import QMessageBox
from configuracion.conf import BASE_DIR

class BaseDatos:
    def __init__(self,nombre,servidor):
        
        self.nombre = os.path.join(BASE_DIR,f"modelo/{nombre}")
        self.servidor = servidor
        

        # Método para crear la base de datos
    def db_connect(self): # Recibe dos parametros: nombre de la base de datos, y el tipo.
        db = QSqlDatabase.addDatabase(self.servidor) # Creamos la base de datos
        db.setDatabaseName(self.nombre) # Le asignamos un nombre
        if not db.open(): # En caso de que no se abra
            QMessageBox.critical(None, "Error al abrir la base de datos.nn"
                    "Click para cancelar y salir.", QMessageBox.Cancel)
            return False
        return True

        # Método para crear la tabla personas
    def db_create(self):
        query = QSqlQuery() # Instancia de Query
        #Ejecutamos la sentencia para crear la tabla personas con 3 columnas
        query.exec_("create table if not exists registro(id integer primary key autoincrement, "
                    "inicio text, final text, numpersonas int, numcamaras int, detallecam text)")

        # Método para ejecutar la base de datos
    def init(self):
        import os # Importamos os
        if not os.path.exists(self.nombre):
            self.db_connect() # Llamamos a "db_connect"
            self.db_create() # Llamamis a "db_create"
            print("BD Creada")
        else:
            self.db_connect()
            print("BD Conectada")

    def guardarregistro(self,inicio, final, numpersonas, numcamaras,detallecam):
        
        query = QSqlQuery()
        query.exec_(f"insert into registro (inicio,final,numpersonas,numcamaras,detallecam) values('{inicio}','{final}',{numpersonas},{numcamaras},'{detallecam}')")

    def getregistrodiario(self):
        query = QSqlQuery()
        hoy = date.today()
        #query.exec_(f"select count(final) from registro where date(final) = {hoy}")
        query.exec_("SELECT count(final) FROM registro WHERE date(inicio) = '" +str(hoy)+"'")
        while query.next():
            print(query.value(0))
            return query.value(0)
