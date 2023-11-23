# IMPORT PARA EL SISTEMA

# -------------------------------------------------------------------------------------------------------------

import dbm
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    jsonify,
    make_response,
    send_from_directory,
)
from flask_principal import Principal, Permission, RoleNeed, identity_loaded
import sqlite3
from datetime import datetime
import matplotlib

matplotlib.use("Agg")  # MATPLOTLIB EN MODO NO INTERACTIVO
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
import csv
import base64
from io import BytesIO
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from jinja2 import Template
from fpdf import FPDF
from collections import defaultdict
import glob
from functools import wraps

# -------------------------------------------------------------------------------------------------------------
# VARIABLES
app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tu_basededatos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.secret_key = "goku1997"

# Configuración de Flask-Principal
principal = Principal(app)

# ---- VARIABLES ----
# Configura la ubicación de tu base de datos SQLite
DATABASE = "BDD.db"
# Agregar esta línea al principio de tu código Flask para crear una lista vacía de compras
lista_compra = []


# ---- Conexion BDD ----
# conectar
def conectar_base_de_datos():
    conexion = sqlite3.connect("BDD.db")
    return conexion


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Rutas Permisos por Rol
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# Define permisos y necesidades de roles
admin_permission = Permission(RoleNeed("administrador"))
vendedor_permission = Permission(RoleNeed("vendedor"))


# Decorador para requerir el rol de administrador
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session.get("user_role") != "administrador":
            return render_template("acceso_no_autorizado.html")
        return func(*args, **kwargs)

    return decorated_view


# Decorador para requerir el rol de vendedor
def vendedor_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session.get("user_role") != "vendedor":
            flash(
                "Acceso no autorizado. Debes ser vendedor para ver esta página.",
                "error",
            )
            return redirect(url_for("dashboard"))  # Redirige a una página adecuada
        return func(*args, **kwargs)

    return decorated_view


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Rutas de acceso para html
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# Ruta Login
@app.route("/", methods=["GET"])
def show_login_form():
    return render_template("login.html")


# Ruta index / home
@app.route("/index")
def pagina_de_inicio():
    if "logged_in" in session and session["logged_in"]:
        username = session["usuario_actual"]
        # Leer la información de la empresa desde el archivo empresa.csv (si existe)
        informacion_empresa = {}
        if os.path.isfile("empresa.csv"):
            with open("empresa.csv", mode="r", newline="") as archivo_csv:
                lector_csv = csv.DictReader(archivo_csv)
                for row in lector_csv:
                    informacion_empresa = row
        # Llama a la función para obtener las últimas 3 ventas
        ultimas_ventas = obtener_ultimas_ventas()
        # Llama a la función para obtener la cantidad total de ventas
        cantidad_total_ventas = obtener_cantidad_de_ventas()
        # Llama a la función para obtener la cantidad total de usuarios
        cantidad_total_usuarios = obtener_cantidad_de_usuarios()
        # Llama a la función para obtener la cantidad total de artículos en la base de datos
        cantidad_total_articulos = obtener_cantidad_de_articulos()

        # Registra la acción en el archivo CSV
        usuario_actual = session.get("usuario_actual")
        accion = "Inicio Index"
        registrar_actividad(usuario_actual, accion)

        return render_template(
            "index.html",
            username=username,
            ultimas_ventas=ultimas_ventas,
            cantidad_total_ventas=cantidad_total_ventas,
            cantidad_total_usuarios=cantidad_total_usuarios,
            cantidad_total_articulos=cantidad_total_articulos,
            informacion_empresa=informacion_empresa,
        )
    else:
        return redirect(url_for("show_login_form"))


# Ruta ventas
@app.route("/ventas")
def pagina_ventas():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Ventas"
    registrar_actividad(usuario_actual, accion)

    datos = obtener_datos_de_articulo()
    if datos is not None:
        return render_template(
            "ventas.html", articulos=datos, username=session.get("usuario_actual")
        )


# Ruta reportes
@app.route("/reportes")
def pagina_de_reportes():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Reportes"
    registrar_actividad(usuario_actual, accion)

    return render_template("reportes.html", username=session.get("usuario_actual"))


# Ruta inventario
@app.route("/inventario")
@admin_required
def pagina_de_inventario():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Inventario"
    registrar_actividad(usuario_actual, accion)

    return render_template("inventario.html", username=session.get("usuario_actual"))


# Ruta registro de articulos
@app.route("/registro")
@admin_required
def pagina_de_registro():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Registro de Articulo"
    registrar_actividad(usuario_actual, accion)

    return render_template("registro.html", username=session.get("usuario_actual"))


@app.route("/registro", methods=["GET"])
def mostrar_formulario():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Registro de Articulo"
    registrar_actividad(usuario_actual, accion)

    return render_template("registro.html", username=session.get("usuario_actual"))


# Ruta confirmaciones
@app.route("/confirmacion")
def confirmacion():
    return render_template("confirmacion.html", username=session.get("usuario_actual"))


# Ruta de ediciones de articulo
@app.route("/editar")
@admin_required
def pagina_de_editar():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Editar Articulo"
    registrar_actividad(usuario_actual, accion)

    datos = obtener_datos_de_articulo()
    if datos is not None:
        return render_template(
            "editar.html", articulos=datos, username=session.get("usuario_actual")
        )


@app.route("/mostrar_auditoria")
def mostrar_auditoria_ventas():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio mostrar auditoria"
    registrar_actividad(usuario_actual, accion)

    registros_inicios_sesion = leer_registros_inicios_sesion()
    return render_template(
        "auditoria_inicio.html",
        registros_inicios_sesion=registros_inicios_sesion,
        username=session.get("usuario_actual"),
    )


@app.route("/mostrar_auditoria")
def mostrar_auditoria_inicio():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio mostrar auditoria"
    registrar_actividad(usuario_actual, accion)

    return render_template(
        "auditoria_inicio.html", username=session.get("usuario_actual")
    )


# Ruta para mostrar el formulario de modificación de folios
@app.route("/modificar_folios", methods=["GET"])
@admin_required
def mostrar_formulario_modificar_folios():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Cambiar Folio"
    registrar_actividad(usuario_actual, accion)

    return render_template(
        "modificar_folios.html", username=session.get("usuario_actual")
    )


@app.route("/registro_usuario", methods=["GET"])
@admin_required
def mostrar_formulario_registro_usuario():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Registro usuario"
    registrar_actividad(usuario_actual, accion)

    return render_template(
        "registro_usuario.html", username=session.get("usuario_actual")
    )


@app.route("/ver_datos")
def ver_datos():
    datos = obtener_datos_de_articulo()

    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Inventario"
    registrar_actividad(usuario_actual, accion)

    if datos is not None:
        return render_template(
            "ver_datos.html", articulos=datos, username=session.get("usuario_actual")
        )  # Asegúrate de usar 'articulos'
    else:
        return "Error al obtener datos de la base de datos."


# Ruta para mostrar los registros de auditoría
@app.route("/registros_auditoria", methods=["GET"])
def mostrar_registros_auditoria():
    # Leer los datos del archivo CSV
    registros = []
    with open("registroauditoria_usuario.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        for fila in lector_csv:
            registros.append(fila)

    # Pasar los registros a la plantilla HTML
    return render_template("registros_auditoria.html", registros=registros)


# -------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------- PRUEBAS
# -------------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado Registro
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


@app.route("/registro", methods=["GET", "POST"])
def registro_producto():
    if request.method == "POST":
        id_producto = request.form["id"]
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        cantidad = request.form["cantidad"]
        precio = request.form["precio"]
        ubicacion = request.form["ubicacion"]
        cantidad_maxima = request.form["cantidad_maxima"]
        cantidad_minima = request.form["cantidad_minima"]

        try:
            # Conecta con la base de datos
            conn = sqlite3.connect(
                "BDD.db"
            )  # Reemplaza con el nombre de tu base de datos
            cursor = conn.cursor()

            # Verifica si el producto ya existe en la base de datos
            cursor.execute("SELECT id FROM articulo WHERE id = ?", (id_producto,))
            producto_existente = cursor.fetchone()

            if producto_existente:
                flash(
                    f"El producto con ID {id_producto} ya existe en la base de datos.",
                    "error",
                )
            else:
                # Registra el nuevo producto en la base de datos
                cursor.execute(
                    "INSERT INTO articulo (id, nombre, descripcion, cantidad, precio, ubicacion,cantidad_maxima,cantidad_minima) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        id_producto,
                        nombre,
                        descripcion,
                        cantidad,
                        precio,
                        ubicacion,
                        cantidad_maxima,
                        cantidad_minima,
                    ),
                )
                conn.commit()
                flash(f'Se ha registrado el producto "{nombre}" con éxito.', "success")

                # Obtén el ID del artículo recién agregado
                id_producto_agregado = id_producto  # se llama a la id del producto

                # Después de agregar el artículo, registra la actividad con el ID
                usuario_actual = session.get("usuario_actual")
                accion = f"Agregó un artículo (ID: {id_producto_agregado})"
                registrar_actividad(usuario_actual, accion)

                # Auditoría: Registrar los detalles del producto en un archivo CSV
                fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nombre_archivo_csv = "registro.csv"

                with open(nombre_archivo_csv, mode="a", newline="") as archivo_csv:
                    escritor_csv = csv.writer(archivo_csv)
                    escritor_csv.writerow(
                        [
                            id_producto,
                            nombre,
                            cantidad,
                            precio,
                            cantidad_maxima,
                            cantidad_minima,
                            fecha_hora_actual,
                        ]
                    )

            conn.close()

        except sqlite3.Error as e:
            flash(f"Error en la base de datos: {str(e)}", "error")

        # Redirige a la página de confirmación
        return redirect(url_for("confirmacion"))


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado Login del sistema
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


def registrar_actividad(usuario, accion):
    # Genera una ID única basada en la fecha y hora actual
    registro_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # Obtiene la fecha y hora actual
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Abre el archivo CSV en modo de escritura (append) y escribe la información
    with open("registroauditoria_usuario.csv", mode="a", newline="") as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)
        escritor_csv.writerow([registro_id, usuario, accion, fecha_hora])


