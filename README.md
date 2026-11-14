# Grupo 1 — Laboratorio de Física

Este proyecto implementa el sistema completo de medición de la velocidad del sonido a través del fenómeno de resonancia acústica en columnas de aire (tubos con agua) utilizando un micrófono, procesamiento de señales con la Transformada Rápida de Fourier (FFT) y una interfaz gráfica visual interactiva en Python.

## Interfaz y procedimiento

1. **Captura y análisis FFT**: selecciona tubo uniforme o botella y completa sus medidas. Captura audio del micrófono, carga un WAV o ingresa una frecuencia manual.
2. **Cálculos y gráficas**: revisa fórmula, sustitución, velocidad, frecuencia teórica y error. Pulsa **Registrar esta medición** después de comprobar los datos. Cambiar las dimensiones recalcula la vista, sin modificar mediciones anteriores.
3. **Tabla de Resultados experimentales**: consulta los dos modelos, elimina filas y exporta a CSV. La tabla tiene desplazamiento vertical y horizontal. El CSV puede abrirse con Excel; no es un archivo `.xlsx`.

## Modelos y unidades

Las longitudes se ingresan en **cm** y los volúmenes en **mL**. Los cálculos usan unidades SI:

- Longitud en metros = longitud en cm / 100.
- Volumen en m³ = volumen en mL × 10⁻⁶.
- Frecuencia en Hz, área en m² y velocidad en m/s.

### Tubo uniforme abierto arriba y cerrado por el agua

Mide L desde la superficie del agua hasta la abertura, no la altura total del tubo.

Sin diámetro ingresado se conserva el modelo ideal:

$$v = 4Lf_1, \qquad f_1 = \frac{343}{4L}$$

Con diámetro interior D positivo se usa:

$$r = D/2, \quad L_{ef} \approx L + 0.61r, \quad v \approx 4f_1L_{ef}$$

$$f_{teórica} \approx \frac{343}{4(L+0.61r)}$$

La corrección 0.61r es aproximada para una abertura sin reborde.
Ejemplo ideal: L=20 cm y f=425 Hz dan 340 m/s.
Con esos mismos datos y D=4 cm: r=0.02 m, Lef=0.2122 m y v=360.74 m/s.

### Botella como resonador de Helmholtz

Ingresa diámetro interior D del cuello, longitud física ℓ del cuello, capacidad del cuerpo y agua añadida.
La capacidad corresponde a la cavidad **hasta la base del cuello, excluyendo el cuello**;
no uses automáticamente la capacidad comercial hasta la boca. El agua debe quedar debajo del cuello.

$$V = V_{cuerpo} - V_{agua}, \quad r = D/2, \quad A = \pi r^2$$

$$L_{ef} \approx \ell + 1.46r$$

$$v = 2\pi f_H \sqrt{\frac{VL_{ef}}{A}}$$

$$f_{H,teórica} = \frac{343}{2\pi}\sqrt{\frac{A}{VL_{ef}}}$$

La raíz incluye toda la fracción. La corrección 1.46r es la aproximación adoptada;
la geometría real de los extremos puede requerir otra corrección. Este modelo supone
una cavidad y un cuello bien definidos y dimensiones pequeñas frente a la longitud de onda.
No aplica a cualquier forma de botella ni a la vibración del material al golpearla.

El agua puede ser cero, pero debe ser menor que la capacidad del cuerpo.
Ejemplo de unidades: D=2.8 cm, ℓ=3.2 cm, cuerpo=600 mL y agua=200 mL
producen V=0.0004 m³ y Lef=0.05244 m.

### **2. Herramientas Utilizadas (Sección 5)**

| Herramienta | ¿Para qué la utilizamos? |
|-------------|---------------------------|
| **NumPy** | Realizar los cálculos matemáticos de la fórmula. |
| **SciPy** | Analizar frecuencias mediante FFT y detectar picos automáticamente. |
| **Matplotlib** | Crear las gráficas del sonido (espectro FFT y comparativa al variar el agua). |
| **SoundDevice** | Capturar el audio en tiempo real mediante el micrófono. |

---

### **3. Ejecución del Proyecto**

#### **Modo Interfaz Gráfica Visual (Recomendado):**
Abre una terminal en la carpeta del proyecto y ejecuta:
```bash
python main.py
```
*(O haz doble clic en `iniciar_laboratorio.bat` en Windows).*

#### **¿Qué muestra la Interfaz Gráfica?**

1. **Entrada de la Columna de Aire (L):** Permite ingresar la longitud medida con regla (en cm o metros).
2. **Captura de Sonido:** Botón para grabar el audio del micrófono durante 1.5 segundos mientras se produce el sonido en el tubo, o cargar un archivo WAV, o ingresar una frecuencia manual.
3. **Recuadro de Cálculos Físicos en Pantalla:**
   - Muestra la fórmula: $v = 4 \cdot L \cdot f_1$
   - Muestra la sustitución paso a paso: $v = 4 \cdot (L\text{ m}) \cdot (f_1\text{ Hz})$
   - Muestra el resultado: $v = \dots\text{ m/s}$
   - Muestra la comparación con el valor teórico de $343\text{ m/s}$, el error porcentual y el porcentaje de precisión.
4. **Gráficas de Matplotlib:**
   - **Gráfica 1:** Espectro de frecuencias por FFT, identificando con un marcador rojo el pico de resonancia fundamental $f_1$.
   - **Gráfica 2:** Comparativa de cómo cambia la frecuencia al modificar el nivel de agua (curva teórica vs mediciones registradas).
5. **Tabla de Resultados:** Registro ordenado de cada medición para comparar los resultados al cambiar la cantidad de agua, con opción de exportar a CSV/Excel.

---

## Consola y simulaciones

La CLI conserva el modelo ideal de tubo:

```powershell
.\.venv\Scripts\python.exe cli.py --length-cm 20 --freq-hz 425
```

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover tests
```