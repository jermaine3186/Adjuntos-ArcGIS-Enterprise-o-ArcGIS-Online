#-------------------------------------------------------------------------------
# Name:        módulo1
# Purpose:
#
# Author:      osolis
#
# Created:     14/02/2023
# Copyright:   (c) osolis 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from arcgis import GIS
import pandas as pd
import os, sys
from os import walk
import requests
from urllib.error import HTTPError
import urllib.request
import arcpy
import re
#Conectarse al Portal
PORTAL = GIS("url", "usuario","contraseña")
token = PORTAL._con.token
servicio = PORTAL.content.get(arcpy.GetParameterAsText(0))
num_capa=int(arcpy.GetParameterAsText(1))
tipo=arcpy.GetParameterAsText(2)
if tipo=="capa":
    capa=(servicio.layers)[num_capa]
elif tipo=="tabla":
    capa =(servicio.tables)[num_capa]
cap_url=str(re.findall('htt.*'+str(num_capa), str(capa)))
cap_url=str(cap_url)[2:-2]
print(cap_url)
#Carpeta para almacenar las subcarpetas y los adjuntos
carpeta=arcpy.GetParameterAsText(3)
#construir dataframe
#sdf = capa.query().sdf
sdf = capa.query(where=arcpy.GetParameterAsText(5)+" IS NULL").sdf
#Lista vacia para almacenar los elementos a actualizar
elementos_a_actualizar = []
#Iterar a través del dataframe
for index, row in sdf.iterrows():
    objID=str(row[arcpy.GetParameterAsText(4)])
    Attachments = capa.attachments.get_list(oid=objID)
    if len(Attachments)>0:
        for k in range(len(Attachments)):
                    attachmentId = Attachments[k]['id']
                    attachmentName = Attachments[k]['name']
                    img_url = cap_url+"/{0}/attachments/{1}".format(objID,attachmentId)+"?token="+token
                    fileName = os.path.join(carpeta, attachmentName)
                    existe_archiv=os.path.exists(fileName)
                    if existe_archiv is True:
                        arcpy.AddMessage("No descargar")
                    else:
                        arcpy.AddMessage("Descargar ShapeFile "+attachmentName)
                        #Descarga con la direccion corregida
                        try:
                            arcpy.AddMessage("Obteniendo la URL del ShapeFile")
                            request=urllib.request.urlretrieve(img_url)
                            req = requests.get(img_url)
                            file = open(fileName, 'wb')
                            for chunk in req.iter_content(100000):
                                file.write(chunk)
                            file.close()
                            arcpy.AddMessage("ShapeFile "+attachmentName+" descargado en la carpeta "+carpeta+ " de forma correcta")
                            capa.attachments.delete(objID,attachmentId)
                        except urllib.error.HTTPError as err:
                            arcpy.AddMessage("Error "+str(err.code)+" no existe un ShapeFile para descargar o existe un problema de conexion")
        #Actualizar el campo de la direccion de la carpeta
        seleccion=capa.query(where=arcpy.GetParameterAsText(4)+"="+objID)
        elem_actualizar=(seleccion.features[0])
        elem_actualizar.attributes[arcpy.GetParameterAsText(5)]=str(fileName)
        elementos_a_actualizar.append(elem_actualizar)
#Actualizar el estado del curso
capa.edit_features(updates=elementos_a_actualizar)
###############################################################################
###Busca los archivos zip descargados y los sube como entidades################
formato="zip"
for (dir_path, dir_names, file_names) in walk(carpeta):
    for filename in file_names:
        shp=str(os.path.join(dir_path, filename))
        if formato in filename:
            Nombre=filename[0:-4]
            forlderportal="Shapes"
            arcpy.AddMessage("ShapeFile obtenido correctamente")
            #Conectarse al Portal
            servicio1 = PORTAL.content.get(arcpy.GetParameterAsText(6))
            num_capa1=int(arcpy.GetParameterAsText(7))
            capa1 = (servicio1.layers)[num_capa1]
            dfcapa=capa1.query().sdf
            #Meter el shapefile
            arcpy.AddMessage("Insertando el ShapeFile en el Portal")
            shp_adds = {"title":"SHAPE",
                    "type":"Shapefile",
                    "tags":"propiedades, fincas, nuevo registro",
                    "snippet":"Nuevo registro para agregar al servicio",
                    "description":"Datos subidos por la herramienta para copiar el shape"}
            item = PORTAL.content.add(item_properties=shp_adds,
                         data=shp)#,
                         #folder=forlderportal)
            id_csv=item.id
            arcpy.AddMessage("ShapeFile insertado en el Portal con el id "+id_csv)
            csv_item = PORTAL.content.get(id_csv)
            analyzed = PORTAL.content.analyze(item=csv_item,file_type="shapefile")
            publish_parameters = analyzed['publishParameters']
            publish_parameters['name'] = "POLIGONO_BORRAR"
            publish_parameters['editorTrackingInfo'] = '{enableEditorTracking": false,"enableOwnershipAccessControl": true,"allowOthersToQuery": true,"allowOthersToUpdate": true,"allowOthersToDelete": true,"allowAnonymousToUpdate": true,"allowAnonymousToDelete": true}'
            published_item = csv_item.publish(publish_parameters)
            shapefile=published_item.layers[0]
            seleccion=shapefile.query(where='1=1')
            arcpy.AddMessage("Insertando Shape en la capa")
            capa1.edit_features(adds = seleccion)
            arcpy.AddMessage("Shape insertado en la capa correctamente")
            published_item.delete()
            item.delete()