# Función para verificar las credenciales del usuario
def verify_user(username, password):
    with open("users.txt", "r") as file:
        for line in file:
            parts = line.strip().split(":")
            if len(parts) == 3:
                stored_username, stored_password, user_role = parts
                print(
                    f"User: {stored_username}, Password: {stored_password}, Role: {user_role}"
                )
                if username == stored_username and password == stored_password:
                    return user_role
    return None


# Ruta para procesar el formulario de inicio de sesión
# En la ruta de login, puedes manejar el mensaje de error
# Ruta para procesar el formulario de inicio de sesión
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_role = verify_user(username, password)

        if user_role == "administrador":
            session["logged_in"] = True
            session["usuario_actual"] = username
            session["user_role"] = "administrador"

            fecha_inicio_sesion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("iniciosesion.txt", "a") as file:
                file.write(
                    f"Usuario: {username}, Fecha de inicio de sesión: {fecha_inicio_sesion}\n"
                )

            flash("Inicio de sesión exitoso como administrador.", "success")
            return redirect(url_for("dashboard"))
        elif user_role == "vendedor":
            session["logged_in"] = True
            session["usuario_actual"] = username
            session["user_role"] = "vendedor"

            fecha_inicio_sesion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("iniciosesion.txt", "a") as file:
                file.write(
                    f"Usuario: {username}, Fecha de inicio de sesión: {fecha_inicio_sesion}\n"
                )

            flash("Inicio de sesión exitoso como vendedor.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas. Inténtalo de nuevo.", "error")
            return render_template("login.html", username=session.get("usuario_actual"))
    return render_template("login.html", username=session.get("usuario_actual"))


# Ruta protegida que requiere inicio de sesión
@app.route("/index")
def dashboard():
    if "logged_in" in session and session["logged_in"]:
        user_role = session.get("user_role")
        print(f"User Role: {user_role}")  # Agrega esta línea para depuración
        if user_role == "administrador":
            return redirect(url_for("dashboard"))
        elif user_role == "vendedor":
            # Usuario con rol de vendedor, muestra las opciones limitadas
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("show_login_form"))


@app.route("/logout", methods=["POST"])
def logout():
    if "logged_in" in session and session["logged_in"]:
        # Obtén el nombre de usuario actual
        usuario_actual = session.get("usuario_actual")

        # Registra la actividad de cierre de sesión
        accion = "Cierre de sesión"
        registrar_actividad(usuario_actual, accion)

        # Elimina la información de la sesión para cerrar la sesión
        session.pop("logged_in", None)
        session.pop("usuario_actual", None)
        flash("Sesión cerrada con éxito.", "success")
    return redirect(url_for("show_login_form"))


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado DE ARTICULO
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


def obtener_datos_de_articulo():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, descripcion, cantidad, precio, ubicacion, cantidad_maxima, cantidad_minima FROM articulo"
        )
        datos = cursor.fetchall()
        conn.close()
        return datos
    except sqlite3.Error as e:
        print("Error al obtener datos de la base de datos:", e)
        return None


# Ruta para obtener datos en tiempo real desde la base de datos de artículos
@app.route("/obtener_datos_articulos", methods=["GET"])
def obtener_datos_articulos():
    datos = obtener_datos_de_articulo()
    if datos:
        return jsonify(datos)
    else:
        return jsonify({"error": "No se pudieron obtener los datos de los artículos"})


# Ruta para procesar la búsqueda de producto
@app.route("/buscar_producto", methods=["POST"])
def buscar_producto():
    if request.method == "POST":
        # Obtén el código de barras ingresado por el usuario
        codigo_barras = request.form["codigo_barras"]

        # Realiza la búsqueda en la base de datos para obtener los datos del producto
        conn = sqlite3.connect(
            "BDD.db"
        )  # Asegúrate de usar el nombre correcto de tu base de datos
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulo WHERE id = ?", (codigo_barras,))
        producto = (
            cursor.fetchone()
        )  # Obtiene el producto con el código de barras especificado
        conn.close()

        if producto:
            # Si se encuentra el producto, muestra los detalles del producto
            return render_template("resultados.html", producto=producto)
        else:
            mensaje = "Producto no encontrado."
            return render_template("resultados.html", mensaje=mensaje)


# Ruta para procesar la búsqueda de producto
@app.route("/buscar_producto2", methods=["POST"])
def buscar_producto2():
    if request.method == "POST":
        # Obtén el código de barras ingresado por el usuario
        codigo_barras = request.form["codigo_barras"]

        # Realiza la búsqueda en la base de datos para obtener los datos del producto
        conn = sqlite3.connect(
            "BDD.db"
        )  # Asegúrate de usar el nombre correcto de tu base de datos
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulo WHERE id = ?", (codigo_barras,))
        producto = (
            cursor.fetchone()
        )  # Obtiene el producto con el código de barras especificado
        conn.close()

        if producto:
            # Si se encuentra el producto, muestra los detalles del producto
            return render_template("resultados2.html", producto=producto)
        else:
            mensaje = "Producto no encontrado."
            return render_template("resultados2.html", mensaje=mensaje)


# Route to display the edit form
@app.route("/editar", methods=["GET"])
def mostrar_formulario_editar():
    return render_template("editar.html")


# Route to process the form submission and edit the database
@app.route("/editar", methods=["POST"])
def editar_articulo():
    if request.method == "POST":
        # Get the article ID from the form
        id = request.form["id"]

        # Connect to the database
        conn = conectar_base_de_datos()
        cursor = conn.cursor()

        # Check if the article with the given ID exists
        cursor.execute("SELECT * FROM articulo WHERE id = ?", (id,))
        existing_article = cursor.fetchone()

        if existing_article:
            # Build the SQL update statement based on user inputs
            update_values = {}
            for field in ["nombre", "cantidad", "precio", "ubicacion"]:
                if request.form.get(field):
                    update_values[field] = request.form[field]

            # Generate an alert message with the updated fields
            alert_message = f"Artículo ID: {id}, Datos actualizados: {', '.join([f'{key}: {value}' for key, value in update_values.items()])}"

            # Update the database if there are changes
            if update_values:
                set_clause = ", ".join([f"{key} = ?" for key in update_values.keys()])
                cursor.execute(
                    f"UPDATE articulo SET {set_clause} WHERE id = ?",
                    (*update_values.values(), id),
                )
                conn.commit()

                # Registra la actividad de modificación en el archivo CSV
                usuario_actual = session.get("usuario_actual")
                accion = f'Modificó un artículo (ID: {id}, Datos: {", ".join([f"{key}: {value}" for key, value in update_values.items()])})'
                registrar_actividad(usuario_actual, accion)
            else:
                alert_message = "No se realizaron cambios."

            conn.close()

            # Render a confirmation page with the alert message
            return render_template("confirmacioneditar.html", message=alert_message)
        else:
            error_message = "Artículo no encontrado."
            return render_template("confirmacioneditar.html", message=error_message)


@app.route("/editar")
def ver_datos_editar():
    datos = obtener_datos_de_articulo()
    if datos is not None:
        return render_template(
            "editar.html", articulos=datos
        )  # Asegúrate de usar 'articulos'
    else:
        return "Error al obtener datos de la base de datos."


@app.route("/eliminar_articulo", methods=["POST"])
def eliminar_articulo():
    if request.method == "POST":
        # Obtén el ID del artículo a eliminar desde el formulario
        id = request.form["id"]

        # Conecta con la base de datos y elimina el artículo
        conn = conectar_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articulo WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        # Registra la actividad de eliminación en el archivo CSV
        usuario_actual = session.get("usuario_actual")
        accion = f"Eliminó un artículo (ID: {id})"
        registrar_actividad(usuario_actual, accion)

        # No necesitas una redirección aquí, pero puedes redirigir a donde desees si es necesario
        return render_template("confirmacioneliminar.html", message="ID eliminada")


@app.route("/resultado_busqueda", methods=["POST"])
def resultado_busqueda():
    if request.method == "POST":
        # Obtén el código de barras ingresado por el usuario
        codigo_barras = request.form["codigo_barras"]

        # Realiza la búsqueda en la base de datos para obtener los datos del producto
        conn = sqlite3.connect(
            "BDD.db"
        )  # Asegúrate de usar el nombre correcto de tu base de datos
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulo WHERE id = ?", (codigo_barras,))
        producto = (
            cursor.fetchone()
        )  # Obtiene el producto con el código de barras especificado
        conn.close()

        if producto:
            # Si se encuentra el producto, muestra los detalles del producto en la misma página
            return render_template("editar.html", producto=producto)
        else:
            mensaje = "Producto no encontrado."
            # Si el producto no se encuentra, también puedes mostrar un mensaje en la misma página
            return render_template("editar.html", mensaje=mensaje)

    # Esta parte es para manejar la carga inicial de la página
    return render_template("editar.html")


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado Auditoria
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# Ruta para mostrar la página de auditoría de ventas
@app.route("/auditoria", methods=["GET", "POST"])
def auditoria_ventas():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio  auditoria"
    registrar_actividad(usuario_actual, accion)

    # Leer los datos del archivo de auditoría
    datos_auditoria = leer_datos_auditoria()

    # Filtrar los datos por fechas si se proporciona un rango de fechas en la solicitud del usuario
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    if fecha_inicio and fecha_fin:
        datos_auditoria_filtrados = filtrar_por_fechas(
            datos_auditoria, fecha_inicio, fecha_fin
        )
    else:
        datos_auditoria_filtrados = datos_auditoria

    return render_template(
        "auditoria.html",
        datos_auditoria=datos_auditoria_filtrados,
        username=session.get("usuario_actual"),
    )


# Función para leer los datos del archivo de auditoría (ventas.csv)
def leer_datos_auditoria():
    datos_auditoria = []

    with open("ventas.csv", newline="") as csvfile:
        reader = csv.reader(csvfile)
        # Salta la primera línea que contiene los encabezados de las columnas
        next(reader)
        for row in reader:
            datos_auditoria.append(row)

    return datos_auditoria


