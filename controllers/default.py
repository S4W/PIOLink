# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------
import os

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    if not(request.args):
        if auth.is_logged_in():
            redirect(URL('redireccionando'))
        else:
            redirect(URL('index'))
    else:
        if request.args[0] == 'login':
            if auth.is_logged_in():
                redirect(URL('redireccionando'))
            else:
                redirect(URL('index'))
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

@auth.requires_login()
def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def index():
    if auth.is_logged_in():
        redirect(URL('default', 'user', args='logout')) # Si ya hay un usuario conectado, desconectarlo
    return dict(form=auth.login())

def redireccionando():
    if auth.is_logged_in():
        if 'Administrador' in auth.user_groups.values():
            redirect(URL('admin'))
        elif 'Estudiante' in auth.user_groups.values():
            redirect(URL('welcome'))
        elif 'Profesor' in auth.user_groups.values():
            redirect(URL('profesor'))
        elif 'Representante_liceo' in auth.user_groups.values():
            redirect(URL('coordinadorLiceo'))
        elif 'Representante_sede' in auth.user_groups.values():
            redirect(URL('coordinadorPio'))
        else:
            redirect(URL('default', 'user', args='logout'))
    else:
        redirect(URL('index'))
    return dict()

@auth.requires_membership('Administrador')
@auth.requires_login()
def admin():

    ##################
    # Carga de archivo
    ##################
    erroresCarga = [] # Los errores en la carga van aqui
    cargaExitosa = [] # Los usuarios agregados exitosamente van aqui
    cohorte = db(db.cohorte.activo==True).select()[0].identificador # Cohorte Actual
    formularioArchivo = FORM(
                            INPUT(_name='tituloArchivo', _type='text'),
                            INPUT(_name='archivo', _type='file')
                            )
    if formularioArchivo.accepts(request.vars,formname='formularioArchivo'): # Chequeamos si hay un archivo cargado
        archivo =request.vars.fileToUpload.filename.split(".")  # Separamos el nombre del archivo de la extension
        nombreArchivo, extension = archivo[0], archivo[1]
        if extension == "csv":          # Chequeamos la extension del archivo
            ######################
            # Cargando Estudiantes
            ######################
            if request.vars.optradio == "estudiante":   # Chequeamos el tipo de usuario a agregar
                f = request.vars.fileToUpload.file      # Archivo cargado
                texto = f.read().splitlines()           # Leer el archivo
                cabecera = texto[0].split(";")          # Extraemos la cabecera
                liceo = texto[1].split(";")             # Extraemos la linea que contiene el nombre del liceo
                texto.remove(texto[1])                  # Eliminamos del texto la linea del liceo para no iterar sobre ella
                texto.remove(texto[0])                  # Eliminamos del texto la cabecera para no iterar sobre ella
                if ((cabecera[0]=="C.I." and cabecera[1]=='Nombres' and
                cabecera[2]=='Apellidos' and cabecera[3]=='Promedio (00.00)') and
                (liceo[0] == "Nombre del Liceo:") and liceo[1] == "" and liceo[2] != ""): # Verificamos que la cabecera y la linea del liceo tenga el formato correcto
                    liceo = liceo[2]                    # Seleccionamos el nombre del liceo
                    datos = []                          # Los usuarios a agregar van aqui
                    for i in texto:
                        if i != ";;;;":
                            dato = i.split(";")         # Separamos los datos del usuario
                            datos.append(dato)          # Agregamos el usuario a la lista de usuarios por agregar

                    for i in datos:
                        if (not(db(db.usuario.username == i[0]).select()) and
                           not(db(db.estudiante.ci == i[0]).select())):         # Verificar que no existe un usuario para esa cedula
                            if 0 <= float(i[3]) <= 20:                          # Verificamos que el indice sea correcto
                                if db(db.liceo.nombre == liceo).select():       # Verificamos que el liceo este en la base de datos
                                    id = db.usuario.insert(first_name = i[1],last_name = i[2], email = "", username = i[0],
                                                  password = db.usuario.password.validate(i[0])[0], registration_key = "",
                                                  reset_password_key = "", registration_id = "" )       # Agregar el usuario
                                    db.auth_membership.insert(user_id = id, group_id= 1)                # Agregar permisos de estudiante (group_id=1)
                                    db.estudiante.insert(ci=i[0], promedio=float(i[3]), direccion="", telefono_habitacion="",
                                                    telefono_otro="", fecha_nacimiento="", sexo="", estatus="Pre-inscrito",
                                                    cohorte=cohorte, ci_representante="", nombre_representante="",
                                                    apellido_representante="", sexo_representante="", correo_representante="",
                                                    direccion_representante="", nombre_liceo=liceo, telefono_representante_oficina="",
                                                    telefono_representante_otro="", sufre_enfermedad="", enfermedad="",
                                                    indicaciones_enfermedad="")     # Agregamos el estudiante Cohorte deberia ser una variable global
                                    cargaExitosa.append(i)                          # Agregarlo a los estudiantes cargados exitosamente
                                else:
                                    erroresCarga.append([i,"Su liceo no esta en la base de datos. Contacte al administrador"])  # Error de Carga
                            else:
                                erroresCarga.append([i,"El promedio debe ser un numero entre 0 y 20"])                          # Error de Carga
                        else:
                            erroresCarga.append([i,"Ya existe un usuario en el sistema con esta cedula"])                       # Error de Carga

                else: #Error
                    erroresCarga.append("Formato de los datos del archivo invalido. Consulte el manual")                        # Error de Carga
            #################################
            # Cargando Representantes de sede
            #################################
            elif request.vars.optradio == "sede":
                f = request.vars.fileToUpload.file      # Archivo cargado
                texto = f.read().splitlines()           # Leer el archivo
                cabecera = texto[0].split(";")          # Extraemos la cabecera
                texto.remove(texto[0])                  # Eliminamos del texto la cabecera para no iterar sobre ella
                if (cabecera[0]=="C.I." and cabecera[1]=='Nombres' and
                    cabecera[2]=='Apellidos' and cabecera[3]=='Sede'): # Verificamos que la cabecera tenga el formato correcto
                    datos = []                          # Los usuarios a agregar van aqui
                    for i in texto:
                        if i != ";;;;":
                            dato = i.split(";")         # Separamos los datos del usuario
                            datos.append(dato)          # Agregamos el usuario a la lista de usuarios por agregar

                    for i in datos:
                        if (not(db(db.usuario.username == i[0]).select()) and
                            not(db(db.representante_sede.ci == i[0]).select())):    # Verificar que no existe un usuario para esa cedula
                            #if db(db.sede.nombre == i[3]).select():                # Verificamos que la sede este en la base de datos
                            id = db.usuario.insert(first_name = i[1],last_name = i[2], email = "", username = i[0],
                                          password = db.usuario.password.validate(i[0])[0], registration_key = "",
                                          reset_password_key = "", registration_id = "" ) # Agregar el usuario
                            db.auth_membership.insert(user_id = id, group_id=4) # Agregar permisos de representante sede (group_id=4)
                            db.representante_sede.insert(ci=i[0], sede=i[3]) # Agregar el representante de sede
                            cargaExitosa.append(i) # Agregarlo a los usuarios cargados exitosamente
                            #else:
                                #erroresCarga.append([i,"Su sede no esta en la base de datos. Contacte al administrador"])  # Error de Carga
                        else:
                            erroresCarga.append([i,"Ya existe un usuario en el sistema con esta cedula"])                   # Error de Carga
                else: #Error
                    erroresCarga.append("Formato de los datos del archivo invalido. Consulte el manual")                    # Error de Carga
            ##################################
            # Cargando Representante de liceos
            ##################################
            elif request.vars.optradio == "liceo":
                f = request.vars.fileToUpload.file      # Archivo cargado
                texto = f.read().splitlines()           # Leer el archivo
                cabecera = texto[0].split(";")          # Extraemos la cabecera
                texto.remove(texto[0])                  # Eliminamos del texto la cabecera para no iterar sobre ella
                if (cabecera[0]=="C.I." and cabecera[1]=='Nombres' and
                cabecera[2]=='Apellidos' and cabecera[3]=='Liceo'): # Verificamos que la cabecera tenga el formato correcto
                    datos = []                          # Los usuarios a agregar van aqui
                    for i in texto:
                        if i != ";;;;":
                            dato = i.split(";")         # Separamos los datos del usuario
                            datos.append(dato)          # Agregamos el usuario a la lista de usuarios por agregar

                    for i in datos:
                        if (not(db(db.usuario.username == i[0]).select()) and
                            not(db(db.representante_liceo.ci == i[0]).select())):    # Verificar que no existe un usuario para esa cedula
                            if db(db.liceo.nombre == i[3]).select():                # Verificamos que el liceo este en la base de datos
                                id = db.usuario.insert(first_name = i[1],last_name = i[2], email = "", username = i[0],
                                              password = db.usuario.password.validate(i[0])[0], registration_key = "",
                                              reset_password_key = "", registration_id = "" ) # Agregar el usuario
                                db.auth_membership.insert(user_id = id, group_id=3) # Agregar permisos de representante liceo (group_id=3)
                                db.representante_liceo.insert(ci=i[0], nombre_liceo=i[3]) # Agregar el representante de liceo
                                cargaExitosa.append(i) # Agregarlo a los usuarios cargados exitosamente
                            else:
                                erroresCarga.append([i,"Su liceo no esta en la base de datos. Contacte al administrador"])  # Error de Carga
                        else:
                            erroresCarga.append([i,"Ya existe un usuario en el sistema con esta cedula"])                   # Error de Carga
                else: #Error
                    erroresCarga.append("Formato de los datos del archivo invalido. Consulte el manual")                    # Error de Carga
            #####################
            # Cargando Profesores
            #####################
            elif request.vars.optradio == "profesor":
                erroresCarga.append("Opcion no disponible por el momento. Disculpe las molestias")
            #####################
            # Cargando Liceos
            #####################
            elif request.vars.optradio == "liceos":
                f = request.vars.fileToUpload.file      # Archivo cargado
                texto = f.read().splitlines()           # Leer el archivo
                cabecera = texto[0].split(";")          # Extraemos la cabecera
                texto.remove(texto[0])                  # Eliminamos del texto la cabecera para no iterar sobre ella
                if (cabecera[0]=="Nombre del Liceo" and cabecera[2]=='Tipo del Liceo' and
                cabecera[4]=='Zona'):                   # Verificamos que la cabecera tenga el formato correcto
                    datos = []                          # Los liceos a agregar van aqui
                    for i in texto:
                        if i != ";;;;":
                            dato = i.split(";")         # Separamos los datos del usuario
                            datos.append(dato)          # Agregamos el usuario a la lista de usuarios por agregar

                    for i in datos:
                        if not(db(db.liceo.nombre == i[0]).select()):               # Verificar que no existe un liceo con ese nombre
                            db.liceo.insert(nombre = i[0], tipo = i[2], zona = i[4]) # Agregar el liceos
                            cargaExitosa.append(i) # Agregarlo a los liceos cargados exitosamente
                        else:
                            erroresCarga.append([i,"Ya existe un liceo en el sistema con ese nombre"])                      # Error de Carga
                else: #Error
                    erroresCarga.append("Formato de los datos del archivo invalido. Consulte el manual")                    # Error de Carga
        else: #Error
            erroresCarga.append("El formato del archivo debe ser \".csv\". Consulte el manual de usuario")
    else:
        pass

    ######################
    # Fin Carga de Archivo
    ######################


    ########################
    ###Consula de datos
    ########################
    T.force('es')
    username = auth.user.username
    usuario = db(db.usuario.username==username).select().first()
    #tipo=""
    #error = False

    formAdministrador = SQLFORM.factory(
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('username',
            type='string',
            notnull = True,
            default=usuario.username,
            requires=db.usuario.username.requires,
            label='ci'
            ),
        Field('email',
            type='string',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formAdministrador.process(session=None, formname='perfil del administrador', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formAdministrador.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'
    ############################
    ###fin de Consula de datos
    ############################

    return dict(formAdministrador=formAdministrador, erroresCarga=erroresCarga, cargaExitosa=cargaExitosa)

@auth.requires_membership('Profesor')
@auth.requires_login()
def profesor():
    return dict()

@auth.requires_membership('Representante_liceo')
@auth.requires_login()
def coordinadorLiceo():

    ##################
    # Carga de archivo
    ##################
    erroresCarga = [] # Los errores en la carga van aqui
    cargaExitosa = [] # Los usuarios agregados exitosamente van aqui
    cohorte = db(db.cohorte.activo==True).select()[0].identificador # Cohorte Actual
    liceo = db(db.representante_liceo.ci == auth.user.username).select()[0].nombre_liceo # Liceo al que pertenece el representante logiado

    formularioArchivo = FORM(
                            INPUT(_name='tituloArchivo', _type='text'),
                            INPUT(_name='archivo', _type='file')
                            )
    if formularioArchivo.accepts(request.vars,formname='formularioArchivo'): # Chequeamos si hay un archivo cargado
        archivo =request.vars.fileToUpload.filename.split(".")  # Separamos el nombre del archivo de la extension
        nombreArchivo, extension = archivo[0], archivo[1]
        if extension == "csv":          # Chequeamos la extension del archivo
            ######################
            # Cargando Estudiantes
            ######################
            f = request.vars.fileToUpload.file      # Archivo cargado
            texto = f.read().splitlines()           # Leer el archivo
            cabecera = texto[0].split(";")          # Extraemos la cabecera
            texto.remove(texto[0])                  # Eliminamos del texto la cabecera para no iterar sobre ella
            if (cabecera[0]=="C.I." and cabecera[1]=='Nombres' and
            cabecera[2]=='Apellidos' and cabecera[3]=='Promedio (00.00)'): # Verificamos que la cabecera tenga el formato correcto
                datos = []                          # Los usuarios a agregar van aqui
                for i in texto:
                    if i != ";;;;":
                        dato = i.split(";")         # Separamos los datos del usuario
                        datos.append(dato)          # Agregamos el usuario a la lista de usuarios por agregar

                for i in datos:
                    if (not(db(db.usuario.username == i[0]).select()) and
                       not(db(db.estudiante.ci == i[0]).select())):         # Verificar que no existe un usuario para esa cedula
                        if 0 <= float(i[3]) <= 20:                          # Verificamos que el indice sea correcto
                            if db(db.liceo.nombre == liceo).select():       # Verificamos que el liceo este en la base de datos
                                id = db.usuario.insert(first_name = i[1],last_name = i[2], email = "", username = i[0],
                                              password = db.usuario.password.validate(i[0])[0], registration_key = "",
                                              reset_password_key = "", registration_id = "" )       # Agregar el usuario
                                db.auth_membership.insert(user_id = id, group_id= 1)                # Agregar permisos de estudiante (group_id=1)
                                db.estudiante.insert(ci=i[0], promedio=float(i[3]), direccion="", telefono_habitacion="",
                                                telefono_otro="", fecha_nacimiento="", sexo="", estatus="Pre-inscrito",
                                                cohorte=cohorte, ci_representante="", nombre_representante="",
                                                apellido_representante="", sexo_representante="", correo_representante="",
                                                direccion_representante="", nombre_liceo=liceo, telefono_representante_oficina="",
                                                telefono_representante_otro="", sufre_enfermedad="", enfermedad="",
                                                indicaciones_enfermedad="")     # Agregamos el estudiante Cohorte deberia ser una variable global
                                cargaExitosa.append(i)                          # Agregarlo a los estudiantes cargados exitosamente
                            else:
                                erroresCarga.append([i,"Su liceo no esta en la base de datos. Contacte al administrador"])  # Error de Carga
                        else:
                            erroresCarga.append([i,"El promedio debe ser un numero entre 0 y 20"])                          # Error de Carga
                    else:
                        erroresCarga.append([i,"Ya existe un usuario en el sistema con esta cedula"])                       # Error de Carga

            else: #Error
                erroresCarga.append("Formato de los datos del archivo invalido. Consulte el manual")                        # Error de Carga

        else: #Error
            erroresCarga.append("El formato del archivo debe ser \".csv\". Consulte el manual de usuario")
    else:
        pass

    ######################
    # Fin Carga de Archivo
    ######################
    ########################
    ###Consula de datos
    ########################
    T.force('es')
    username = auth.user.username
    representante_liceo=db(db.representante_liceo.ci==username).select().first()
    usuario = db(db.usuario.username==username).select().first()
    #tipo=""
    #error = False

    formDatosBasicos = SQLFORM.factory(
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('username',
            type='string',
            notnull = True,
            default=usuario.username,
            requires=db.usuario.username.requires,
            label='ci'
            ),
        Field('email',
            type='string',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formDatosBasicos.process(session=None, formname='perfil basico del Representante liceo de sede', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formDatosBasicos.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'

    formCoordinadorLiceo = SQLFORM.factory(
        Field('ci',
            type='string',
            notnull=True,
            default=representante_liceo.ci,
            requires=db.representante_liceo.ci.requires,
            label='ci'
            ),
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('nombre_liceo',
            type='string',
            default=representante_liceo.nombre_liceo,
            requires=db.representante_liceo.nombre_liceo.requires,
            label='nombre_liceo'
            ),
        Field('email',
            type='date',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formCoordinadorLiceo.process(session=None, formname='perfil del Representante Liceo de sede', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formCoordinadorLiceo.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'
    ############################
    ###fin de Consula de datos
    ############################

    return dict(formCoordinadorLiceo=formCoordinadorLiceo, formDatosBasicos=formDatosBasicos, erroresCarga=erroresCarga, cargaExitosa=cargaExitosa)

@auth.requires_membership('Representante_sede')
@auth.requires_login()
def coordinadorPio():

    ########################
    ###Consula de datos
    ########################
    T.force('es')
    username = auth.user.username
    representante_sede=db(db.representante_sede.ci==username).select().first()
    usuario = db(db.usuario.username==username).select().first()
    #tipo=""
    #error = False

    formDatosBasicos = SQLFORM.factory(
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('username',
            type='string',
            notnull = True,
            default=usuario.username,
            requires=db.usuario.username.requires,
            label='ci'
            ),
        Field('email',
            type='string',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formDatosBasicos.process(session=None, formname='perfil basico del Representante PIO de sede', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formDatosBasicos.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'

    formCoordinadorPio = SQLFORM.factory(
        Field('ci',
            type='string',
            notnull=True,
            default=representante_sede.ci,
            requires=db.representante_sede.ci.requires,
            label='ci'
            ),
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('sede',
            type='string',
            default=representante_sede.sede,
            requires=db.representante_sede.sede.requires,
            label='sede'
            ),
        Field('email',
            type='date',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formCoordinadorPio.process(session=None, formname='perfil del Representante PIO de sede', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formCoordinadorPio.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'
    ############################
    ###fin de Consula de datos
    ############################

    return dict(formDatosBasicos=formDatosBasicos, formCoordinadorPio=formCoordinadorPio)

@auth.requires_membership('Estudiante')
@auth.requires_login()
def welcome():

    ########################
    ###Consula de datos
    ########################
    T.force('es')
    username = auth.user.username
    estudiante=db(db.estudiante.ci==username).select().first()
    usuario = db(db.usuario.username==username).select().first()
    #tipo=""
    #error = False

    formDatosBasicos = SQLFORM.factory(
        Field('first_name' +  'last_name',
            type='string',
            default=usuario.first_name + " " + usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('username',
            type='string',
            notnull = True,
            default=usuario.username,
            requires=db.usuario.username.requires,
            label='ci'
            ),
        Field('email',
            type='string',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email'),
        readonly = True
        )

    if formDatosBasicos.process(session=None, formname='perfil basico del Estudiante', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formDatosBasicos.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'

    formEstudiante = SQLFORM.factory(
        Field('ci',
            type='string',
            notnull=True,
            default=estudiante.ci,
            requires=db.estudiante.ci.requires,
            label='ci'
            ),
        Field('first_name',
            type='string',
            default=usuario.first_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='nombre'
            ),
        Field('last_name',
            type='string',
            default=usuario.last_name,
            requires=db.usuario.first_name.requires and db.usuario.last_name.requires,
            label='apellido'
            ),

        Field('sexo',
            type='string',
            default=estudiante.sexo,
            requires=db.estudiante.sexo.requires,
            label='sexo'
            ),
        Field('fecha_nacimiento',
            type='date',
            default=estudiante.fecha_nacimiento,
            requires=db.estudiante.fecha_nacimiento.requires,
            label='fecha_de_nacimiento'
            ),
        Field('promedio',
            type='string',
            default= estudiante.promedio,
            requires=db.estudiante.promedio.requires,
            label='promedio'
            ),
        Field('nombre_liceo',
            type='string',
            default="            "+estudiante.nombre_liceo,
            requires=db.estudiante.nombre_liceo.requires,
            label='nombre_liceo'
            ),
        Field('email',
            type='string',
            default=usuario.email,
            requires=db.usuario.email.requires,
            label='email',
            ),
        Field('telefono_habitacion',
            type='integer',
            default=estudiante.telefono_habitacion,
            requires=db.estudiante.telefono_habitacion.requires,
            label='telefono_habitacion',
            ),
        Field('direccion',
            type='string',
            default= estudiante.direccion,
            requires=db.estudiante.direccion.requires,
            label='direccion'),
        readonly = True
        )

    if formEstudiante.process(session=None, formname='perfil del Estudiante', keepvalues=True).accepted:
        response.flash = 'El formulario fue aceptado exitosamente.'

    elif formEstudiante.errors:
        #error = True
        response.flash = 'Hay un error en un campo.'

    ############################
    ###fin de Consula de datos
    ############################

    return dict(formDatosBasicos = formDatosBasicos, formEstudiante = formEstudiante)
