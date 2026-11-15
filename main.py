
import os
import shutil
import sqlite3
import threading
import customtkinter as ctk

from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageOps

from services.face_comparator import comparar_rostro


# =====================================================
# CONFIGURACION GENERAL
# =====================================================

APP_NAME = "Analizador de rostro IA"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
FACES_DIR = os.path.join(BASE_DIR, "rostros_autorizados")

DB_PATH = os.path.join(DATABASE_DIR, "rostros.db")

os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)


# =====================================================
# COLORES
# =====================================================

BG_COLOR = "#101418"
PANEL_COLOR = "#171E25"
IMAGE_COLOR = "#222B35"

WHITE = "#FFFFFF"
GRAY = "#AAB5C0"

GREEN = "#32F477"
RED = "#FF343F"
ORANGE = "#E87524"
BLUE = "#36B9F5"
YELLOW = "#F5B942"


# =====================================================
# BASE DE DATOS
# =====================================================

def conectar_db():

    return sqlite3.connect(DB_PATH)


def inicializar_db():

    conexion = conectar_db()

    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nombre TEXT NOT NULL,

            imagen TEXT NOT NULL,

            fecha_registro TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conexion.commit()
    conexion.close()


# =====================================================
# APLICACION PRINCIPAL
# =====================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class AnalizadorRostro:

    def __init__(self, root):

        self.root = root

        self.root.title(APP_NAME)

        self.root.geometry("1200x780")

        self.root.minsize(950, 680)

        self.root.configure(fg_color=BG_COLOR)

        self.imagen_seleccionada = None

        self.consultando = False

        self.robot_estado = 0

        self.imagen_ctk = None

        inicializar_db()

        self.crear_interfaz()

        self.actualizar_contador()

        self.animar_robot()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.cerrar_aplicacion
        )

    # =================================================
    # CREAR INTERFAZ
    # =================================================

    def crear_interfaz(self):

        # ENCABEZADO

        header = ctk.CTkFrame(
            self.root,
            fg_color=PANEL_COLOR,
            corner_radius=15
        )

        header.pack(
            fill="x",
            padx=20,
            pady=(20, 10)
        )

        titulo = ctk.CTkLabel(
            header,
            text="ANALIZADOR DE ROSTRO IA",
            font=("Segoe UI", 27, "bold"),
            text_color=WHITE
        )

        titulo.pack(
            side="left",
            padx=25,
            pady=20
        )

        self.estado_sistema = ctk.CTkLabel(
            header,
            text="● SISTEMA ACTIVO",
            font=("Segoe UI", 13, "bold"),
            text_color=GREEN
        )

        self.estado_sistema.pack(
            side="right",
            padx=25
        )

        # CONTENEDOR CENTRAL

        contenido = ctk.CTkFrame(
            self.root,
            fg_color="transparent"
        )

        contenido.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        contenido.grid_columnconfigure(
            0,
            weight=1
        )

        contenido.grid_columnconfigure(
            1,
            weight=1
        )

        contenido.grid_rowconfigure(
            0,
            weight=1
        )

        # PANEL IZQUIERDO

        panel_izquierdo = ctk.CTkFrame(
            contenido,
            fg_color=PANEL_COLOR,
            corner_radius=18
        )

        panel_izquierdo.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        # ROBOT

        robot_titulo = ctk.CTkLabel(
            panel_izquierdo,
            text="ASISTENTE INTELIGENTE",
            font=("Segoe UI", 16, "bold"),
            text_color=WHITE
        )

        robot_titulo.pack(pady=(25, 5))

        self.robot = ctk.CTkLabel(
            panel_izquierdo,
            text="🤖",
            font=("Segoe UI Emoji", 75)
        )

        self.robot.pack(pady=10)

        self.robot_mensaje = ctk.CTkLabel(
            panel_izquierdo,
            text="Estoy listo para analizar",
            font=("Segoe UI", 15, "bold"),
            text_color=GRAY
        )

        self.robot_mensaje.pack(pady=5)

        # SEPARADOR

        ctk.CTkFrame(
            panel_izquierdo,
            height=2,
            fg_color="#303B46"
        ).pack(
            fill="x",
            padx=25,
            pady=20
        )

        # BOTON CARGAR IMAGEN

        self.boton_cargar = ctk.CTkButton(
            panel_izquierdo,
            text="📂  CARGAR IMAGEN",
            height=52,
            corner_radius=10,
            fg_color=ORANGE,
            hover_color="#FF923F",
            text_color=WHITE,
            font=("Segoe UI", 16, "bold"),
            command=self.cargar_imagen
        )

        self.boton_cargar.pack(
            fill="x",
            padx=25,
            pady=10
        )

        # BOTON REGISTRAR

        self.boton_registrar = ctk.CTkButton(
            panel_izquierdo,
            text="➕  REGISTRAR ROSTRO AUTORIZADO",
            height=52,
            corner_radius=10,
            fg_color="#263B50",
            hover_color="#345675",
            text_color=WHITE,
            font=("Segoe UI", 14, "bold"),
            command=self.registrar_rostro
        )

        self.boton_registrar.pack(
            fill="x",
            padx=25,
            pady=10
        )

        # CONTADOR

        self.contador = ctk.CTkLabel(
            panel_izquierdo,
            text="ROSTROS REGISTRADOS: 0",
            font=("Segoe UI", 13, "bold"),
            text_color=BLUE
        )

        self.contador.pack(pady=20)

        # PANEL DERECHO

        panel_derecho = ctk.CTkFrame(
            contenido,
            fg_color=PANEL_COLOR,
            corner_radius=18
        )

        panel_derecho.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        titulo_imagen = ctk.CTkLabel(
            panel_derecho,
            text="IMAGEN PARA ANALIZAR",
            font=("Segoe UI", 17, "bold"),
            text_color=WHITE
        )

        titulo_imagen.pack(pady=(25, 15))

        # VISUALIZACION

        self.imagen_panel = ctk.CTkLabel(
            panel_derecho,
            text="📷\n\nSeleccioná una fotografía",
            font=("Segoe UI", 18),
            text_color=GRAY,
            fg_color=IMAGE_COLOR,
            corner_radius=15,
            width=400,
            height=300
        )

        self.imagen_panel.pack(
            padx=25,
            pady=10,
            fill="both",
            expand=True
        )

        # NOMBRE ARCHIVO

        self.nombre_archivo = ctk.CTkLabel(
            panel_derecho,
            text="Ninguna imagen seleccionada",
            font=("Segoe UI", 12),
            text_color=GRAY
        )

        self.nombre_archivo.pack(pady=10)

        # BOTON ANALIZAR

        self.boton_analizar = ctk.CTkButton(
            panel_derecho,
            text="🔍  ANALIZAR ROSTRO",
            height=55,
            corner_radius=12,
            fg_color="#168B48",
            hover_color="#20B85F",
            text_color=WHITE,
            font=("Segoe UI", 17, "bold"),
            command=self.iniciar_analisis
        )

        self.boton_analizar.pack(
            fill="x",
            padx=25,
            pady=20
        )

        # RESULTADO

        resultado_frame = ctk.CTkFrame(
            self.root,
            fg_color=PANEL_COLOR,
            corner_radius=15
        )

        resultado_frame.pack(
            fill="x",
            padx=20,
            pady=(5, 20)
        )

        ctk.CTkLabel(
            resultado_frame,
            text="RESULTADO DEL SISTEMA",
            font=("Segoe UI", 14, "bold"),
            text_color=GRAY
        ).pack(pady=(15, 5))

        self.resultado = ctk.CTkLabel(
            resultado_frame,
            text="ESPERANDO ANALISIS",
            font=("Segoe UI", 25, "bold"),
            text_color=WHITE
        )

        self.resultado.pack(pady=(5, 15))

    # =================================================
    # CARGAR IMAGEN
    # =================================================

    def cargar_imagen(self):

        ruta = filedialog.askopenfilename(
            title="Seleccionar fotografía",
            filetypes=[
                (
                    "Imágenes",
                    "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"
                ),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        try:

            with Image.open(ruta) as original:

                imagen = ImageOps.exif_transpose(
                    original
                ).convert("RGB")

            self.imagen_seleccionada = ruta

            imagen.thumbnail((430, 330))

            self.imagen_ctk = ctk.CTkImage(
                light_image=imagen,
                dark_image=imagen,
                size=imagen.size
            )

            self.imagen_panel.configure(
                image=self.imagen_ctk,
                text=""
            )

            self.nombre_archivo.configure(
                text=os.path.basename(ruta)
            )

            self.resultado.configure(
                text="IMAGEN CARGADA - PENDIENTE",
                text_color=WHITE
            )

            self.robot_mensaje.configure(
                text="Fotografía recibida correctamente."
            )

        except Exception as error:

            messagebox.showerror(
                "Error",
                f"No se pudo abrir la imagen:\n{error}"
            )

    # =================================================
    # REGISTRAR ROSTRO
    # =================================================

    def registrar_rostro(self):

        ruta = filedialog.askopenfilename(
            title="Seleccionar fotografía autorizada",
            filetypes=[
                (
                    "Imágenes",
                    "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff"
                )
            ]
        )

        if not ruta:
            return

        nombre = simpledialog.askstring(
            "Registrar persona",
            "Ingresá el nombre o identificador:"
        )

        if not nombre or not nombre.strip():

            return

        nombre = nombre.strip()

        destino = None

        try:

            with Image.open(ruta) as imagen:
                imagen.verify()

            extension = os.path.splitext(ruta)[1].lower()

            nombre_archivo = (
                f"persona_{os.urandom(6).hex()}{extension}"
            )

            destino = os.path.join(
                FACES_DIR,
                nombre_archivo
            )

            shutil.copy2(
                ruta,
                destino
            )

            conexion = conectar_db()

            try:

                cursor = conexion.cursor()

                cursor.execute(
                    """
                    INSERT INTO personas (nombre, imagen)
                    VALUES (?, ?)
                    """,
                    (nombre, nombre_archivo)
                )

                conexion.commit()

            finally:

                conexion.close()

            self.actualizar_contador()

            messagebox.showinfo(
                "Registro completado",
                f"Fotografía registrada correctamente.\n\n"
                f"Identificador: {nombre}"
            )

        except Exception as error:

            if destino and os.path.exists(destino):
                os.remove(destino)

            messagebox.showerror(
                "Error de registro",
                str(error)
            )

    # =================================================
    # CONTADOR
    # =================================================

    def actualizar_contador(self):

        conexion = conectar_db()

        try:

            cursor = conexion.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM personas"
            )

            cantidad = cursor.fetchone()[0]

        finally:

            conexion.close()

        self.contador.configure(
            text=f"ROSTROS REGISTRADOS: {cantidad}"
        )

    # =================================================
    # ANIMACION ROBOT
    # =================================================

    def animar_robot(self):

        if not self.root.winfo_exists():
            return

        if self.consultando:

            estados = [
                "🤖",
                "🧐",
                "🔎",
                "🤖"
            ]

            self.robot_estado = (
                self.robot_estado + 1
            ) % len(estados)

            self.robot.configure(
                text=estados[self.robot_estado]
            )

            self.robot_mensaje.configure(
                text="Consultando información..."
            )

        else:

            self.robot.configure(
                text="🤖"
            )

        self.root.after(
            650,
            self.animar_robot
        )

    # =================================================
    # INICIAR ANALISIS
    # =================================================

    def iniciar_analisis(self):

        if not self.imagen_seleccionada:

            messagebox.showwarning(
                "Atención",
                "Primero tenés que cargar una fotografía."
            )

            return

        if self.consultando:
            return

        conexion = conectar_db()

        try:

            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT id, nombre, imagen
                FROM personas
                ORDER BY id
                """
            )

            personas = cursor.fetchall()

        finally:

            conexion.close()

        if not personas:

            messagebox.showwarning(
                "Base de datos vacía",
                "Primero registrá fotografías autorizadas."
            )

            return

        self.consultando = True

        self.boton_analizar.configure(
            state="disabled",
            text="ANALIZANDO..."
        )

        self.boton_cargar.configure(
            state="disabled"
        )

        self.boton_registrar.configure(
            state="disabled"
        )

        self.resultado.configure(
            text="ANALIZANDO ROSTROS...",
            text_color=BLUE
        )

        self.estado_sistema.configure(
            text="● PROCESANDO",
            text_color=YELLOW
        )

        hilo = threading.Thread(
            target=self.ejecutar_comparacion,
            args=(self.imagen_seleccionada, personas),
            daemon=True
        )

        hilo.start()

    # =================================================
    # EJECUTAR COMPARACION
    # =================================================

    def ejecutar_comparacion(self, imagen, personas):

        registros = []

        for persona_id, nombre, archivo in personas:

            ruta_completa = os.path.join(
                FACES_DIR,
                archivo
            )

            registros.append(
                (
                    persona_id,
                    nombre,
                    ruta_completa
                )
            )

        try:

            resultado = comparar_rostro(
                imagen,
                registros
            )

        except Exception as error:

            resultado = {
                "estado": "error",
                "mensaje": str(error)
            }

        self.root.after(
            0,
            lambda: self.mostrar_resultado(resultado)
        )

    # =================================================
    # RESTAURAR BOTONES
    # =================================================

    def restaurar_botones(self):

        self.consultando = False

        self.boton_analizar.configure(
            state="normal",
            text="🔍  ANALIZAR ROSTRO"
        )

        self.boton_cargar.configure(
            state="normal"
        )

        self.boton_registrar.configure(
            state="normal"
        )

        self.estado_sistema.configure(
            text="● SISTEMA ACTIVO",
            text_color=GREEN
        )

    # =================================================
    # MOSTRAR RESULTADO
    # =================================================

    def mostrar_resultado(self, resultado):

        self.restaurar_botones()

        estado = resultado.get("estado")

        if estado == "coincide":

            persona = resultado["persona"]

            self.resultado.configure(
                text="PUEDE PASAR",
                text_color=GREEN
            )

            self.robot_mensaje.configure(
                text="Coincidencia biométrica detectada."
            )

            messagebox.showinfo(
                "Coincidencia detectada",
                f"PERSONA: {persona['nombre']}\n\n"
                f"Comparaciones: {resultado['comparaciones']}\n"
                f"Distancia: {persona['distancia']:.4f}\n\n"
                "Resultado orientativo. "
                "Requiere verificación humana."
            )

        elif estado == "no_coincide":

            self.resultado.configure(
                text="NO COINCIDE",
                text_color=RED
            )

            self.robot_mensaje.configure(
                text="No se encontró coincidencia suficiente."
            )

            messagebox.showwarning(
                "Sin coincidencia",
                "NO SE ENCONTRÓ UNA COINCIDENCIA SUFICIENTE.\n\n"
                "El resultado no demuestra que la persona "
                "no esté registrada."
            )

        else:

            self.resultado.configure(
                text="ERROR DE ANALISIS",
                text_color=YELLOW
            )

            self.robot_mensaje.configure(
                text="No pude completar el análisis."
            )

            errores = resultado.get(
                "errores",
                []
            )

            detalle = resultado.get(
                "mensaje",
                "Ocurrió un error durante la comparación."
            )

            if errores:
                detalle += "\n\n" + "\n".join(errores[:5])

            messagebox.showerror(
                "Error de análisis",
                detalle
            )

    # =================================================
    # CERRAR APLICACION
    # =================================================

    def cerrar_aplicacion(self):

        self.consultando = False

        self.root.destroy()


# =====================================================
# EJECUTAR PROGRAMA
# =====================================================

if __name__ == "__main__":

    ventana = ctk.CTk()

    aplicacion = AnalizadorRostro(ventana)

    ventana.mainloop()