# Función para filtrar los datos de auditoría por fechas
def filtrar_por_fechas(datos_auditoria, fecha_inicio, fecha_fin):
    datos_filtrados = []

    # Convierte las fechas de inicio y fin a objetos datetime.date
    fecha_inicio = datetime.strptime(fecha_inicio.strip(), "%Y-%m-%d").date()
    fecha_fin = datetime.strptime(fecha_fin.strip(), "%Y-%m-%d").date()

    for row in datos_auditoria:
        if len(row) >= 6:
            fecha_registro = datetime.strptime(row[5].strip(), "%d-%m-%Y").date()
            if fecha_inicio <= fecha_registro <= fecha_fin:
                datos_filtrados.append(row)

    return datos_filtrados


# Auditoria Inicio de Sesion


def leer_registros_inicios_sesion():
    registros_inicios_sesion = []  # Inicializar con una lista vacía
    try:
        with open("iniciosesion.txt", "r") as file:
            for line in file:
                # Parsear cada línea del archivo para obtener usuario, fecha y hora
                parts = line.strip().split(", ")
                if len(parts) == 2:
                    usuario, fecha_hora = parts
                    registros_inicios_sesion.append(
                        {
                            "usuario": usuario.replace("Usuario: ", ""),
                            "fecha_hora": fecha_hora.replace(
                                "Fecha de inicio de sesión: ", ""
                            ),
                        }
                    )
    except FileNotFoundError:
        flash("El archivo iniciosesion.txt no se encontró.", "error")

    return registros_inicios_sesion


# Función para registrar actividad en el archivo CSV
def registrar_actividad(usuario, accion):
    # Genera una ID única basada en la fecha y hora actual
    registro_id = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # Obtiene la fecha y hora actual
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Abre el archivo CSV en modo de escritura (append) y escribe la información
    with open("registroauditoria_usuario.csv", mode="a", newline="") as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)
        escritor_csv.writerow([registro_id, usuario, accion, fecha_hora])


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado VENTAS
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# FOLIOS


# Función para obtener el rango de folios desde el archivo CSV
folios_utilizados = []


# Función para obtener el rango de folios desde el archivo CSV
def obtener_rango_folios():
    try:
        with open("folios.csv", mode="r") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            next(lector_csv)  # Salta la primera fila (etiquetas)
            for fila in lector_csv:
                folio_inicial = int(fila[0])
                folio_final = int(fila[1])
                return folio_inicial, folio_final
    except FileNotFoundError:
        return None, None


# Función para actualizar el rango de folios en el archivo CSV
def actualizar_rango_folios(folio_inicial_nuevo, folio_final_nuevo):
    try:
        with open("folios.csv", mode="w", newline="") as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(["folio_inicial", "folio_final"])
            escritor_csv.writerow([folio_inicial_nuevo, folio_final_nuevo])
    except Exception as e:
        print("Error al actualizar el rango de folios:", e)


# Función para agregar un folio utilizado al archivo 'folios_usados.csv'
def agregar_folio_utilizado(folio):
    try:
        with open("folios_usados.csv", mode="a", newline="") as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow([folio])
    except Exception as e:
        print("Error al agregar el folio utilizado:", e)


# Función para obtener el próximo folio disponible
def obtener_proximo_folio():
    global folios_utilizados  # Accedemos a la lista global de folios utilizados

    # Define el nombre del archivo CSV de folios
    archivo_folios = "folios.csv"

    # Lee el rango de folios desde el archivo
    with open(archivo_folios, mode="r") as file:
        reader = csv.reader(file)
        for row in reader:
            folio_inicial = int(row[0])
            folio_final = int(row[1])

    # Encuentra el próximo folio disponible
    for folio in range(folio_inicial, folio_final + 1):
        # Verifica si el folio ya se ha utilizado en ventas anteriores
        if folio not in folios_utilizados:
            # Agrega el folio a la lista de folios utilizados y al archivo 'folios_usados.csv'
            folios_utilizados.append(folio)
            agregar_folio_utilizado(folio)
            return str(folio).zfill(7)  # Formatea el folio con ceros a la izquierda

    # Si no se encuentra un folio disponible, puedes manejarlo según tus necesidades
    return "Folios agotados"


# Función para obtener el último folio utilizado desde folios_usados.csv
def obtener_ultimo_folio_utilizado():
    try:
        with open("folios_usados.csv", mode="r") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            for fila in lector_csv:
                ultimo_folio_utilizado = int(fila[0])
            return ultimo_folio_utilizado
    except FileNotFoundError:
        return (
            0  # Si no existe el archivo, asumimos que no se ha utilizado ningún folio
        )


# Función para actualizar el archivo folios.csv con el nuevo rango
def actualizar_folios_csv(ultimo_folio_utilizado):
    folio_final = 999  # Establece el valor final de tu rango
    nuevo_folio_inicio = min(ultimo_folio_utilizado + 1, folio_final)

    # Escribe el nuevo rango en folios.csv
    with open("folios.csv", mode="w", newline="") as archivo_csv:
        escritor_csv = csv.writer(archivo_csv)
        escritor_csv.writerow([nuevo_folio_inicio, folio_final])


# Ejemplo de uso después de completar una venta
ultimo_folio_utilizado = obtener_ultimo_folio_utilizado()
actualizar_folios_csv(ultimo_folio_utilizado)

# Ahora, folios.csv se actualizará con el nuevo rango, como 7,999 (si el último folio utilizado fue 6)

id_venta = 1


# Ruta para mostrar la página de ventas
@app.route("/ventas", methods=["GET"])
def pagina_de_ventas():
    # Calcula el total de la venta justo antes de mostrar la página
    total_precio = calcular_total_precio()

    # Obtén los detalles de los productos en la lista temporal
    detalles_productos = []

    for item in lista_temporal_venta:
        id_producto, nombre_producto, cantidad_venta = item  # Desempaqueta la tupla
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, precio FROM articulo WHERE id = ?", (id_producto,))
        producto = cursor.fetchone()
        conn.close()

        if producto:
            id_producto, precio_producto = producto
            subtotal = precio_producto * cantidad_venta
            detalles_productos.append(
                {
                    "id_producto": id_producto,
                    "nombre_producto": nombre_producto,
                    "cantidad_venta": cantidad_venta,
                    "precio_producto": precio_producto,
                    "subtotal": subtotal,
                }
            )

    return render_template(
        "ventas.html", total_precio=total_precio, detalles_productos=detalles_productos
    )


# Lista temporal de venta (inicialmente vacía)
lista_temporal_venta = []
print(len(lista_temporal_venta))  # Verifica la longitud de la lista
print(lista_temporal_venta)  # Verifica los elementos en la lista


# Ruta para agregar un artículo a la lista temporal de venta
@app.route("/agregar_venta", methods=["POST"])
def agregar_venta():
    if request.method == "POST":
        id_producto = request.form["id_producto"]
        cantidad_venta = int(request.form["cantidad_venta"])

        # Realiza la búsqueda en la base de datos para obtener el artículo por su ID
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, cantidad FROM articulo WHERE id = ?", (id_producto,)
        )
        articulo = cursor.fetchone()

        if articulo:
            # Verifica si la cantidad solicitada está disponible
            if cantidad_venta <= articulo[2]:
                # Agrega el artículo a la lista temporal de venta
                lista_temporal_venta.append((articulo[0], articulo[1], cantidad_venta))
                flash(
                    f"Se ha agregado {cantidad_venta} unidades de {articulo[1]} a la lista de venta.",
                    "success",
                )
            else:
                flash(
                    f"La cantidad solicitada de {articulo[1]} no está disponible.",
                    "error",
                )
        else:
            flash(
                f"El artículo con ID {id_producto} no fue encontrado en la base de datos.",
                "error",
            )

        conn.close()

        # Redirige nuevamente a la página de ventas
        return redirect(url_for("pagina_de_ventas"))


# Ruta para calcular total
def calcular_total_precio():
    total = 0
    for item in lista_temporal_venta:
        id_producto, _, cantidad_venta = item  # Desempaqueta la tupla
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()
        cursor.execute("SELECT precio FROM articulo WHERE id = ?", (id_producto,))
        precio_producto = cursor.fetchone()[0]
        conn.close()
        subtotal = precio_producto * cantidad_venta
        total += subtotal
    return total


# Función para guardar registros de ventas en un archivo de auditoría
def guardar_registro_de_venta(
    id_venta, tipo_venta, rut_cliente, nombre_producto, total_venta, fecha_venta, folio
):
    try:
        # Define el nombre del archivo CSV
        archivo_csv = "ventas.csv"

        # Abre el archivo CSV en modo de escritura (append)
        with open(archivo_csv, mode="a", newline="") as archivo:
            # Crea un escritor CSV
            escritor_csv = csv.writer(archivo)

            # Escribe una nueva fila con los datos de la venta
            escritor_csv.writerow(
                [
                    id_venta,
                    tipo_venta,
                    rut_cliente,
                    nombre_producto,
                    total_venta,
                    fecha_venta,
                    folio,
                ]
            )

    except Exception as e:
        print("Error al guardar el registro de venta:", e)


# Obtener datos empresa


def obtener_datos_empresa():
    datos_empresa = {
        "Nombre": "",
        "RUT": "",
        "Dirección": "",
        "Número de Contacto": "",
        "Correo Electrónico": "",
        "Logo": "",
        "Giro": "",
    }
    try:
        with open("empresa.csv", mode="r", encoding="iso-8859-1") as archivo_csv:
            lector_csv = csv.DictReader(archivo_csv)
            for row in lector_csv:
                datos_empresa = {
                    "Nombre": row["Nombre"],
                    "RUT": row["RUT"],
                    "Dirección": row["Dirección"],
                    "Número de Contacto": row["Número de Contacto"],
                    "Correo Electrónico": row["Correo Electrónico"],
                    "Logo": row["Logo"],
                    "Giro": row["Giro"],
                }
    except FileNotFoundError:
        print("El archivo 'empresa.csv' no fue encontrado.")
    except Exception as e:
        print(f"Error al leer 'empresa.csv': {str(e)}")
    return datos_empresa


# Ruta para completar la venta
# Variable global para llevar un registro de la ID de la venta


