# **GRUPO 1 - LABORATORIO DE FÍSICA**

## **Medición de la velocidad del sonido mediante resonancia acústica y programación en Python**

Este proyecto implementa el sistema completo de medición de la velocidad del sonido a través del fenómeno de **resonancia acústica** en columnas de aire (tubos con agua) utilizando un micrófono, procesamiento de señales con la **Transformada Rápida de Fourier (FFT)** y una **interfaz gráfica visual** interactiva en Python.

---

### **1. Fórmulas Físicas Implementadas (según el documento del proyecto)**

Para un tubo abierto por un extremo y cerrado por el agua en el otro:

1. **Frecuencia Fundamental:**
   $$f_1 = \frac{v}{4L}$$

2. **Despeje de la Velocidad del Sonido:**
   $$v = 4 \cdot L \cdot f_1$$

3. **Ejemplo del Documento:**
   - Para una columna de aire $L = 20\text{ cm} = 0.20\text{ m}$ y una frecuencia fundamental $f_1 = 425\text{ Hz}$:
   $$v = 4 \cdot (0.20) \cdot (425) = 340\text{ m/s}$$
   - Valor teórico del aire a $20^\circ\text{C}$:
   $$v_{\text{teórico}} \approx 343\text{ m/s}$$
   - Comparación y cálculo de error:
   $$\text{Error} = \frac{|v_{\text{experimental}} - 343|}{343} \times 100\%$$
   $$\text{Precisión} = 100\% - \text{Error}$$

---

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

#### **Modo Consola (CLI):**
Si deseas probar directamente desde la terminal con el ejemplo del documento:
```bash
python cli.py --length-cm 20.0 --freq-hz 425.0
```
O capturando sonido real con el micrófono:
```bash
python cli.py --length-cm 20.0 --record
```

---

### **4. Pruebas Unitarias**
Para validar automáticamente que todas las fórmulas físicas, el filtrado y la FFT funcionan con exactitud matemática:
```bash
python -m unittest discover tests
```
