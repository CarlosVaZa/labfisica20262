# **GRUPO 1 - LABORATORIO DE FÍSICA (TARDE)**

## **Medición de la Velocidad del Sonido mediante Resonancia Acústica y Programación en Python**

Este repositorio contiene la solución completa de software, modelos físicos, procesamiento digital de señales (DSP) e interfaz gráfica para el proyecto de laboratorio de ondas y acústica del **Grupo 1**.

El sistema permite capturar el sonido emitido por una columna de aire resonante (tubo con agua), identificar sus frecuencias naturales mediante la **Transformada Rápida de Fourier (FFT)**, realizar ajustes por regresión lineal por mínimos cuadrados para estimar experimentalmente la **velocidad del sonido en el aire**, y aplicar estos principios a herramientas del mundo real (sensor acústico de nivel de líquidos y afinador digital cromático).

---

## 📋 **Tabla de Contenido**
1. [¿De qué trata el proyecto?](#-1-de-qué-trata-el-proyecto)
2. [Fundamento Físico y Ecuaciones](#-2-fundamento-físico-y-ecuaciones)
3. [Relación con Ingeniería de Sistemas](#-3-relación-con-ingeniería-de-sistemas)
4. [Estructura del Proyecto](#-4-estructura-del-proyecto)
5. [Requisitos e Instalación](#-5-requisitos-e-instalación)
6. [Guía de Uso](#-6-guía-de-uso)
   - [Interfaz Gráfica de Usuario (GUI)](#modo-gráfico-gui)
   - [Línea de Comandos (CLI)](#modo-línea-de-comandos-cli)
7. [Guía Experimental de Laboratorio](#-7-guía-experimental-de-laboratorio)
8. [Aplicaciones Prácticas Desarrolladas](#-8-aplicaciones-prácticas-desarrolladas)
9. [Pruebas Automatizadas](#-9-pruebas-automatizadas)

---

## 🔬 **1. ¿De qué trata el proyecto?**

Al producir un sonido cerca de una columna de aire cerrada en un extremo por agua, el aire en su interior entra en resonancia acústica cuando la frecuencia excitadora coincide con una de sus frecuencias naturales.

Modificando la cantidad de agua contenida en el tubo, varía la longitud $L$ de la columna de aire y, por consiguiente, su frecuencia de resonancia fundamental $f_1$. En lugar de estimar la frecuencia auditivamente, el programa:
1. **Captura la señal acústica** en tiempo real mediante el micrófono del computador.
2. **Aplica preprocesamiento digital**: remoción de offset DC, filtro Butterworth pasa-banda y ventanado Hann para mitigar la fuga espectral (*spectral leakage*).
3. **Calcula la Transformada Rápida de Fourier (FFT)** y detecta el pico fundamental con interpolación parabólica cuadrática (resolución sub-bin $< 0.1\text{ Hz}$).
4. **Calcula la velocidad del sonido experimental** individualmente y mediante regresión lineal sobre una serie de alturas ($L$ vs $1/f$).
5. **Compara con el valor termodinámico teórico** a la temperatura del laboratorio.

---

## 📐 **2. Fundamento Físico y Ecuaciones**

### **2.1 Tubo Abierto en un Extremo y Cerrado por Agua**
En el fondo del tubo (superficie del agua), las moléculas de aire no pueden desplazarse, formando un **nodo de desplazamiento** (vientre de presión). En la abertura superior (boca del tubo), las moléculas oscilan libremente en contacto con la presión atmosférica, formando un **vientre o antinodo de desplazamiento**.

Para el modo fundamental ($n = 1$):
$$\lambda = 4 L_{eff}$$

Relacionando con la velocidad de propagación $v = \lambda \cdot f$:
$$f_1 = \frac{v}{4 L_{eff}} \implies v = 4 L_{eff} f_1$$

Para armónicos superiores impares ($n = 1, 2, 3...$):
$$f_n = (2n - 1) \frac{v}{4 L_{eff}}$$

### **2.2 Corrección de Extremo (End Correction)**
El antinodo acústico real no se localiza exactamente en el plano de la abertura física, sino a una distancia $\Delta L$ por fuera de la boca debido a la inercia de la masa de aire adyacente:
$$L_{eff} = L + \Delta L$$
$$\Delta L \approx 0.61 \cdot r$$
donde $r$ es el radio interno del tubo cilíndrico (corrección teórica de Levine & Schwinger).

### **2.3 Linealización y Regresión Lineal por Mínimos Cuadrados**
Al despejar la longitud física medida $L$:
$$L = \left(\frac{v}{4}\right) \cdot \left(\frac{1}{f_1}\right) - \Delta L$$

Definiendo las variables experimentales:
- $y = L$ (longitud de la columna de aire en metros)
- $x = \frac{1}{f_1}$ (periodo acústico fundamental en segundos)

La ecuación tiene la forma lineal $y = m x + c$:
- **Pendiente:** $m = \frac{v}{4} \implies \mathbf{v_{exp} = 4 \cdot m}$
- **Intercepto:** $c = -\Delta L \implies \mathbf{\Delta L_{exp} = -c}$

Este ajuste global cancela el sesgo sistemático del extremo del tubo y minimiza la incertidumbre aleatoria del experimento.

### **2.4 Velocidad Teórica en Función de la Temperatura**
La velocidad del sonido en aire seco depende de la temperatura termodinámica:
$$v(T) = v_0 \sqrt{1 + \frac{T}{273.15}} \approx 331.3 \sqrt{\frac{T + 273.15}{273.15}} \text{ [m/s]}$$
A $20^\circ\text{C}$, $v_{teórica} \approx 343.2\text{ m/s}$.

El error porcentual experimental se calcula como:
$$\text{Error } \% = \frac{|v_{exp} - v_{teórica}|}{v_{teórica}} \times 100\%$$

---

## 💻 **3. Relación con Ingeniería de Sistemas**

El proyecto integra de manera interdisciplinaria:
- **Programación Orientada a Objetos y Modularidad en Python**: Código desacoplado entre física, DSP, adquisición de datos y GUI.
- **Procesamiento Digital de Señales (DSP)**: Algoritmos FFT unilateral con `scipy.fft`, ventanado temporal (Hann), filtros IIR Butterworth y refinamiento sub-bin con interpolación parabólica.
- **Concurrencia y Audio Multihilo**: Adquisición asíncrona mediante buffer circular continuo (*ring buffer*) con `sounddevice` sin bloquear el hilo principal de la interfaz gráfica.
- **Modelado Estadístico y Regresión**: Ajuste lineal OLS, cálculo de coeficientes de determinación $R^2$, propagación de errores e incertidumbres estadísticas.
- **Desarrollo de Interfaces Gráficas (GUI)**: Pantalla interactiva en Tkinter y gráficos científicos embebidos en tiempo real mediante `FigureCanvasTkAgg` de Matplotlib.
- **Pruebas Automatizadas (TDD)**: Suite de pruebas unitarias (`unittest`) para verificar la física y el tratamiento de señales.

---

## 📁 **4. Estructura del Proyecto**

```text
labfisica20262/
├── README.md                      # Documentación completa del proyecto
├── requirements.txt               # Dependencias del proyecto
├── main.py                        # Lanzador unificado (GUI o CLI)
├── run_gui.py                     # Lanzador directo de la interfaz gráfica
├── cli.py                         # Interfaz interactiva de consola
│
├── core/                          # Núcleo algorítmico y matemático
│   ├── __init__.py
│   ├── physics_engine.py          # Modelos de ondas, resonancia, regresión y temperatura
│   ├── signal_processing.py       # FFT, filtros digitales, ventanado y picos
│   ├── audio_capture.py           # Adquisición de audio con buffer circular y ráfagas
│   ├── audio_generator.py         # Sintetizador de tonos, barridos y soplido simulado
│   └── data_manager.py            # Almacenamiento, exportación/importación CSV/JSON
│
├── gui/                           # Interfaz gráfica de usuario
│   ├── __init__.py
│   ├── app.py                     # Ventana principal, temas y pestañas
│   ├── styles.py                  # Paleta de colores y tipografías
│   ├── tab_realtime.py            # Pestaña 1: Captura en vivo, osciloscopio y FFT
│   ├── tab_experiment.py          # Pestaña 2: Tabla de mediciones y regresión lineal
│   ├── tab_applications.py        # Pestaña 3: Sensor de nivel de agua y afinador
│   └── tab_theory.py              # Pestaña 4: Teoría, procedimiento y calculadora
│
├── data/
│   └── sample_experiments.csv     # Dataset modelo de laboratorio precargado
│
├── tests/                         # Pruebas unitarias
│   ├── __init__.py
│   ├── test_physics.py            # Tests de fórmulas físicas y regresión
│   ├── test_signal.py             # Tests de FFT y detección de picos
│   └── test_data.py               # Tests de persistencia CSV/JSON
│
└── GRUPO 1- LAB FISICA-TARDE.md   # Documento guía original del laboratorio
```

---

## ⚙️ **5. Requisitos e Instalación**

### **Requisitos Previos**
- Python 3.10 o superior (compatible con Python 3.12).
- Micrófono o auriculares con micrófono (opcional: el sistema incluye modo simulación acústica para pruebas en aula).

### **Instalación de Dependencias**
```bash
pip install -r requirements.txt
```

Las dependencias principales son:
- `numpy`: Cálculo vectorial y matricial.
- `scipy`: Filtrado digital IIR Butterworth y detección de picos (`find_peaks`).
- `matplotlib`: Visualización de espectros, formas de onda y rectas de ajuste.
- `sounddevice`: Captura y reproducción de audio en tiempo real.
- `pandas`: Manipulación estructurada de tablas experimentales.

---

## 🚀 **6. Guía de Uso**

### **Modo Gráfico (GUI)**
Para iniciar la interfaz gráfica interactiva, ejecute:
```bash
python main.py
# o también:
python run_gui.py
```

La interfaz cuenta con cuatro pestañas especializadas:
1. **🎙️ Captura y Espectro en Vivo**:
   - Visualice la señal en el tiempo (oscilograma) y su Transformada de Fourier (FFT).
   - Botón *Iniciar Monitor en Vivo* para seguimiento continuo.
   - Botón *⚡ Capturar Ráfaga (1.5 s)* para registrar una medición limpia con filtro.
   - Botón *➕ Guardar en Experimento* para almacenar el punto en la tabla.
   - Opción *Modo Simulación (Sin Micrófono)* para practicar sin hardware.
   - Generador de tonos y barridos acústicos para excitar el tubo con altavoces.
2. **📊 Experimento y Regresión**:
   - Tabla dinámica de mediciones ($L$, $f_1$, $1/f$, $v_{puntual}$).
   - Gráfico de regresión lineal en tiempo real con línea de tendencia $L$ vs $1/f$.
   - Panel de resultados estadísticos: $v_{experimental} \pm \Delta v$, $v_{teórica}$, error porcentual, coeficiente $R^2$ y corrección de extremo experimental.
   - Botones para cargar datos de prueba, agregar puntos manuales, exportar e importar archivos CSV/JSON, y guardar gráficos en alta resolución.
3. **💡 Aplicaciones Prácticas**:
   - **Sensor Acústico de Nivel**: Estima la altura del agua en recipientes cilíndricos a partir de la resonancia acústica, con visualización gráfica del tanque y volumen en litros.
   - **Afinador Cromático Digital**: Identifica la nota musical más cercana y muestra la aguja de desviación en *cents* para afinación de instrumentos.
4. **📖 Teoría y Calculadora**:
   - Resumen teórico completo de física de ondas.
   - Calculadora teórica en vivo: predice frecuencias fundamentales y armónicos a partir de $L$, $T$ y $r$.

---

### **Modo Línea de Comandos (CLI)**
El sistema puede ejecutarse por completo desde la consola de comandos:

#### **1. Demostración Completa Automatizada:**
```bash
python main.py demo
```

#### **2. Capturar Sonido con Micrófono y Medir Resonancia:**
```bash
python main.py record --length-cm 20.0 --temp 20.0 --plot
```
*(Si no cuenta con micrófono, agregue el argumento `--simulate`)*.

#### **3. Analizar Serie Experimental con Regresión Lineal:**
```bash
python main.py analyze --temp 20.0 --radius-cm 1.5 --out grafica_regresion.png
```

#### **4. Listar Dispositivos de Audio Disponibles:**
```bash
python main.py devices
```

#### **5. Generar Barrido Senoidal por Parlantes:**
```bash
python main.py sweep --start-freq 200 --end-freq 1200 --duration 3.0
```

---

## 🧪 **7. Guía Experimental de Laboratorio**

Para llevar a cabo la toma de datos en el laboratorio con botellas o tubos cilíndricos:

1. **Alistar el material**: Tubo plástico o de vidrio transparente de sección uniforme, regla milimetrada, agua, micrófono y el computador con el software ejecutándose.
2. **Medición inicial**: Verter agua en el tubo y medir con la regla la longitud $L$ de la columna de aire (desde la superficie del agua hasta el borde superior de la boca).
3. **Colocación del sensor**: Posicionar el micrófono a unos 2 a 5 cm de la abertura del tubo.
4. **Excitación acústica**:
   - *Opción A (Soplido)*: Soplar suavemente y de manera rasante sobre la boca del tubo (como en una flauta de pan o botella).
   - *Opción B (Altavoz / Parlante)*: Acercar un pequeño altavoz emitiendo un tono o barrido continuo desde el software.
5. **Captura**: En la pestaña *Captura y Espectro*, presionar *Capturar Ráfaga*. El algoritmo detectará automáticamente el pico fundamental $f_1$.
6. **Almacenamiento**: Hacer clic en *➕ Guardar en Experimento*.
7. **Variar niveles**: Añadir más agua (o vaciarla) para cambiar la longitud $L$ y repetir el procedimiento para al menos 6 alturas distintas (por ejemplo: 12, 16, 20, 25, 30, 35 y 40 cm).
8. **Análisis de Regresión**: Pasar a la pestaña *Experimento y Regresión* para verificar la recta de regresión lineal, la velocidad experimental del sonido obtenida ($v_{exp}$) y el error porcentual respecto a la temperatura ambiente.

---

## 🌟 **8. Aplicaciones Prácticas Desarrolladas**

Siguiendo las propuestas del documento del proyecto, el software incluye:

1. **Sensor Acústico de Nivel de Líquidos en Recipientes**:
   Aprovecha la relación inversa entre el nivel de líquido y la columna de aire. Permite estimar la altura y volumen de agua en tanques y depósitos cerrados sin necesidad de boyas mecánicas ni sensores sumergidos.
2. **Afinador Digital Cromático de Instrumentos**:
   Utiliza la transformada rápida de Fourier junto con interpolación espectral para afinar guitarras, pianos y otros instrumentos musicales con exactitud de $\pm 1\text{ cent}$.
3. **Generador Acústico de Laboratorio**:
   Emite tonos y barridos senoidales precisos para investigar fenómenos de resonancia acústica y respuesta en frecuencia.

---

## 🧪 **9. Pruebas Automatizadas**

El proyecto cuenta con pruebas unitarias que validan la exactitud matemática de los modelos físicos, el procesamiento DSP y la persistencia de datos:

```bash
python -m unittest discover tests
```

Resultados esperados:
- **`test_physics.py`**: Validación de velocidad teórica $v(T)$, resonancia $f_1 = v/(4L)$, regresión lineal por mínimos cuadrados y cálculo de error.
- **`test_signal.py`**: Validación de remoción de DC, cálculo de FFT, ventanado Hann y detección de picos con interpolación parabólica.
- **`test_data.py`**: Validación de importación y exportación de archivos CSV y JSON.

---

## 👥 **Integrantes - Grupo 1**
- **Laboratorio de Física (Tarde)**
- Proyecto: *Medición de la velocidad del sonido mediante resonancia acústica y programación en Python.*