# Ruta para completar la venta
@app.route("/completar_venta", methods=["POST"])
def completar_venta():
    if request.method == "POST":
        # Obtén el folio ingresado por el usuario desde el formulario
        folio = obtener_proximo_folio()

        total_venta = calcular_total_precio()  # Calcula el total de la venta
        global id_venta
        # Realiza las acciones necesarias para completar la venta en la base de datos
        # Obtén los valores ingresados por el usuario
        tipo_venta = request.form["tipo_venta"]
        rut_cliente = request.form.get(
            "rut_cliente"
        )  # Obtén el RUT del cliente (opcional)
        # Obtiene la fecha ingresada por el usuario desde el formulario
        fecha_venta = request.form["fecha_venta"]

        # Conecta con la base de datos
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()

        # Inicializa la suma total de precios en cero
        total_precio = 0

        # Después de procesar la venta, incrementa la ID de la venta
        usuario_id = 1  # Reemplaza con el ID del usuario que realiza la venta
        fecha = datetime.now().date()
        comentario = "Venta realizada"

        # Obtiene la fecha ingresada por el usuario desde el formulario
        fecha_venta = request.form["fecha_venta"]

        # Convierte la fecha al formato "dd-mm-yyyy"
        fecha_venta = datetime.strptime(fecha_venta, "%Y-%m-%d").strftime("%d-%m-%Y")

        # Calcula el total de la venta antes de procesar los productos
        total_precio = calcular_total_precio()  # Mover esta línea aquí

        # Lista para almacenar los detalles de la venta
        detalles_venta = []

        # Itera a través de los productos en la lista temporal de venta
        for item in lista_temporal_venta:
            id_producto, nombre_producto, cantidad_venta = item  # Desempaqueta la tupla

            # Obtiene el precio del producto desde la base de datos
            cursor.execute("SELECT precio FROM articulo WHERE id = ?", (id_producto,))
            row = cursor.fetchone()
            if row is not None:
                precio_producto = row[0]
            else:
                precio_producto = 0  # Puedes proporcionar un valor predeterminado en caso de que no se encuentre el precio

            # Calcula el subtotal para este producto y agrégalo al total_precio
            subtotal = precio_producto * cantidad_venta
            total_precio += subtotal

            # Registra la venta para este producto
            cursor.execute(
                "INSERT INTO venta (usuario_id, fecha, cantidad, comentario) VALUES (?, ?, ?, ?)",
                (usuario_id, fecha, cantidad_venta, comentario),
            )

            # Llama a la función 'guardar_registro_de_venta' con los datos de la venta
            # Llama a la función 'guardar_registro_de_venta' con los datos de la venta, excluyendo num_boleta
            guardar_registro_de_venta(
                id_venta,
                tipo_venta,
                rut_cliente,
                nombre_producto,
                total_venta,
                fecha_venta,
                folio,
            )

            # Actualiza la cantidad disponible del producto en la base de datos
            cursor.execute(
                "UPDATE articulo SET cantidad = cantidad - ? WHERE id = ?",
                (cantidad_venta, id_producto),
            )

            # Agrega los detalles de la venta a la lista
            detalles_venta.append(
                {
                    "nombre_producto": nombre_producto,
                    "cantidad_venta": cantidad_venta,
                    "precio_producto": precio_producto,
                    "subtotal": subtotal,
                }
            )

            # Obtén los datos de la empresa
            datos_empresa = obtener_datos_empresa()
        # Crear un diccionario con los datos de la venta y la empresa
        datos_venta = {
            "id_venta": id_venta,
            "tipo_venta": tipo_venta,
            "rut_cliente": rut_cliente,
            "nombre_producto": nombre_producto,
            "total_venta": total_venta,
            "fecha_venta": request.form["fecha_venta"],
            "folio": folio,
            "Nombre": datos_empresa["Nombre"],
            "RUT": datos_empresa["RUT"],
            "Dirección": datos_empresa["Dirección"],
            "Número de Contacto": datos_empresa["Número de Contacto"],
            "Correo Electrónico": datos_empresa["Correo Electrónico"],
            "Logo": datos_empresa["Logo"],
            "Giro": datos_empresa["Giro"],
        }
        # Guardar los datos de la venta y la empresa en el archivo registro_ventas.csv
        with open("registro_ventas.csv", mode="a", newline="") as archivo_csv:
            campos = [
                "id_venta",
                "tipo_venta",
                "rut_cliente",
                "nombre_producto",
                "total_venta",
                "fecha_venta",
                "folio",
                "Nombre",
                "RUT",
                "Dirección",
                "Número de Contacto",
                "Correo Electrónico",
                "Logo",
                "Giro",
            ]
            escritor_csv = csv.DictWriter(archivo_csv, fieldnames=campos)

            # Verificar si el archivo está vacío y escribir encabezados si es necesario
            if archivo_csv.tell() == 0:
                escritor_csv.writeheader()

            escritor_csv.writerow(datos_venta)

        # Llama a la función para generar el comprobante
        generar_comprobante(datos_venta, ruta_boletas)
        # Limpia la lista temporal de venta
        lista_temporal_venta.clear()

        # Confirma y cierra la conexión con la base de datos
        conn.commit()
        conn.close()

        flash(f"La venta se ha completado con éxito. Total: {total_precio}", "success")

        # Renderiza la página de ventas con los detalles de la venta
        return render_template(
            "ventas.html",
            total_precio=total_precio,
            detalles_productos=detalles_venta,
            folio=folio,
        )


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado de Informes
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


@app.route("/informes", methods=["GET"])
def informes():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Informes"
    registrar_actividad(usuario_actual, accion)

    # Leer los datos de ventas desde el archivo CSV
    ventas_por_articulo = {}
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            if len(fila) >= 4:  # Asegurarse de que la fila tenga al menos 4 elementos
                _, _, _, nombre_producto, total_venta, *_ = fila
                total_venta = float(total_venta)  # Convertir a tipo float
                if nombre_producto in ventas_por_articulo:
                    ventas_por_articulo[nombre_producto] += total_venta
                else:
                    ventas_por_articulo[nombre_producto] = total_venta

    # Preparar datos para el gráfico de torta
    articulos = list(ventas_por_articulo.keys())
    ventas = list(ventas_por_articulo.values())

    # Crear el gráfico de torta
    plt.figure(figsize=(8, 8))
    plt.pie(ventas, labels=articulos, autopct="%1.1f%%", startangle=140)

    # Agregar título
    plt.title("Porcentaje de Ventas Globales por Artículo")

    # Mostrar el gráfico
    plt.axis("equal")

    # Guardar el gráfico en un archivo o mostrarlo en la página web
    plt.savefig("static/ventas_globales.png")  # Guardar el gráfico en un archivo
    # plt.show()  # Mostrar el gráfico en la página web (descomentar esta línea si lo prefieres)

    # Leer los datos del archivo CSV y calcular las ventas por producto
    ventas_por_producto = {}
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            if len(fila) >= 7:  # Asegurarse de que la fila tenga al menos 7 elementos
                (
                    id_venta,
                    tipo_venta,
                    rut_cliente,
                    nombre_producto,
                    total_venta,
                    fecha_venta,
                    folio,
                ) = fila
                if nombre_producto in ventas_por_producto:
                    ventas_por_producto[nombre_producto] += int(total_venta)
                else:
                    ventas_por_producto[nombre_producto] = int(total_venta)

    ventas_por_tipo = leer_datos_ventas()
    tablas_html = generar_tablas_html(ventas_por_tipo)

    # Obtener nombres de productos y ventas como listas separadas
    productos = list(ventas_por_producto.keys())
    ventas = list(ventas_por_producto.values())

    # Crea el gráfico de barras
    plt.figure(figsize=(11, 8))
    plt.bar(productos, ventas)
    plt.xlabel("Nombre del Producto")
    plt.ylabel("Ventas")
    plt.title("Ventas por Producto")

    # Rotar etiquetas del eje x para mejorar la legibilidad
    plt.xticks(rotation=16, ha="right")

    # Guarda el gráfico en un archivo temporal
    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    # Codifica la imagen en base64
    img_base64 = base64.b64encode(img.read()).decode()

    # Cierra la figura de matplotlib
    plt.close()

    # Renderiza la página de informes con la imagen del gráfico
    return render_template(
        "informes.html",
        img_path="ventas_globales.png",
        tablas=tablas_html,
        img_base64=img_base64,
        username=session.get("usuario_actual"),
    )


# Conectar a la base de datos SQLite
conn = sqlite3.connect(
    "BDD.db"
)  # Asegúrate de usar el nombre correcto de tu base de datos
cursor = conn.cursor()

# Consulta SQL para obtener todos los artículos de la tabla 'articulo'
cursor.execute("SELECT id, nombre, cantidad, precio, ubicacion FROM articulo")
articulos = cursor.fetchall()

# Cerrar la conexión a la base de datos
conn.close()

# Crear un archivo PDF
pdf_filename = "lista_de_articulos.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

# Crear una lista de artículos en formato de tabla
data = [["ID", "Nombre", "Cantidad", "Precio", "Ubicación"]]
data.extend(articulos)

# Crear la tabla y establecer el estilo
table = Table(data)
style = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), (0.8, 0.8, 0.8)),  # Fila de encabezados
        ("TEXTCOLOR", (0, 0), (-1, 0), (0, 0, 0)),  # Color de texto de encabezados
        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER",
        ),  # Alineación centrada para todas las celdas
        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold",
        ),  # Fuente en negrita para los encabezados
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),  # Espacio inferior para los encabezados
        (
            "BACKGROUND",
            (0, 1),
            (-1, -1),
            (0.9, 0.9, 0.9),
        ),  # Color de fondo para las filas de datos
        ("GRID", (0, 0), (-1, -1), 1, (0, 0, 0)),  # Líneas de cuadrícula
    ]
)
table.setStyle(style)

# Crear la lista de elementos a ser incluidos en el PDF
elements = []

# Agregar un título al PDF
styles = getSampleStyleSheet()
title = Paragraph("<b>Lista de Artículos</b>", styles["Title"])
elements.append(title)

# Agregar la tabla al PDF
elements.append(table)

# Generar el PDF y guardarlo
doc.build(elements)

print(f"PDF generado: {pdf_filename}")


