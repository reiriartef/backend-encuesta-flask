from flask import Flask, request, jsonify
import json
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Configuración de la base de datos

db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")


# Conexión a la base de datos
def get_db_connection():
    conn = psycopg2.connect(
        host=db_host, dbname=db_name, user=db_user, password=db_password
    )
    return conn


@app.route("/api/submit", methods=["POST"])
def submit_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Procesar datos del formulario
        form_data = request.form.to_dict()
        print("Datos del formulario:", form_data)

        # Procesar el archivo de la foto
        foto_funcionario = None
        if "fotoFuncionario" in request.files:
            file = request.files["fotoFuncionario"]
            if file.filename != "":
                foto_funcionario = file.read()

        # Insertar o recuperar responsable
        cursor.execute(
            "INSERT INTO responsables (name, phone) VALUES (%s, %s) RETURNING id",
            (form_data["responsableName"], form_data["responsablePhone"]),
        )
        responsable_id = cursor.fetchone()["id"]

        # Recuperar ID de la sede
        cursor.execute("SELECT id FROM sedes WHERE nombre = %s", (form_data["sede"],))
        sede = cursor.fetchone()
        if sede:
            sede_id = sede["id"]
        else:
            cursor.execute(
                "INSERT INTO sedes (nombre) VALUES (%s) RETURNING id",
                (form_data["sede"],),
            )
            sede_id = cursor.fetchone()["id"]

        # Insertar datos del funcionario
        cursor.execute(
            """
            INSERT INTO funcionarios (
                funcionario_id, name, age, gender, phone, tiene_carnet, razon_no_carnet, 
                foto, shirt_size, suit_size, shoe_size, num_carga_familiar, 
                num_fasdem_beneficiarios, sede_id, responsable_id, instagram, tiktok, facebook, cargo, tipo_personal, tipo_trabajador, adscripcion_nominal, ubicacion_fisica, funciones, estado_civil, nivel_academico, titulo_educacion_superior
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s, %s, %s, %s, %s, %s, %s,%s,%s,%s)
            RETURNING id
            """,
            (
                form_data["funcionarioID"],
                form_data["funcionarioName"],
                form_data["age"],
                form_data["gender"],
                form_data["funcionarioPhone"],
                form_data["tieneCarnet"] == "Sí",
                form_data.get("razonNoCarnet"),
                foto_funcionario,
                form_data.get("shirtSize"),
                form_data.get("suitSize"),
                form_data.get("shoeSize"),
                form_data.get("numCargaFamiliar"),
                form_data.get("numFasdemBeneficiarios"),
                sede_id,
                responsable_id,
                form_data.get("instagram"),
                form_data.get("tiktok"),
                form_data.get("facebook"),
                form_data.get("cargoActual"),
                form_data.get("tipoPersonal"),
                form_data.get("tipoTrabajador"),
                form_data.get("adscripcionNominal"),
                form_data.get("ubicacionFisica"),
                form_data.get("funcionesLaborales"),
                form_data.get("estadoCivil"),
                form_data.get("nivelAcademico"),
                form_data.get("tituloEducacionSuperior"),
            ),
        )
        funcionario_id = cursor.fetchone()["id"]

        cargas_familiares = json.loads(form_data.get("cargasFamiliares", "[]"))
        beneficiarios_fasdem = json.loads(form_data.get("beneficiariosFasdem", "[]"))
        hijos = json.loads(form_data.get("hijos", "[]"))

        for carga in cargas_familiares:
            cursor.execute(
                "INSERT INTO carga_familiar (funcionario_id, nombre, edad, patologias) VALUES (%s,%s,%s,%s)",
                [
                    funcionario_id,
                    carga.get("nombre"),
                    carga.get("edad"),
                    carga.get("patologias"),
                ],
            )

        for beneficiario in beneficiarios_fasdem:
            cursor.execute(
                "INSERT INTO beneficiarios_fasdem (funcionario_id, nombre, edad, patologias) VALUES (%s,%s,%s,%s)",
                [
                    funcionario_id,
                    beneficiario.get("nombre"),
                    beneficiario.get("edad"),
                    beneficiario.get("patologias"),
                ],
            )

        for hijo in hijos:
            cursor.execute(
                "INSERT INTO hijos (funcionario_id, nombre, edad, patologias) VALUES (%s,%s,%s,%s)",
                [
                    funcionario_id,
                    hijo.get("nombre"),
                    hijo.get("edad"),
                    hijo.get("patologias"),
                ],
            )

        conn.commit()
        return jsonify({"message": "Datos almacenados correctamente"}), 200

    except Exception as e:
        print("Error al procesar la solicitud:", e)
        return jsonify(
            {"error": "Error en el servidor, contacte al administrador"}
        ), 500

    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    app.run(debug=True)
