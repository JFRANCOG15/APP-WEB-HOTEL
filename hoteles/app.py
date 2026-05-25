from flask import Flask, render_template, request, redirect, url_for, session
from pymysql.cursors import DictCursor
import pymysql
import datetime
from flask_moment import Moment

moment = Moment


app = Flask(__name__)  
app.secret_key = "mi_clave_super_secreta_cambiar_en_produccion"

# Configuración de conexión más robusta
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="hoteles",
        cursorclass=DictCursor,
        autocommit=True
    )

@app.route("/")
def index():
    usuario = session.get("usuario")
    return render_template("index.html", usuario=usuario)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        documento = request.form["documento"]
        clave = request.form["clave"]

        try:
            conexion = get_db_connection()
            with conexion.cursor() as cursor:
                sql = "SELECT * FROM clientes WHERE Numero_documento=%s AND clave=%s"
                cursor.execute(sql, (documento, clave))
                cliente = cursor.fetchone()
            conexion.close()

            if cliente:
                session["usuario"] = cliente["Nombre_cliente"]
                session["documento"] = cliente["Numero_documento"]
                return redirect(url_for("index"))
            else:
                return render_template("login.html", error="Documento o clave incorrecta")
        except Exception as e:
            return render_template("login.html", error="Error de conexión")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear() 
    return redirect(url_for("index"))

@app.route("/crear_cliente", methods=["GET", "POST"])
def crear_cliente():
    if request.method == "POST":
        v_documento = request.form["documento"]
        v_nombre = request.form["nombre"] 
        v_apellido = request.form["apellido"]
        v_telefono = request.form["telefono"]
        v_correo = request.form["email"]
        v_clave = request.form.get("clave", "123456")  # Clave por defecto
        
        try:
            conexion = get_db_connection()
            with conexion.cursor() as cursor:
                sql = """
                    INSERT INTO clientes(Numero_documento, Nombre_cliente, Apellido_cliente, 
                    Telefono_cliente, Email_cliente, clave)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (v_documento, v_nombre, v_apellido, v_telefono, v_correo, v_clave))
            conexion.close()
            return redirect(url_for("crear_cliente"))
        except Exception as e:
            return render_template("crear_cliente.html", error="Error al crear cliente")
    
    return render_template("crear_cliente.html")

@app.route("/clientes", methods=["GET"])
def listar_clientes():
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            cursor.execute('SELECT * FROM clientes')
            clientes = cursor.fetchall()
        conexion.close()
        return render_template("clientes.html", clientes=clientes)
    except Exception as e:
        return render_template("clientes.html", clientes=[], error="Error al cargar clientes")
            
@app.route('/Tipo_habitacion', methods=['GET', 'POST'])
def Tipo_habitacion():
    return render_template('Tipo_habitacion.html')

@app.route("/ciudades", methods=["GET"])
def listar_ciudades():
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM ciudades")
            ciudades = cursor.fetchall()
        conexion.close()
        return render_template("ciudades.html", ciudades=ciudades)
    except Exception as e:
        return render_template("ciudades.html", ciudades=[], error="Error al cargar ciudades")

@app.route("/crear_sucursal", methods=["GET","POST"])
def crear_sucursal():
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT Id_ciudades, Nombre_ciudades FROM ciudades") 
            ciudades = cursor.fetchall()

            if request.method == "POST":
                nombre = request.form["Nombre_sucursal"]
                direccion = request.form["Direccion_sucursal"]
                ciudad_id = request.form["Id_ciudades"]

                sql = """
                    INSERT INTO sucursales (Nombre_sucursal, Direccion_sucursal, Id_ciudades, Id_hotel)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre, direccion, ciudad_id, 1))
                conexion.close()
                return redirect(url_for("index"))
        
        conexion.close()
        return render_template("crear_sucursal.html", ciudades=ciudades)
    except Exception as e:
        return render_template("crear_sucursal.html", ciudades=[], error="Error al procesar sucursal")
    