# Ruta para mostrar el PDF en la página de informes
@app.route("/ver_pdf", methods=["GET"])
def ver_pdf():
    # Aquí, debes proporcionar el camino completo hacia tu archivo PDF generado
    pdf_path = "lista_de_articulos.pdf"
    return send_file(pdf_path, as_attachment=False)


# Leer datos de CSV ventas
def leer_datos_ventas():
    ventas_por_tipo = {}
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            if len(fila) >= 7:  # Asegurarse de que la fila tenga al menos 7 elementos
                (
                    id_venta,
                    tipo_venta,
                    rut_cliente,
                    nombre_producto,
                    total_venta,
                    fecha_venta,
                    folio,
                ) = fila
                if tipo_venta in ventas_por_tipo:
                    ventas_por_tipo[tipo_venta].append(fila)
                else:
                    ventas_por_tipo[tipo_venta] = [fila]
    return ventas_por_tipo


# Crear una función para generar tablas HTML
def generar_tablas_html(ventas_por_tipo):
    tablas_html = []
    for tipo_venta, ventas in ventas_por_tipo.items():
        # Crear una tabla HTML para cada tipo de venta
        tabla_html = f"<h2>Tabla de {tipo_venta}</h2>"
        tabla_html += '<div class="tabla-container">'
        tabla_html += '<div class="tabla-scroll">'
        tabla_html += "<table><tr><th>ID Venta</th><th>RUT Cliente</th><th>Nombre Producto</th><th>Total Venta</th><th>Fecha Venta</th><th>Folio</th></tr>"
        suma_total = 0  # Inicializar la suma del monto total
        for venta in ventas:
            (
                id_venta,
                tipo_venta,
                rut_cliente,
                nombre_producto,
                total_venta,
                fecha_venta,
                folio,
            ) = venta
            suma_total += int(total_venta)  # Sumar el monto total
            tabla_html += f"<tr><td>{id_venta}</td><td>{rut_cliente}</td><td>{nombre_producto}</td><td>{total_venta}</td><td>{fecha_venta}</td><td>{folio}</td></tr>"
        tabla_html += "</table>"
        tabla_html += "</div>"  # Cierre del div con desplazamiento vertical
        tabla_html += "</div>"  # Cierre del contenedor de la tabla

        # Agregar el total dentro de un recuadro
        tabla_html += (
            f'<div class="total-recuadro">Recaudación Total: {suma_total}</div>'
        )

        tablas_html.append(tabla_html)
    return tablas_html


def generar_informe_pdf():
    # Leer los datos de ventas desde el archivo CSV y procesarlos
    datos_ventas = []
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            datos_ventas.append(fila)  # Agrega fila de datos

    # Crear un archivo PDF
    pdf_filename = "informe_ventas.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

    # Crear una lista de ventas en formato de tabla
    data = [
        [
            "ID Venta",
            "Tipo Venta",
            "RUT Cliente",
            "Nombre Producto",
            "Total Venta",
            "Fecha Venta",
            "Folio",
        ]
    ]
    data.extend(datos_ventas)

    # Crear la tabla y establecer el estilo
    table = Table(data)
    style = TableStyle(
        [
            # Estilos de tabla, encabezados, etc.
        ]
    )
    table.setStyle(style)

    # Crear la lista de elementos a ser incluidos en el PDF
    elements = []

    # Agregar un título al PDF
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Informe de Ventas</b>", styles["Title"])
    elements.append(title)

    # Agregar la tabla al PDF
    elements.append(table)

    # Generar el PDF y guardarlo
    doc.build(elements)

    return pdf_filename


@app.route("/descargar_informe", methods=["GET"])
def descargar_informe():
    pdf_filename = generar_informe_pdf()
    return send_file(pdf_filename, as_attachment=True)


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado de Index
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# Función para obtener la cantidad de ventas desde 'ventas.csv'
def obtener_cantidad_de_ventas():
    try:
        with open("ventas.csv", mode="r", newline="") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            cantidad_ventas = (
                len(list(lector_csv)) - 1
            )  # Resta 1 para excluir el encabezado
        return cantidad_ventas
    except FileNotFoundError:
        return 0


# Función para obtener la cantidad de usuarios desde 'users.txt'
def obtener_cantidad_de_usuarios():
    try:
        with open("users.txt", "r") as archivo_users:
            cantidad_usuarios = sum(1 for linea in archivo_users)
        return cantidad_usuarios
    except FileNotFoundError:
        return 0


def obtener_cantidad_de_articulos():
    try:
        # Conecta a la base de datos SQLite (reemplaza 'tu_basededatos.db' con el nombre de tu base de datos)
        conexion = sqlite3.connect("BDD.db")
        cursor = conexion.cursor()

        # Consulta para contar la cantidad de artículos en la tabla 'articulo' (ajusta el nombre de la tabla según corresponda)
        cursor.execute("SELECT COUNT(*) FROM articulo")
        cantidad_articulos = cursor.fetchone()[0]

        # Cierra la conexión a la base de datos
        conexion.close()

        return cantidad_articulos
    except sqlite3.Error as error:
        print(
            "Error al obtener la cantidad de artículos desde la base de datos:", error
        )
        return 0  # Devuelve 0 en caso de error


def obtener_ultimas_ventas():
    try:
        with open("ventas.csv", mode="r", newline="") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            # Convierte el lector CSV en una lista y toma las últimas 3 filas
            ultimas_ventas = list(lector_csv)[-3:]
        return ultimas_ventas
    except FileNotFoundError:
        return []


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado Opciones Usuario
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------------------------------------------------
# DATOS DE EMPRESA
# --------------------------------------------------------------------------------------------------------------------------------


@app.route("/informacion_empresa", methods=["GET"])
@admin_required
def mostrar_informacion_empresa():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio información empresa"
    registrar_actividad(usuario_actual, accion)

    # Leer la información de la empresa desde el archivo empresa.csv (si existe)
    informacion_empresa = {}
    if os.path.isfile("empresa.csv"):
        with open("empresa.csv", mode="r", newline="") as archivo_csv:
            lector_csv = csv.DictReader(archivo_csv)
            for row in lector_csv:
                informacion_empresa = row

    return render_template(
        "informacion_empresa.html",
        informacion_empresa=informacion_empresa,
        username=session.get("usuario_actual"),
    )


@app.route("/modificar_informacion_empresa", methods=["POST"])
def modificar_informacion_empresa():
    if request.method == "POST":
        # Obtener los datos del formulario
        nombre = request.form["nombre"]
        rut = request.form["rut"]
        direccion = request.form["direccion"]
        contacto = request.form["contacto"]
        correo = request.form["correo"]
        giro = request.form["giro"]  # Obtener el campo "giro"

        # Obtener el nombre de la imagen anterior desde el formulario
        nombre_imagen_anterior = request.form.get("nombre_imagen_anterior")

        # Guardar el logo de la empresa en la carpeta "static"
        if "logo" in request.files:
            logo = request.files["logo"]
            if logo.filename != "":
                logo.save(os.path.join("static", logo.filename))

                # Eliminar la imagen anterior si existe
                if nombre_imagen_anterior:
                    imagen_anterior_path = os.path.join(
                        "static", nombre_imagen_anterior
                    )
                    if os.path.exists(imagen_anterior_path):
                        os.remove(imagen_anterior_path)

        # Crear un diccionario con la información de la empresa
        informacion_empresa = {
            "Nombre": nombre,
            "RUT": rut,
            "Dirección": direccion,
            "Número de Contacto": contacto,
            "Correo Electrónico": correo,
            "Giro": giro,  # Agregar el campo "giro"
            "Logo": logo.filename,  # Nombre del archivo del logo
        }

        # Guardar la información de la empresa en el archivo empresa.csv
        with open("empresa.csv", mode="w", newline="") as archivo_csv:
            campos = [
                "Nombre",
                "RUT",
                "Dirección",
                "Número de Contacto",
                "Correo Electrónico",
                "Logo",
                "Giro",
            ]
            escritor_csv = csv.DictWriter(archivo_csv, fieldnames=campos)
            escritor_csv.writeheader()
            escritor_csv.writerow(informacion_empresa)

        flash("Información de la empresa actualizada con éxito.", "success")

    return redirect(url_for("mostrar_informacion_empresa"))


# --------------------------------------------------------------------------------------------------------------------------------
# MODIFICACION DE FOLIOS
# --------------------------------------------------------------------------------------------------------------------------------


# Ruta para procesar los cambios en el archivo folios.csv
@app.route("/modificar_folios", methods=["POST"])
def modificar_folios():
    if request.method == "POST":
        # Obtén los nuevos valores de folio_inicial y folio_final desde el formulario
        folio_inicial_nuevo = request.form["folio_inicial"]
        folio_final_nuevo = request.form["folio_final"]

        # Realiza la modificación en el archivo folios.csv
        with open("folios.csv", mode="w", newline="") as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow([folio_inicial_nuevo, folio_final_nuevo])

        flash("Folios modificados con éxito.", "success")
        return redirect(url_for("mostrar_formulario_modificar_folios"))


def obtener_datos_folios():
    datos_folios = []

    try:
        with open("folios.csv", mode="r") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            for fila in lector_csv:
                datos_folios.append(fila)
    except FileNotFoundError:
        # Si el archivo no se encuentra, puedes manejar este caso de acuerdo a tus necesidades
        pass

    return datos_folios


@app.route("/mostrar_folios", methods=["GET"])
def mostrar_folios():
    # Obtén los datos de folios utilizando la función obtener_datos_folios()
    datos_folios = obtener_datos_folios()

    # Obtiene el folio actual desde el primer elemento de datos_folios
    folio_actual = datos_folios[0][0]

    # Guarda el folio actual en un archivo de texto (folio_actual.txt)
    with open("folio_actual.txt", "w") as archivo_txt:
        archivo_txt.write(folio_actual)

    return render_template("mostrar_folios.html", datos_folios=datos_folios)


# --------------------------------------------------------------------------------------------------------------------------------
# CREAR USUARIOS
# --------------------------------------------------------------------------------------------------------------------------------


