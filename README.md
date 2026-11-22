# Choco Lab · Laboratorio matemático

Choco Lab reúne álgebra lineal, métodos numéricos y temas complementarios en una aplicación web local. Python realiza los cálculos y el navegador muestra las entradas, los pasos y sus comprobaciones.

## Cómo abrir (Windows)

1. Extrae todo el contenido del ZIP en una carpeta.
2. Instala Python 3.10 o superior; marca la casilla **Add Python to PATH** si es necesario.
3. Haz doble clic en **`INICIAR_CHOCOLAB.bat`**.
4. El archivo BAT comprueba las dependencias, intenta instalarlas si faltan y abre el navegador en `http://127.0.0.1:5000`.
5. En la portada, elige **Álgebra lineal**, **Métodos numéricos** o **Temas complementarios**. Mantén abierta la ventana negra mientras trabajas. Para detener la aplicación, cierra esa ventana o presiona `Ctrl+C`.

### Opción manual en VS Code

Abre una terminal en la carpeta del proyecto y ejecuta:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000` en Chrome o Edge. No necesitas instalar Node.js para ejecutar la aplicación.

## Álgebra lineal

Los cuatro módulos se abren con el editor de datos a todo el ancho. Puedes escribir por casillas o pegar un bloque desde una hoja de cálculo. Las columnas se separan con tabulaciones o espacios, y las filas con saltos de línea. **Opciones de vista** cambia las coordenadas y alterna entre fracciones y decimales.

| Módulo | Ingreso del ejercicio | Desarrollo y comprobación |
| --- | --- | --- |
| Sistemas lineales | Matriz aumentada o ecuaciones. También admite factorización de A sin b. | Operaciones sobre filas, factores triangulares o sustituciones. Comprueba Ax, la familia paramétrica o la fila contradictoria. |
| Operaciones matriciales y vectoriales | Crea objetos con nombre y escribe una expresión como `A(u+v)`. | Inspecciona los operandos y pulsa una entrada del resultado para ver su cálculo. Las expresiones se contrastan con un segundo evaluador y la inversa se comprueba en los dos órdenes. |
| Combinaciones lineales | Selecciona objetivo y generadores o analiza la dependencia del conjunto. | Sigue la reducción de los coeficientes y comprueba los pesos mediante el vector reconstruido o una contradicción. |
| Determinantes | Elige el orden de A y uno de los métodos disponibles. | Recorre diagonales, menores u operaciones de eliminación y compara los determinantes obtenidos por distintos métodos. |

Después del cálculo, usa **Anterior**, **Siguiente** o el selector de pasos. **Verificación** lleva a la comprobación y **Descargar TXT** guarda el procedimiento.

## Métodos numéricos

| Familia | Métodos |
| --- | --- |
| Métodos cerrados | Bisección y regla falsa |
| Métodos abiertos | Newton-Raphson y secante |
| Métodos iterativos para sistemas lineales | Jacobi y Gauss-Seidel |

### Uso de bisección

- Escribe una función de `x`, por ejemplo `x^4-5x^3+0.5x^2-11x+10` o `sin(x)`.
- Pulsa **Graficar y buscar raíces**. El programa explora el rango indicado (inicialmente `-10, 10`).
- En modo **Automático**, elige una raíz candidata A, B, C...; el programa propone un intervalo. En modo **Manual**, introduce `a` y `b`, o haz clic dos veces sobre la gráfica (primero `a` y luego `b`).
- Pulsa **Resolver por Bisección**. Se muestra la raíz aproximada, el **residuo absoluto `|f(c)|`**, las iteraciones y la tabla.
- Haz clic en cualquier fila o usa **Anterior / Siguiente** para ver el intervalo `a`, `b`, el punto `c` y su valor en la gráfica.
- **CSV** descarga la tabla para abrirla en Excel.

## Editor matemático y funcionamiento sin Internet

El **teclado matemático propio** incluido en la interfaz funciona sin Internet (123, f(x), ABC, #&). El editor visual enriquecido **MathLive** primero busca una copia local y, si no existe, intenta cargarlo desde un CDN; sin red se mantiene el campo de texto y el teclado propio. Si tienes Node.js y npm, puedes ejecutar **`PREPARAR_MATHLIVE_OFFLINE.bat` una sola vez con Internet** para descargar MathLive y copiarlo a `static/vendor`, junto con sus recursos; después el editor visual también funcionará sin Internet. La **gráfica Plotly está incluida localmente** en `static/vendor`.

El sistema acepta `x`, números, `+`, `-`, `*`, `/`, `^`, paréntesis, multiplicación implícita `2x`, `sin`, `cos`, `tan`, `sqrt`, `abs`, `ln`, `log`, `log10`, `exp`, `pi`, `e` y algunas funciones trigonométricas inversas. El parser propio restringe la expresión a operaciones y funciones admitidas, sin ejecutar texto ingresado por el usuario.

## Precisión y limitaciones matemáticas

- **Bisección** es un método cerrado: requiere una función continua en `[a, b]` con signos opuestos, salvo que un extremo sea ya una raíz exacta.
- Por defecto utiliza **precisión `0.0001` para el residuo absoluto `|f(c)|`**, exactamente como en el Excel utilizado en clase. En cada iteración, la columna **Error** es `abs(f(c))` y el método se detiene cuando `|f(c)| <= 0.0001` (o la tolerancia que indique el usuario).
- **Prueba de referencia:** para `f(x) = x^4 - 5x^3 + 0.5x^2 - 11x + 10`, el intervalo `[0.6, 1]` requiere **15 iteraciones** y `[5, 5.4]` requiere **19 iteraciones**, con tolerancia `0.0001`.
- `|f(c)|` mide el residuo de la ecuación, **no** es una garantía de que la distancia entre `c` y una raíz sea inferior a `0.0001`. La cota `(b-a)/2` sigue siendo un dato matemático disponible internamente, pero **no se usa para detener las iteraciones**.
- La búsqueda automática explora un **rango finito y una malla numérica**. Identifica candidatos por cambio de signo y valores muestreados que sean cero; **no garantiza descubrir todas las raíces**, especialmente si están muy próximas o solo rozan el eje X.
- El programa valida continuidad mediante SymPy antes de intentar Bisección. Las funciones con discontinuidades, asíntotas o expresiones no válidas deben utilizarse en un intervalo de continuidad.
- En candidatos separados se proponen intervalos alrededor de 0.4 unidades de anchura *solo si* conservan signos opuestos, continuidad y no se aproximan excesivamente a otro candidato. Si no, se conserva el intervalo estrecho detectado.

## Estructura

```text
ChocoLab/
├── app.py                       # Servidor Flask; rutas HTML y API
├── motor.py                     # Parser seguro, detección y Bisección programada a mano
├── INICIAR_CHOCOLAB.bat         # Inicio Windows
├── PREPARAR_MATHLIVE_OFFLINE.bat # Editor visual offline opcional
├── requirements.txt             # Dependencias Python
├── README.md
├── templates/index.html         # Pantalla y componentes
├── static/css/estilos.css       # Diseño responsive claro/oscuro
├── static/js/app.js             # Teclado, gráficas, estado e interacción
├── static/img/                  # Logos proporcionados por el usuario
└── static/vendor/plotly.min.js  # Motor de Plotly para uso offline
```

Los motores de álgebra están en los archivos `algebra_*.py`. Las rutas de cálculo se agrupan en `laboratorio_api.py` y `iterativos_api.py`.

## Verificación

Para repetir las pruebas en un equipo con todas las dependencias instaladas:

```powershell
python -m unittest discover -s tests -v
```

El proyecto incluye pruebas del algoritmo y de las rutas HTTP de Flask. Las rutas HTTP solo se ejecutan cuando Flask está disponible. La aplicación está pensada para ejecutarse localmente; no la expongas como servidor público sin añadir medidas propias de despliegue y seguridad.
