"""Genera diagramas educativos exactos; no requiere micrófono ni interfaz.

Ejecutar desde cualquier carpeta: python assets/guias/generar_guias.py
No sobrescribe imágenes existentes salvo que se indique --reemplazar.
"""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

ROOT = Path(__file__).resolve().parent
NAVY = "#12345b"
BLUE = "#155fa0"


def text(ax, x, y, value, size=14, color=NAVY, **kwargs):
    return ax.text(x, y, value, fontsize=size, color=color, va="top", **kwargs)


def arrow(ax, start, end, color=BLUE):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="<->", color=color, lw=2))


def guide(bottle=False):
    fig = plt.figure(figsize=(15, 10), dpi=150, facecolor="#f7fafc")
    fig.suptitle("Botella: resonancia de Helmholtz" if bottle else "Tubo uniforme: columna de aire con agua",
                 fontsize=24, fontweight="bold", color=NAVY, y=.96)
    diagram = fig.add_axes([.03, .28, .38, .61])
    diagram.set(xlim=(0, 10), ylim=(0, 12))
    diagram.axis("off")
    if bottle:
        outline = [(2.7,1), (7.3,1), (7.3,8), (6,9.2), (6,11), (4,11), (4,9.2), (2.7,8)]
        diagram.add_patch(Polygon(outline, closed=True, fc="#e9f3fb", ec=BLUE, lw=2))
        diagram.add_patch(Rectangle((2.72,1.02), 4.56, 3.0, fc="#7cc5e9", ec="none"))
        diagram.plot([2.7,7.3],[4.02,4.02],color=BLUE,lw=2)
        diagram.plot([4,6],[11,11],color="#f7fafc",lw=4)
        arrow(diagram, (4,11.5),(6,11.5), "#16a34a")
        text(diagram,5,12,"D interior",12,ha="center")
        arrow(diagram,(7,9.2),(7,11),"#c28512")
        text(diagram,7.4,10.5,"ℓ del\ncuello",12)
        text(diagram,5,7.5,"Volumen de aire V",14,ha="center",weight="bold")
        text(diagram,5,3.2,"Agua añadida",13,ha="center")
        diagram.plot([2,8],[9.2,9.2],ls="--",color="#64748b",lw=1)
        text(diagram,.2,.6,"Capacidad del cuerpo: hasta la base del cuello.\nEl agua debe quedar por debajo del cuello.",11)
    else:
        diagram.add_patch(Rectangle((3,1),4,9.5,fc="#e9f3fb",ec="none"))
        diagram.add_patch(Rectangle((3,1),4,3,fc="#7cc5e9",ec="none"))
        diagram.plot([3,3,7,7],[10.5,1,1,10.5],color=BLUE,lw=3)
        diagram.plot([3,7],[4,4],color=BLUE,lw=2)
        arrow(diagram,(2,4),(2,10.5))
        text(diagram,.3,7.7,"L: aire",14,weight="bold")
        arrow(diagram,(3,11.3),(7,11.3),"#16a34a")
        text(diagram,5,12,"D interior",13,ha="center")
        text(diagram,5,8.6,"Aire",18,ha="center",weight="bold")
        text(diagram,5,3,"Agua",16,ha="center")
        text(diagram,5,.5,"Fondo cerrado y abertura libre",12,ha="center")
    formulas = fig.add_axes([.44, .28, .53, .61])
    formulas.set(xlim=(0,1),ylim=(0,1))
    formulas.axis("off")
    text(formulas,0,.98,"Medidas y fórmulas",20,weight="bold")
    if bottle:
        text(formulas,0,.88,"1. Mide D y ℓ del cuello en cm.\n2. Mide la capacidad del cuerpo y el agua en mL.\n3. Obtén la frecuencia de resonancia fH con la FFT.",14,linespacing=1.7)
        text(formulas,0,.65,r"$r=D/2,\quad A=\pi r^2,\quad V=V_{cuerpo}-V_{agua}$",18)
        text(formulas,0,.53,r"$L_{ef}\approx\ell+1.46\,r$",19)
        text(formulas,0,.41,r"$f_H=\frac{v}{2\pi}\sqrt{\frac{A}{V\,L_{ef}}}\quad\Rightarrow\quad v=2\pi f_H\sqrt{\frac{V\,L_{ef}}{A}}$",21)
        text(formulas,0,.23,"El modelo relaciona el aire del cuello con el de la cavidad.\nSe despeja v de la expresión de la frecuencia de Helmholtz.",13,linespacing=1.6)
        text(formulas,0,.10,"Ejemplo: D = 2.8 cm; ℓ = 3.2 cm; cuerpo = 600 mL; agua = 200 mL.\nV = 400 mL = 0.0004 m³; Lef = 0.05244 m.",12,linespacing=1.7)
    else:
        text(formulas,0,.88,"1. Mide L desde el agua hasta la abertura.\n2. Mide el diámetro interior D, si aplicarás la corrección.\n3. Obtén la frecuencia fundamental f₁ con la FFT.",14,linespacing=1.7)
        text(formulas,0,.65,"Modelo ideal: la columna de aire equivale a un cuarto de onda.",13)
        text(formulas,0,.57,r"$\lambda_1=4L,\quad v=\lambda_1 f_1\quad\Rightarrow\quad v=4Lf_1$",21)
        text(formulas,0,.43,"Corrección aproximada de la abertura sin reborde:",14)
        text(formulas,0,.35,r"$r=D/2,\quad L_{ef}\approx L+0.61r$",20)
        text(formulas,0,.23,r"$v\approx4f_1(L+0.61r)$",23)
        text(formulas,0,.10,"Ejemplo: L = 20 cm; D = 4 cm → r = 2 cm.\nLef = 21.22 cm = 0.2122 m.",13,linespacing=1.7)
    bottom = fig.add_axes([.04,.035,.92,.18])
    bottom.set(xlim=(0,1),ylim=(0,1))
    bottom.axis("off")
    text(bottom,0,.98,"Cómo usar la guía en el programa",18,weight="bold")
    text(bottom,0,.73,"Ingresa cm y mL: el programa convierte a metros y metros cúbicos. 1 cm = 0.01 m; 1 mL = 10⁻⁶ m³.",14)
    text(bottom,0,.49,"Sopla sobre la boca, graba o carga un WAV y comprueba el pico detectado antes de registrar la medición.",14)
    text(bottom,0,.25,"El pico dominante puede ser ruido o un armónico. Evita golpear el recipiente: su vibración es otro fenómeno.",13)
    text(bottom,0,.03,"Referencia: 343 m/s a 20 °C. Las correcciones de abertura son aproximaciones que dependen de la geometría.",12)
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reemplazar", action="store_true")
    args = parser.parse_args()
    for filename,bottle in (("tubo_uniforme.png",False),("botella.png",True)):
        target = ROOT / filename
        if not target.exists() or args.reemplazar:
            fig = guide(bottle)
            fig.savefig(target, dpi=150, facecolor=fig.get_facecolor())
            plt.close(fig)
            print(target.name)