@app.route("/registro_usuario", methods=["POST"])
def registro_usuario():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form[
            "role"
        ]  # Acceder al valor seleccionado del campo de selección

        try:
            # Abre el archivo users.txt en modo de escritura y agrega el nuevo usuario con su rol
            with open("users.txt", "a") as archivo_users:
                archivo_users.write(
                    f"{username}:{password}:{role}\n"
                )  # Separar los campos con ":" o el delimitador de tu elección

            flash(f'Se ha registrado el usuario "{username}" con éxito.', "success")

        except Exception as e:
            flash(f"Error al registrar el usuario: {str(e)}", "error")

    return redirect(url_for("mostrar_formulario_registro_usuario"))


# --------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado Documentos Generados
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# Generar Boleta para Ventas
# Define la ruta de la carpeta de boletas
ruta_boletas = "boletas"


# Función para generar un comprobante de venta en formato PDF
def generar_comprobante(datos_venta, ruta_boletas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Dibuja un rectángulo para resaltar ciertos datos
    pdf.set_fill_color(200, 200, 200)  # Color de relleno (gris claro)
    #    pdf.cell(200, 10, txt="Datos Empresa", ln=True, align='C')

    pdf.cell(
        200,
        10,
        txt="--------------------------------------------------------------------------------------------------------------------------------------",
        ln=True,
    )  # Línea en blanco
    pdf.cell(200, 10, txt=f"R.U.T: {datos_venta['RUT']}", ln=True, align="C")
    pdf.cell(
        200,
        10,
        txt=f"Número de Contacto: {datos_venta['Número de Contacto']}",
        ln=True,
        align="C",
    )
    pdf.cell(200, 10, txt=f"N*: {datos_venta['folio']}", ln=True, align="C")
    pdf.cell(
        200,
        10,
        txt="--------------------------------------------------------------------------------------------------------------------------------------",
        ln=True,
    )  # Línea en blanco

    pdf.cell(
        200,
        10,
        txt="--------------------------------------------------------------------------------------------------------------------------------------",
        ln=True,
    )  # Línea en blanco
    pdf.cell(200, 10, txt=datos_venta["Nombre"], ln=True)
    pdf.cell(200, 10, txt=f"Giro: {datos_venta['Giro']}", ln=True)
    pdf.cell(200, 10, txt=f"Dirección: {datos_venta['Dirección']}", ln=True)
    pdf.cell(
        200, 10, txt=f"Número de Contacto: {datos_venta['Número de Contacto']}", ln=True
    )
    pdf.cell(
        200,
        10,
        txt="--------------------------------------------------------------------------------------------------------------------------------------",
        ln=True,
    )  # Línea en blanco
    pdf.cell(200, 10, txt=f"Fecha Venta: {datos_venta['fecha_venta']}", ln=True)
    pdf.cell(200, 10, txt=f"Tipo de Venta: {datos_venta['tipo_venta']}", ln=True)

    pdf.cell(
        200,
        10,
        txt="________________________________________________________________________________",
        ln=True,
    )  # Línea en blanco
    pdf.cell(200, 10, txt=f"Nombre Producto: {datos_venta['nombre_producto']}", ln=True)
    pdf.cell(200, 10, txt=f"Total Venta: {datos_venta['total_venta']}", ln=True)

    # Guarda el comprobante en la carpeta de boletas
    nombre_pdf = f'{ruta_boletas}/comprobante_venta_{datos_venta["folio"]}.pdf'
    pdf.output(nombre_pdf)

    # Ejemplo de uso


# datos_ejemplo_venta = {
#     'id_venta': '1',
#     'tipo_venta': 'Venta Online',
#     'rut_cliente': '12345678-9',
#     'nombre_producto': 'Producto Ejemplo',
#     'total_venta': '100.00',
#     'fecha_venta': '2023-09-25',
#     'folio': 'FOLIO123',
#     'Nombre': 'Nombre Empresa',
#     'RUT': '12345678-0',
#     'Dirección': 'Dirección Empresa',
#     'Número de Contacto': '123456789',
#     'Correo Electrónico': 'correo@empresa.com',
#     'Logo': 'logo.png',
#     'Giro': 'Giro de la Empresa'
# }

# generar_comprobante(datos_ejemplo_venta, 'boletas')


def obtener_lista_archivos_pdf(directorio):
    archivos_pdf = []
    # Recorre todos los archivos en el directorio especificado
    for nombre_archivo in os.listdir(directorio):
        # Verifica si el archivo tiene una extensión PDF
        if nombre_archivo.lower().endswith(".pdf"):
            archivos_pdf.append(nombre_archivo)
    return archivos_pdf


directorio_pdf = "boletas"
archivos_pdf = obtener_lista_archivos_pdf(directorio_pdf)
print(archivos_pdf)  # Esto imprimirá la lista de archivos PDF en el directorio


# Ruta para mostrar la lista de archivos PDF y descargarlos
@app.route("/archivos_pdf")
def mostrar_archivos_pdf():
    directorio_pdf = "boletas"  # Define el directorio en el que buscar los archivos PDF
    archivos_pdf = obtener_lista_archivos_pdf(
        directorio_pdf
    )  # Pasa el directorio como argumento
    return render_template("lista_pdf.html", archivos_pdf=archivos_pdf)


@app.route("/archivos_pdf/<nombre_archivo>")
def descargar_archivo_pdf(nombre_archivo):
    directorio_pdf = "boletas"  # Usar el directorio correcto
    return send_from_directory(directorio_pdf, nombre_archivo)


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
# Apartado de cotizacion
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
@app.route("/static/cotizaciones/<path:filename>")
def cotizaciones(filename):
    return send_from_directory(os.path.join(app.root_path, "cotizaciones"), filename)


# Lista temporal de cotización (inicialmente vacía)
lista_temporal_cotizacion = []

# Contador de ID para las cotizaciones (inicializado en 1)
cotizacion_id = 1  # Definir el contador de ID como una variable global


@app.route("/cotizar", methods=["GET", "POST"])
def cotizar():
    global cotizacion_id  # Declarar que se utilizará la variable global cotizacion_id
    carpeta_cotizaciones = "cotizaciones"
    archivos_pdf = [
        archivo
        for archivo in os.listdir(carpeta_cotizaciones)
        if archivo.endswith(".pdf")
    ]

    if request.method == "POST":
        id_producto = request.form["id_producto"]
        cantidad_cotizada = int(request.form["cantidad_cotizada"])

        if request.method == "POST":
            id_producto = request.form["id_producto"]
            cantidad_cotizada = int(request.form["cantidad_cotizada"])

        # Realiza una consulta a la base de datos para obtener el producto por su ID
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, precio, cantidad FROM articulo WHERE id = ?",
            (id_producto,),
        )
        producto = cursor.fetchone()

        if producto:
            id_producto, nombre_producto, precio_producto, cantidad = producto

            # Verifica si la cantidad cotizada no excede la cantidad disponible
            if cantidad_cotizada <= cantidad:
                # Crea un objeto de cotización con ID autoincrementable
                cotizacion = {
                    "id": cotizacion_id,
                    "id_producto": id_producto,
                    "nombre_producto": nombre_producto,
                    "precio_producto": precio_producto,
                    "cantidad_cotizada": cantidad_cotizada,
                }

                # Incrementa el contador de ID para la próxima cotización
                cotizacion_id += 1

                # Agrega la cotización a la lista temporal de cotizaciones
                lista_temporal_cotizacion.append(cotizacion)

                flash(
                    f"Se ha agregado {cantidad_cotizada} unidades de {nombre_producto} a la cotización.",
                    "success",
                )
            else:
                flash(
                    f"La cantidad solicitada de {nombre_producto} no está disponible.",
                    "error",
                )
        else:
            flash(
                f"El producto con ID {id_producto} no fue encontrado en la base de datos.",
                "error",
            )

        conn.close()

    # Consulta la lista de productos disponibles en la base de datos
    conn = sqlite3.connect("BDD.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, precio, cantidad FROM articulo")
    productos_disponibles = cursor.fetchall()
    conn.close()

    return render_template(
        "cotizar.html",
        productos_disponibles=productos_disponibles,
        lista_temporal_cotizacion=lista_temporal_cotizacion,
        archivos_pdf=archivos_pdf,
    )


@app.route("/ingresar_datos", methods=["GET", "POST"])
def ingresar_datos():
    if request.method == "POST":
        fecha_cotizacion = request.form["fecha_cotizacion"]
        nombre_cliente = request.form["nombre_cliente"]
        rut_cliente = request.form["rut_cliente"]
        observaciones = request.form["observaciones"]
        # Verifica si se proporcionó un valor para el descuento
        descuento = request.form["descuento"]
        if descuento:
            descuento = float(descuento)
        else:
            descuento = 0.0

        # Crear una lista para almacenar los datos de la cotización
        datos_cotizacion = [
            cotizacion_id,
            fecha_cotizacion,
            nombre_cliente,
            rut_cliente,
            observaciones,
            descuento,
        ]

        # Crear una lista para almacenar los datos de la cotización
        datos_cotizacion = [
            cotizacion_id,
            fecha_cotizacion,
            nombre_cliente,
            rut_cliente,
            observaciones,
            descuento,
        ]

        # Combinar los productos cotizados en una sola cadena
        productos_cotizados = []
        precio_total_cotizacion = (
            0  # Variable para calcular el precio total de la cotización
        )

        for cotizacion in lista_temporal_cotizacion:
            cantidad_cotizada = cotizacion["cantidad_cotizada"]
            precio_unitario = cotizacion["precio_producto"]

            # Calcular el precio total para este artículo
            precio_total_articulo = cantidad_cotizada * precio_unitario
            precio_total_cotizacion += precio_total_articulo

            # Crear la descripción del artículo en la cotización
            producto_cotizado = f"{cotizacion['nombre_producto']} ({cantidad_cotizada} unidades) - Precio Unitario: {precio_unitario} CLP - Precio Total: {precio_total_articulo} CLP"
            productos_cotizados.append(producto_cotizado)

        # Calcular el precio total sin descuento
        precio_total_sin_descuento = precio_total_cotizacion

        # Calcular el descuento aplicado
        descuento_aplicado = precio_total_sin_descuento * (descuento / 100)

        # Calcular el precio con descuento restando el descuento al precio total sin descuento
        precio_con_descuento = precio_total_sin_descuento - descuento_aplicado

        # Agregar el precio con descuento a la lista de datos de la cotización
        datos_cotizacion.append(precio_con_descuento)

        # Agregar los productos cotizados como una sola cadena
        datos_cotizacion.append(", ".join(productos_cotizados))

        # Abre el archivo CSV en modo de escritura
        with open("cotizacion.csv", mode="a", newline="") as file:
            # Crea un objeto escritor CSV
            writer = csv.writer(file)

            # Escribe la fila de encabezado si es necesario
            if file.tell() == 0:
                writer.writerow(
                    [
                        "ID",
                        "Fecha Cotización",
                        "Nombre Cliente",
                        "RUT Cliente",
                        "Observaciones",
                        "Descuento",
                        "Precio Total",
                        "Productos Cotizados",
                    ]
                )

            # Escribe los datos de la cotización en una sola línea
            writer.writerow(datos_cotizacion)

        # Limpia la lista temporal de cotización
        lista_temporal_cotizacion.clear()

        # Llama a la función para generar el PDF
        generar_pdf_cotizacion(
            cotizacion_id,
            fecha_cotizacion,
            nombre_cliente,
            rut_cliente,
            observaciones,
            descuento,
            productos_cotizados,
        )

        flash("Cotización guardada exitosamente.", "success")

    return redirect("/cotizar")


