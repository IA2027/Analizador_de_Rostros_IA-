
import os
from deepface import DeepFace


MODELO = "Facenet512"
DETECTOR = "retinaface"
METRICA = "cosine"


def validar_rostro(ruta):

    if not os.path.isfile(ruta):
        raise ValueError("No se encuentra el archivo de imagen.")

    rostros = DeepFace.extract_faces(
        img_path=ruta,
        detector_backend=DETECTOR,
        enforce_detection=True,
        align=True
    )

    if len(rostros) == 0:
        raise ValueError("No se detectó ningún rostro.")

    if len(rostros) > 1:
        raise ValueError(
            "La fotografía contiene más de un rostro. "
            "Subí una imagen con una sola persona."
        )

    return True


def comparar_rostro(imagen_consulta, registros):

    # Validar la fotografía que queremos analizar
    validar_rostro(imagen_consulta)

    mejor_coincidencia = None
    menor_distancia = float("inf")

    comparaciones_realizadas = 0
    errores = []

    for persona_id, nombre, imagen_referencia in registros:

        if not os.path.isfile(imagen_referencia):
            errores.append(f"Imagen faltante: {nombre}")
            continue

        try:

            # Validar que la referencia también tenga un solo rostro
            validar_rostro(imagen_referencia)

            resultado = DeepFace.verify(
                img1_path=imagen_consulta,
                img2_path=imagen_referencia,
                model_name=MODELO,
                detector_backend=DETECTOR,
                distance_metric=METRICA,
                enforce_detection=True,
                align=True,
                silent=True
            )

            distancia = float(resultado["distance"])
            umbral = float(resultado["threshold"])

            comparaciones_realizadas += 1

            if distancia < menor_distancia:

                menor_distancia = distancia

                mejor_coincidencia = {
                    "id": persona_id,
                    "nombre": nombre,
                    "distancia": distancia,
                    "umbral": umbral,
                    "coincide": distancia <= umbral
                }

        except Exception as error:

            errores.append(f"{nombre}: {str(error)}")

    if comparaciones_realizadas == 0:

        return {
            "estado": "error",
            "mensaje": "No fue posible comparar ninguna fotografía.",
            "errores": errores
        }

    if mejor_coincidencia and mejor_coincidencia["coincide"]:

        return {
            "estado": "coincide",
            "persona": mejor_coincidencia,
            "comparaciones": comparaciones_realizadas
        }

    return {
        "estado": "no_coincide",
        "persona": mejor_coincidencia,
        "comparaciones": comparaciones_realizadas
    }
