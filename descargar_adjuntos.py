#-------------------------------------------------------------------------------
# Name:        descargar adjuntos
# Purpose:
#
# Author:      osolis
#
# Created:     23/09/2022
# Copyright:   (c) osolis 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from arcgis import GIS
import pandas as pd
import os, sys
import requests
from urllib.error import HTTPError
import urllib.request
import arcpy
import re
#Conectarse al Portal
PORTAL = GIS(arcpy.GetParameterAsText(0), arcpy.GetParameterAsText(1),arcpy.GetParameterAsText(2))
token = PORTAL._con.token
servicio = PORTAL.content.get(arcpy.GetParameterAsText(3))
num_capa=int(arcpy.GetParameterAsText(4))
tipo=arcpy.GetParameterAsText(5)
if tipo=="capa":
    capa=(servicio.layers)[num_capa]
elif tipo=="tabla":
    capa =(servicio.tables)[num_capa]
cap_url=str(re.findall('htt.*'+str(num_capa), str(capa)))
cap_url=str(cap_url)[2:-2]
print(cap_url)
#Carpeta para almacenar las subcarpetas y los adjuntos
carpeta=arcpy.GetParameterAsText(6)
#construir dataframe
sdf = capa.query().sdf
#Lista vacia para almacenar los elementos a actualizar
elementos_a_actualizar = []
#Iterar a través del dataframe
for index, row in sdf.iterrows():
    objID=str(row[arcpy.GetParameterAsText(7)])
    ID=str(row[arcpy.GetParameterAsText(8)])
    #Revisa si la direccion de la carpeta termina con espacio o tiene un espacio
    final=ID.endswith(' ')
    inicio=ID.startswith(' ')
    if inicio and final==True:
        print("Corregir direccion")
        ID=ID[1:-1]
    elif final==True and inicio==False:
        print("Corregir direccion")
        ID=ID[0:-1]
    elif inicio==True and final==False:
        print("Corregir direccion")
        ID=ID[1:]
    else:
        print("Direccion correcta")
    carpe_adjun=objID+"_"+ID
    #Crear direcciones para adjuntos
    direccion=os.path.join(carpeta, carpe_adjun)
    #Crear nueva carpeta
    existe=os.path.exists(direccion)
    if existe is True:
        arcpy.AddMessage("No crear carpeta")
    else:
        arcpy.AddMessage("Creando Carpeta "+str(direccion))
        os.mkdir(direccion)
    Attachments = capa.attachments.get_list(oid=objID)
    for k in range(len(Attachments)):
                attachmentId = Attachments[k]['id']
                attachmentName = Attachments[k]['name']
                img_url = cap_url+"/{0}/attachments/{1}".format(objID,attachmentId)+"?token="+token
                fileName = os.path.join(direccion, attachmentName)
                existe_archiv=os.path.exists(fileName)
                if existe_archiv is True:
                    arcpy.AddMessage("No descargar")
                else:
                    arcpy.AddMessage("Descargar imagen "+attachmentName)
                    #Descarga con la direccion corregida
                    try:
                        arcpy.AddMessage("Obteniendo la URL de la imagen")
                        request=urllib.request.urlretrieve(img_url)
                        req = requests.get(img_url)
                        file = open(fileName, 'wb')
                        for chunk in req.iter_content(100000):
                            file.write(chunk)
                        file.close()
                        arcpy.AddMessage("Imagen "+attachmentName+" descargada en la carpeta "+direccion+ " de forma correcta")
                    except urllib.error.HTTPError as err:
                        arcpy.AddMessage("Error "+str(err.code)+" no existe una imagen para descargar o existe un problema de conexion")
    #Actualizar el campo de la direccion de la carpeta
    seleccion=capa.query(where=arcpy.GetParameterAsText(7)+"="+objID)
    elem_actualizar=(seleccion.features[0])
    elem_actualizar.attributes[arcpy.GetParameterAsText(9)]=direccion
    elementos_a_actualizar.append(elem_actualizar)
print(elementos_a_actualizar)
#Actualizar el estado del curso
capa.edit_features(updates=elementos_a_actualizar)