@app.route("/guardar_cotizacion", methods=["POST"])
def guardar_cotizacion():
    # Obtén los datos del formulario
    fecha_cotizacion = request.form["fecha_cotizacion"]
    nombre_cliente = request.form["nombre_cliente"]
    rut_cliente = request.form["rut_cliente"]
    observaciones = request.form["observaciones"]
    descuento = float(request.form["descuento"]) if "descuento" in request.form else 0.0

    # Abre el archivo CSV en modo de escritura
    with open("cotizacion.csv", mode="w", newline="") as file:
        # Crea un objeto escritor CSV
        writer = csv.writer(file)

        # Escribe la fila de encabezado si es necesario
        if not file.readline():
            writer.writerow(
                [
                    "ID",
                    "Fecha Cotización",
                    "Nombre Cliente",
                    "RUT Cliente",
                    "Observaciones",
                    "Descuento",
                    "Productos Cotizados",
                    "Precio Total",
                ]
            )

        # Escribe los datos de la cotización en una sola línea
        for i, item in enumerate(lista_temporal_cotizacion, start=1):
            # Calcula el precio total para cada artículo
            precio_total = item["cantidad_cotizada"] * item["precio_producto"]
            writer.writerow(
                [
                    i,
                    fecha_cotizacion,
                    nombre_cliente,
                    rut_cliente,
                    observaciones,
                    descuento,
                    item["nombre_producto"],
                    item["cantidad_cotizada"],
                    item["precio_producto"],
                    precio_total,
                ]
            )

    flash("La cotización se ha guardado en cotizacion.csv.", "success")

    return redirect("/cotizar")


def generar_pdf_cotizacion(
    cotizacion_id, fecha, cliente, rut, observaciones, descuento, productos
):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Agregar información de la cotización al PDF
    pdf.cell(200, 10, txt=f"ID de Cotización: {cotizacion_id}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Fecha de Cotización: {fecha}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Nombre del Cliente: {cliente}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"RUT del Cliente: {rut}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Observaciones: {observaciones}", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Descuento: {descuento}%", ln=True, align="L")

    pdf.ln(10)

    # Agregar información de los productos cotizados al PDF
    pdf.cell(200, 10, txt="Productos Cotizados:", ln=True, align="L")
    for producto in productos:
        pdf.cell(200, 10, txt=producto, ln=True, align="L")

    # Generar el nombre del archivo PDF
    pdf_file_name = f"cotizaciones/cotizacion_{cotizacion_id}.pdf"

    # Guardar el PDF en la carpeta "cotizaciones"
    pdf.output(pdf_file_name)


# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------
#
# -------------------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------------------------------------


# ---------------------------------------
# Manejo de Errores
# ---------------------------------------


@app.errorhandler(404)
def page_not_found(e):
    return "Página no encontrada", 404


@app.errorhandler(500)
def internal_server_error(e):
    return "Error interno del servidor", 500


@app.errorhandler(403)
def forbidden_error(e):
    return "Acceso prohibido", 403


#######################################################################
####################Actualizacion: Patricio Alarcon####################
#######################################################################


@app.route("/v2/api/informes/", methods=["GET"])
def informesv2():
    # Registra la acción en el archivo CSV
    usuario_actual = session.get("usuario_actual")
    accion = "Inicio Informes"
    registrar_actividad(usuario_actual, accion)

    # Leer los datos de ventas desde el archivo CSV
    ventas_por_articulo = {}
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            if len(fila) >= 4:  # Asegurarse de que la fila tenga al menos 4 elementos
                _, _, _, nombre_producto, total_venta, *_ = fila
                total_venta = float(total_venta)  # Convertir a tipo float
                if nombre_producto in ventas_por_articulo:
                    ventas_por_articulo[nombre_producto] += total_venta
                else:
                    ventas_por_articulo[nombre_producto] = total_venta

    # Preparar datos para el gráfico de torta
    articulos = list(ventas_por_articulo.keys())
    ventas = list(ventas_por_articulo.values())

    # Crear el gráfico de torta
    plt.figure(figsize=(8, 8))
    plt.pie(ventas, labels=articulos, autopct="%1.1f%%", startangle=140)

    # Agregar título
    plt.title("Porcentaje de Ventas Globales por Artículo")

    # Mostrar el gráfico
    plt.axis("equal")

    # Guardar el gráfico en un BytesIO en lugar de un archivo
    img = BytesIO()
    plt.savefig(img, format="png")  # Guardar el gráfico en un BytesIO
    img.seek(0)

    # Codificar la imagen en base64
    img_base64 = base64.b64encode(img.read()).decode()

    # Cierra la figura de matplotlib
    plt.close()

    # Leer los datos del archivo CSV y calcular las ventas por producto
    ventas_por_producto = {}
    with open("ventas.csv", mode="r", newline="") as archivo_csv:
        lector_csv = csv.reader(archivo_csv)
        next(lector_csv)  # Salta la primera fila que contiene encabezados
        for fila in lector_csv:
            if len(fila) >= 7:  # Asegurarse de que la fila tenga al menos 7 elementos
                (
                    id_venta,
                    tipo_venta,
                    rut_cliente,
                    nombre_producto,
                    total_venta,
                    fecha_venta,
                    folio,
                ) = fila
                if nombre_producto in ventas_por_producto:
                    ventas_por_producto[nombre_producto] += int(total_venta)
                else:
                    ventas_por_producto[nombre_producto] = int(total_venta)

    ventas_por_tipo = leer_datos_ventas()
    tablas_html = generar_tablas_html(ventas_por_tipo)

    # Obtener nombres de productos y ventas como listas separadas
    productos = list(ventas_por_producto.keys())
    ventas = list(ventas_por_producto.values())

    # Crea el gráfico de barras
    plt.figure(figsize=(11, 8))
    plt.bar(productos, ventas)
    plt.xlabel("Nombre del Producto")
    plt.ylabel("Ventas")
    plt.title("Ventas por Producto")

    # Rotar etiquetas del eje x para mejorar la legibilidad
    plt.xticks(rotation=16, ha="right")

    # Guarda el gráfico en un BytesIO en lugar de un archivo temporal
    img2 = BytesIO()
    plt.savefig(img2, format="png")
    img2.seek(0)

    # Codifica la imagen en base64
    img_base64_2 = base64.b64encode(img2.read()).decode()

    # Cierra la figura de matplotlib
    plt.close()

    # Puedes enviar la imagen en el cuerpo de la respuesta junto con otros datos
    return {
        "img_base64": img_base64,
        "tablas": tablas_html,
        "username": session.get("usuario_actual"),
        "img_base64_2": img_base64_2,
    }