@app.route("/crear_habitacion", methods=["GET","POST"])
def crear_habitacion():
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT Id_sucursal, Nombre_sucursal FROM sucursales") 
            sucursales = cursor.fetchall()
            cursor.execute("SELECT Id_tipo, Nombre_tipo FROM tipo_habitacion") 
            tipo_habitacion = cursor.fetchall()

            if request.method == "POST":
                nombre_hab = request.form["nombre_hab"]
                telefono = request.form["telefono"]
                tipo_id = request.form["tipo_id"]
                sucursal_id = request.form["sucursal_id"]

                sql = """
                    INSERT INTO habitaciones (Nombre_habitacion, Telefono_habitacion, Id_tipo, Id_sucursal)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (nombre_hab, telefono, tipo_id, sucursal_id))
                conexion.close()
                return redirect(url_for("index"))
        
        conexion.close()
        return render_template("crear_habitacion.html", sucursales=sucursales, tipo_habitacion=tipo_habitacion)
    except Exception as e:
        return render_template("crear_habitacion.html", sucursales=[], tipo_habitacion=[], error="Error al procesar habitación")

@app.route("/consultar_habitaciones", methods=["GET"])
def consultar_habitaciones():
    sucursal = request.args.get("sucursal")
    tipo = request.args.get("tipo")
 
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            sql = """
                SELECT h.Id_habitacion, h.Nombre_habitacion, h.telefono_habitacion, s.Nombre_sucursal, 
                th.Nombre_tipo, th.Precio, c.Nombre_ciudades, th.capacidad 
                FROM habitaciones h 
                INNER JOIN tipo_habitacion th ON h.Id_tipo = th.Id_tipo 
                INNER JOIN sucursales s ON h.Id_sucursal = s.Id_sucursal 
                INNER JOIN ciudades c ON s.Id_ciudades = c.Id_ciudades
                WHERE 1=1
            """
            filtros = []

            if sucursal:
                sql += " AND s.Id_sucursal = %s"
                filtros.append(int(sucursal))

            if tipo:
                sql += " AND th.Id_tipo = %s"
                filtros.append(int(tipo)) 
 
            cursor.execute(sql, filtros)
            habitaciones = cursor.fetchall()
 
            cursor.execute("SELECT Id_sucursal, Nombre_sucursal FROM sucursales")
            sucursales = cursor.fetchall()

            cursor.execute("SELECT Id_tipo, Nombre_tipo FROM tipo_habitacion")
            tipos = cursor.fetchall()

        conexion.close()
        return render_template(
            "consultar_habitaciones.html",
            habitaciones=habitaciones,
            sucursales=sucursales,
            tipo=tipos,
            filtro_sucursal=sucursal,
            filtro_tipo=tipo
        )
    except Exception as e:
        return render_template("consultar_habitaciones.html", habitaciones=[], error="Error al consultar habitaciones")

# RUTA FALTANTE - CREAR RESERVA
@app.route("/crear_reserva", methods=["GET", "POST"])
def crear_reserva():
    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            # Obtener sucursales y tipos para el formulario
            cursor.execute("SELECT Id_sucursal, Nombre_sucursal FROM sucursales")
            sucursales = cursor.fetchall()
            cursor.execute("SELECT Id_tipo, Nombre_tipo FROM tipo_habitacion")
            tipos = cursor.fetchall()
            
            habitaciones = []
            
            if request.method == "POST":
                sucursal_id = request.form.get("sucursal")
                tipo_id = request.form.get("tipo")
                fecha_ini = request.form.get("fecha_ini")
                fecha_fin = request.form.get("fecha_fin")
                
                # Validar fechas
                if fecha_ini and fecha_fin:
                    fecha_inicio = datetime.datetime.strptime(fecha_ini, "%Y-%m-%d")
                    fecha_salida = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
                    
                    if fecha_inicio >= fecha_salida:
                        return render_template("crear_reserva.html", 
                                            sucursales=sucursales, 
                                            tipos=tipos, 
                                            error="La fecha de salida debe ser posterior a la de ingreso")
                
                # Buscar habitaciones disponibles
                sql = """
                    SELECT h.Id_habitacion, h.Nombre_habitacion, s.Nombre_sucursal, 
                    th.Nombre_tipo, th.Precio, th.capacidad 
                    FROM habitaciones h
                    INNER JOIN tipo_habitacion th ON h.Id_tipo = th.Id_tipo
                    INNER JOIN sucursales s ON h.Id_sucursal = s.Id_sucursal
                    WHERE s.Id_sucursal = %s AND th.Id_tipo = %s
                    AND h.Id_habitacion NOT IN (
                        SELECT r.Id_habitacion FROM reservas r 
                        WHERE r.Estado_reserva = 'Confirmada' 
                        AND ((r.Fecha_ing <= %s AND r.Fecha_sal > %s) 
                        OR (r.Fecha_ing < %s AND r.Fecha_sal >= %s)
                        OR (r.Fecha_ing >= %s AND r.Fecha_sal <= %s))
                    )
                """
                cursor.execute(sql, (sucursal_id, tipo_id, fecha_ini, fecha_ini, 
                                   fecha_fin, fecha_fin, fecha_ini, fecha_fin))
                habitaciones = cursor.fetchall()
        
        conexion.close()
        return render_template("crear_reserva.html", 
                             sucursales=sucursales, 
                             tipos=tipos, 
                             habitaciones=habitaciones)
    except Exception as e:
        return render_template("crear_reserva.html", sucursales=[], tipos=[], error="Error al procesar reserva")

@app.route("/consultar_reservas")
def consultar_reservas():
    cliente = request.args.get("Numero_documento")
    tipo = request.args.get("Tipo_habitacion")
    fecha_ini = request.args.get("Fecha_ing")
    fecha_fin = request.args.get("Fecha_sal")
    estado = request.args.get("Estado_reserva")

    try:
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            sql = """
                SELECT r.Id_reserva, r.Fecha_ing, r.Fecha_sal, r.Estado_reserva, r.Total, r.fecha,
                r.Numero_documento, r.Id_habitacion, c.Nombre_cliente, c.Apellido_Cliente, c.Telefono_cliente,
                h.Nombre_habitacion, th.Nombre_tipo, s.Nombre_sucursal, s.Direccion_sucursal
                FROM reservas r 
                INNER JOIN clientes c ON r.Numero_documento = c.Numero_documento
                INNER JOIN habitaciones h ON r.Id_habitacion = h.Id_habitacion
                INNER JOIN tipo_habitacion th ON h.Id_tipo = th.Id_tipo
                INNER JOIN sucursales s ON h.Id_sucursal = s.Id_sucursal
                WHERE 1=1
            """

            filtros = []

            if cliente:
                sql += " AND r.Numero_documento = %s"
                filtros.append(cliente)

            if tipo:
                sql += " AND h.Id_tipo = %s"
                filtros.append(int(tipo)) 

            if fecha_ini and fecha_fin:
                sql += " AND r.Fecha_ing >= %s AND r.Fecha_sal <= %s"
                filtros.append(fecha_ini)
                filtros.append(fecha_fin)
            elif fecha_ini:
                sql += " AND r.Fecha_ing >= %s"
                filtros.append(fecha_ini)
            elif fecha_fin:
                sql += " AND r.Fecha_sal <= %s"
                filtros.append(fecha_fin)
                
            if estado:
                sql += " AND r.Estado_Reserva = %s"
                filtros.append(estado)

            cursor.execute(sql, filtros)
            reservas = cursor.fetchall() or []

            cursor.execute("SELECT Numero_documento, Nombre_cliente, Apellido_cliente FROM clientes")
            clientes = cursor.fetchall() or []

            cursor.execute("SELECT Id_tipo, Nombre_tipo FROM tipo_habitacion")
            tipos = cursor.fetchall()

            cursor.execute("SELECT DISTINCT Estado_reserva FROM reservas")
            estados = cursor.fetchall()

        conexion.close()
        return render_template("consultar_reservas.html",
            reservas=reservas,
            clientes=clientes,
            tipos=tipos, 
            estados=estados,
            fecha_ini=fecha_ini,
            fecha_fin=fecha_fin
        )
    except Exception as e:
        return render_template("consultar_reservas.html", reservas=[], error="Error al consultar reservas")

@app.route("/guardar_reserva", methods=["POST"])
def guardar_reserva():
    try:
        habitacion_id = request.form.get("habitacion_id")
        fecha_ini = request.form.get("fecha_ini")
        fecha_fin = request.form.get("fecha_fin")
        documento = request.form.get("documento")

        # Validar que el cliente existe
        conexion = get_db_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM clientes WHERE Numero_documento = %s", (documento,))
            cliente = cursor.fetchone()
            
            if not cliente:
                conexion.close()
                return redirect(url_for("crear_reserva") + "?error=cliente_no_existe")

            # Obtener precio de la habitación
            cursor.execute("""
                SELECT th.Precio
                FROM habitaciones h
                INNER JOIN tipo_habitacion th ON h.Id_tipo = th.Id_tipo
                WHERE h.Id_habitacion = %s
            """, (habitacion_id,))
            
            resultado = cursor.fetchone()
            if not resultado:
                conexion.close()
                return redirect(url_for("crear_reserva") + "?error=habitacion_no_existe")
                
            precio = resultado["Precio"]

        # Calcular días y total
        d1 = datetime.datetime.strptime(fecha_ini, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
        dias = (d2 - d1).days
        
        if dias <= 0:
            conexion.close()
            return redirect(url_for("crear_reserva") + "?error=fechas_invalidas")
            
        total = precio * dias

        # Guardar reserva
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO reservas (Fecha_ing, Fecha_sal, Estado_reserva, Total, Numero_documento, fecha, Id_habitacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                fecha_ini, fecha_fin, "Confirmada", total, documento, 
                int(d1.strftime("%Y%m%d")), habitacion_id
            ))

        conexion.close()
        return redirect(url_for("consultar_reservas"))
        
    except Exception as e:
        return redirect(url_for("crear_reserva") + "?error=error_interno")

if __name__ == "__main__":
    app.run(debug=True)