#
# Para completar la venta
#
@app.route("/api/completar_venta", methods=["POST"])
def completar_venta_json():
    try:
        # Obtén los datos enviados en el cuerpo JSON de la solicitud
        datos_venta = request.get_json()

        # Obtén el folio ingresado por el usuario desde el formulario
        folio = obtener_proximo_folio()

        total_venta = calcular_total_precio()  # Calcula el total de la venta
        global id_venta
        # Realiza las acciones necesarias para completar la venta en la base de datos
        # Obtén los valores ingresados por el usuario
        tipo_venta = datos_venta["tipo_venta"]
        rut_cliente = datos_venta.get(
            "rut_cliente"
        )  # Obtén el RUT del cliente (opcional)
        fecha_venta = datos_venta["fecha_venta"]

        # Conecta con la base de datos
        conn = sqlite3.connect("BDD.db")
        cursor = conn.cursor()

        # Inicializa la suma total de precios en cero
        total_precio = 0

        # Después de procesar la venta, incrementa la ID de la venta
        usuario_id = 1  # Reemplaza con el ID del usuario que realiza la venta
        fecha = datetime.now().date()
        comentario = "Venta realizada"

        # Convierte la fecha al formato "dd-mm-yyyy"
        fecha_venta = datetime.strptime(fecha_venta, "%Y-%m-%d").strftime("%d-%m-%Y")

        # Calcula el total de la venta antes de procesar los productos
        total_precio = calcular_total_precio()  # Mover esta línea aquí

        # Lista para almacenar los detalles de la venta
        detalles_venta = []

        # Inicializa la variable nombre_producto fuera del bucle
        nombre_producto = None

        # Inicializa datos_empresa fuera del bloque condicional
        datos_empresa = {}

        # Itera a través de los productos en la lista temporal de venta
        for item in lista_temporal_venta:
            id_producto, nombre_producto, cantidad_venta = item  # Desempaqueta la tupla

            # Obtiene el precio del producto desde la base de datos
            cursor.execute("SELECT precio FROM articulo WHERE id = ?", (id_producto,))
            row = cursor.fetchone()
            if row is not None:
                precio_producto = row[0]
            else:
                precio_producto = 0
            subtotal = precio_producto * cantidad_venta
            total_precio += subtotal

            # Registra la venta para este producto
            cursor.execute(
                "INSERT INTO venta (usuario_id, fecha, cantidad, comentario) VALUES (?, ?, ?, ?)",
                (usuario_id, fecha, cantidad_venta, comentario),
            )

            # Llama a la función 'guardar_registro_de_venta' con los datos de la venta, excluyendo num_boleta
            guardar_registro_de_venta(
                id_venta,
                tipo_venta,
                rut_cliente,
                nombre_producto,
                total_venta,
                fecha_venta,
                folio,
            )

            # Actualiza la cantidad disponible del producto en la base de datos
            cursor.execute(
                "UPDATE articulo SET cantidad = cantidad - ? WHERE id = ?",
                (cantidad_venta, id_producto),
            )

            # Agrega los detalles de la venta a la lista
            detalles_venta.append(
                {
                    "nombre_producto": nombre_producto,
                    "cantidad_venta": cantidad_venta,
                    "precio_producto": precio_producto,
                    "subtotal": subtotal,
                }
            )

            # Obtén los datos de la empresa
            datos_empresa = obtener_datos_empresa()
        # Crear un diccionario con los datos de la venta y la empresa
        datos_venta = {
            "id_venta": id_venta,
            "tipo_venta": tipo_venta,
            "rut_cliente": rut_cliente,
            "nombre_producto": nombre_producto,
            "total_venta": total_venta,
            "fecha_venta": datos_venta["fecha_venta"],
            "folio": folio,
            "Nombre": datos_empresa.get("Nombre", ""),
            "RUT": datos_empresa.get("RUT", ""),
            "Dirección": datos_empresa.get("Dirección", ""),
            "Número de Contacto": datos_empresa.get("Número de Contacto", ""),
            "Correo Electrónico": datos_empresa.get("Correo Electrónico", ""),
            "Logo": datos_empresa.get("Logo", ""),
            "Giro": datos_empresa.get("Giro", ""),
        }
        # Guardar los datos de la venta y la empresa en el archivo registro_ventas.csv
        with open("registro_ventas.csv", mode="a", newline="") as archivo_csv:
            campos = [
                "id_venta",
                "tipo_venta",
                "rut_cliente",
                "nombre_producto",
                "total_venta",
                "fecha_venta",
                "folio",
                "Nombre",
                "RUT",
                "Dirección",
                "Número de Contacto",
                "Correo Electrónico",
                "Logo",
                "Giro",
            ]
            escritor_csv = csv.DictWriter(archivo_csv, fieldnames=campos)

            # Verificar si el archivo está vacío y escribir encabezados si es necesario
            if archivo_csv.tell() == 0:
                escritor_csv.writeheader()

            escritor_csv.writerow(datos_venta)

        # Llama a la función para generar el comprobante
        generar_comprobante(datos_venta, ruta_boletas)
        # Limpia la lista temporal de venta
        lista_temporal_venta.clear()

        # Confirma y cierra la conexión con la base de datos
        conn.commit()
        conn.close()

        mensaje_respuesta = (
            f"La venta se ha completado con éxito. Total: {total_precio}"
        )
        respuesta_json = {
            "mensaje": mensaje_respuesta,
            "total_precio": total_precio,
            "detalles_productos": detalles_venta,
            "folio": folio,
        }

        return jsonify(respuesta_json)
    except Exception as e:
        print("Error al completar la venta:", e)
        return jsonify({"mensaje": f"Error al completar la venta: {e}"})


#
# Login de usuarios
#


@app.route("/api/login", methods=["POST"])
def api_login():
    # Obtener datos del cuerpo de la solicitud
    data = request.get_json()

    # Extraer nombre de usuario y contraseña
    nombre_usuario = data.get("nombre_usuario")
    contrasena = data.get("contrasena")

    # Conectar a la base de datos SQLite
    conn = sqlite3.connect("BDD.db")
    cursor = conn.cursor()

    try:
        # Consultar la base de datos para obtener las credenciales del usuario
        query = f"SELECT id, nombre, contrasena, rol_id FROM usuario WHERE nombre = ?"
        cursor.execute(query, (nombre_usuario,))
        result = cursor.fetchone()

        # Verificar las credenciales
        if result and result[2] == contrasena:  # La posición 2 es la contraseña
            # Autenticación exitosa
            response = {
                "mensaje": "Inicio de sesión exitoso",
                "autenticado": True,
                "usuario_id": result[0],
                "nombre_usuario": result[1],
                "rol_id": result[3],
            }
        else:
            # Autenticación fallida
            response = {
                "mensaje": "Nombre de usuario o contraseña incorrectos",
                "autenticado": False,
            }
    finally:
        # Cerrar la conexión a la base de datos
        conn.close()

    return jsonify(response)


@app.route("/api/eliminar_articulo/<int:id>", methods=["DELETE"])
def eliminar_articulo_json(id):
    try:
        # Conecta con la base de datos y elimina el artículo
        conn = conectar_base_de_datos()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articulo WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        mensaje = f"Artículo con ID {id} eliminado exitosamente."
        return jsonify({"mensaje": mensaje})
    except sqlite3.Error as e:
        print("Error al eliminar el artículo en la base de datos:", e)
        return jsonify({"mensaje": "Error al eliminar el artículo en la base de datos"})


#
# rutas para filtros
#


@app.route("/api/buscar_producto/<codigo_barras>", methods=["GET"])
def buscar_producto_por_codigo_json(codigo_barras):
    try:
        # Realiza la búsqueda en la base de datos para obtener los datos del producto
        conn = sqlite3.connect(
            "BDD.db"
        )  # Asegúrate de usar el nombre correcto de tu base de datos
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulo WHERE id = ?", (codigo_barras,))
        producto = (
            cursor.fetchone()
        )  # Obtiene el producto con el código de barras especificado
        conn.close()

        if producto:
            # Si se encuentra el producto, devuelve los detalles del producto en formato JSON
            producto_json = {
                "id": producto[0],
                "nombre": producto[1],
                "descripcion": producto[2],
                "cantidad": producto[3],
                "precio": producto[4],
                "ubicacion": producto[5],
                "cantidad_maxima": producto[6],
                "cantidad_minima": producto[7],
            }
            return jsonify({"producto": producto_json})
        else:
            mensaje = "Producto no encontrado."
            return jsonify({"mensaje": mensaje})
    except sqlite3.Error as e:
        print("Error al buscar el producto en la base de datos:", e)
        return jsonify({"mensaje": "Error al buscar el producto en la base de datos"})


#
# esta seccion es para obtener los articulos en json de manera ordenada.
#


@app.route("/api/articulos", methods=["GET"])
def obtener_datos_de_articulos_json():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, descripcion, cantidad, precio, ubicacion, cantidad_maxima, cantidad_minima FROM articulo"
        )
        datos = cursor.fetchall()
        conn.close()

        # Formatea los datos como un JSON y los devuelve
        articulos_json = []
        for venta in datos:
            venta_dict = {
                "id": venta[0],
                "nombre": venta[1],
                "descripcion": venta[2],
                "cantidad": venta[3],
                "precio": venta[4],
                "ubicacion": venta[5],
                "cantidad_maxima": venta[6],
                "cantidad_minima": venta[7],
            }
            articulos_json.append(venta_dict)

        return jsonify({"articulos": articulos_json})
    except sqlite3.Error as e:
        print("Error al obtener datos de la base de datos:", e)
        return jsonify({"articulos": []})


# Inicio
#
# Leyendo archivos csv del proyecto, solo sera de lectura para la app movil
#
@app.route("/api/ultimas_ventas", methods=["GET"])
def obtener_ultimas_ventas_json():
    try:
        with open("ventas.csv", mode="r", newline="") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            ultimas_ventas = list(lector_csv)[:]

        # Lista para almacenar las ventas formateadas como diccionarios
        ultimas_ventas_formateadas = []

        # Recorre las últimas ventas y forma un diccionario para cada una
        for venta in ultimas_ventas:
            ultima_venta_dict = {
                "id": venta[0],
                "tipo_pago": venta[1],
                "otra_informacion": venta[2],
                "producto": venta[3],
                "monto": venta[4],
                "fecha": venta[5],
                "codigo": venta[6],
            }
            ultimas_ventas_formateadas.append(ultima_venta_dict)

        # Formatea los datos como un JSON y lo devuelve
        return jsonify({"ultimas_ventas": ultimas_ventas_formateadas})
    except FileNotFoundError:
        return jsonify({"ultimas_ventas": []})


@app.route("/api/cantidad_ventas", methods=["GET"])
def obtener_cantidad_ventas_json():
    try:
        with open("ventas.csv", mode="r", newline="") as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            cantidad_ventas = (
                len(list(lector_csv)) - 1
            )  # Resta 1 para excluir el encabezado

        # Formatea los datos como un JSON y lo devuelve
        return jsonify({"cantidad_ventas": cantidad_ventas})
    except FileNotFoundError:
        return jsonify({"cantidad_ventas": 0})


@app.route("/api/cantidad_usuarios", methods=["GET"])
def obtener_cantidad_usuarios_json():
    try:
        with open("users.txt", "r") as archivo_users:
            cantidad_usuarios = sum(1 for linea in archivo_users)

        # Formatea los datos como un JSON y lo devuelve
        return jsonify({"cantidad_usuarios": cantidad_usuarios})
    except FileNotFoundError:
        return jsonify({"cantidad_usuarios": 0})


# cantidad de articulos


@app.route("/api/cantidad_articulos", methods=["GET"])
def obtener_cantidad_articulos_json():
    try:
        conexion = sqlite3.connect("BDD.db")
        cursor = conexion.cursor()

        # Consulta para contar la cantidad de artículos en la tabla 'articulo'
        cursor.execute("SELECT COUNT(*) FROM articulo")
        cantidad_articulos = cursor.fetchone()[0]

        # Cierra la conexión a la base de datos
        conexion.close()

        # Formatea los datos como un JSON y lo devuelve
        return jsonify({"cantidad_articulos": cantidad_articulos})
    except sqlite3.Error as error:
        print(
            "Error al obtener la cantidad de artículos desde la base de datos:", error
        )
        return jsonify({"cantidad_articulos": 0})

        # Fin


#######################################################################
####################Actualizacion: Patricio Alarcon####################
#######################################################################


if __name__ == "__main__":
    app.run(debug=True)
