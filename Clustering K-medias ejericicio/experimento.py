# Ejercicio 1: separar los blobs y volver a elegir k.
# Ejecutar después de la notebook original. Se regeneran los datos para no
# reutilizar X de la segmentación de ladybug.png.
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Circle
import sklearn
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score
from IPython.display import display, Markdown

ENTREGA = Path('Clustering K-medias ejericicio')
FIGURAS = ENTREGA / 'figuras'
FIGURAS.mkdir(parents=True, exist_ok=True)
EN_COLAB = 'google.colab' in sys.modules
plt.rcParams.update({'font.size': 11, 'axes.titlesize': 13,
                     'axes.labelsize': 11, 'xtick.labelsize': 10,
                     'ytick.labelsize': 10, 'figure.facecolor': 'white'})

# Única variable experimental: las coordenadas de los cinco centros.
centros_originales = np.array([[0.2, 2.3], [-1.5, 2.3], [-2.8, 1.8],
                              [-2.8, 2.8], [-2.8, 1.3]])
centros_separados = np.array([[0.0, 4.0], [3.8, 1.2], [2.4, -3.2],
                            [-2.4, -3.2], [-3.8, 1.2]])
blob_std = np.array([0.4, 0.3, 0.1, 0.1, 0.1])
resultados = {}

# Primero los datos originales; después, los centros separados.
for nombre, blob_centers, codo_visual in [
    ('original', centros_originales, 4),
    ('modificado', centros_separados, 5)
]:
    X, y = make_blobs(n_samples=2000, centers=blob_centers,
                     cluster_std=blob_std, random_state=7)
    X_blobs = X.copy()
    k = 5
    kmeans = KMeans(n_clusters=k, random_state=42,
                    init='k-means++', n_init='auto')
    y_pred = kmeans.fit_predict(X_blobs)
    # Se conserva el bucle y sus argumentos tal como están en la fuente.
    kmeans_per_k = [KMeans(n_clusters=k, random_state=42).fit(X_blobs)
                    for k in range(1, 10)]
    inertias = [model.inertia_ for model in kmeans_per_k]
    silhouette_scores = [silhouette_score(X_blobs, model.labels_)
                         for model in kmeans_per_k[1:]]
    assert X_blobs.shape == (2000, 2) and blob_centers.shape == (5, 2)
    assert np.array_equal(np.bincount(y), np.full(5, 400))
    assert all(b <= a + 1e-8 for a, b in zip(inertias, inertias[1:]))
    resultados[nombre] = dict(
        X=X_blobs, y=y.copy(), centros=blob_centers.copy(), modelo=kmeans,
        modelos=kmeans_per_k, inercias=inertias, siluetas=silhouette_scores,
        codo_visual=codo_visual, k_silueta=int(np.argmax(silhouette_scores)+2),
        sha256_X=hashlib.sha256(X_blobs.tobytes()).hexdigest())

assert resultados['original']['k_silueta'] == 4
assert resultados['modificado']['k_silueta'] == 5
# Mismos residuos gaussianos en ambos casos: sólo se trasladaron los centros.
a, b = resultados['original'], resultados['modificado']
assert np.array_equal(a['y'], b['y'])
assert np.allclose(a['X']-a['centros'][a['y']], b['X']-b['centros'][b['y']])
assert a['modelo'].get_params() == b['modelo'].get_params()

cmap = ListedColormap(['#dbeafe', '#ffedd5', '#dcfce7', '#f3e8ff', '#ffe4e6'])
def dibujar(ax, tipo, nombre):
    r = resultados[nombre]
    X, centros = r['X'], r['centros']
    etiqueta = 'Original' if nombre == 'original' else 'Centros separados'
    if tipo in ('scatter', 'voronoi'):
        if tipo == 'voronoi':
            mins, maxs = X.min(axis=0)-0.3, X.max(axis=0)+0.3
            xx, yy = np.meshgrid(np.linspace(mins[0],maxs[0],500),
                                 np.linspace(mins[1],maxs[1],500))
            zz = r['modelo'].predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
            ax.contourf(xx, yy, zz, levels=np.arange(-0.5,5.5), cmap=cmap)
            ax.contour(xx, yy, zz, levels=np.arange(0.5,4.5),
                       colors='#64748b', linewidths=0.7)
            marcas = r['modelo'].cluster_centers_
            ax.scatter(*marcas.T, s=90, marker='X', c='#b91c1c',
                       edgecolors='white', zorder=4, label='Centroides ajustados')
        else:
            for i, (centro, std) in enumerate(zip(centros, blob_std),1):
                ax.add_patch(Circle(centro, std, fill=False, color='#dc2626', lw=1.2))
                ax.annotate(str(i), centro, xytext=(6,7), textcoords='offset points',
                            color='#b91c1c', fontweight='bold')
            ax.scatter(*centros.T, s=48, marker='+', c='#b91c1c',
                       zorder=4, label='Centros; círculos = 1σ')
        ax.scatter(*X.T, c='#111827', s=2, alpha=0.65, linewidths=0)
        ax.set(xlabel='$x_1$', ylabel='$x_2$', aspect='equal')
        ax.legend(fontsize=8, loc='best')
        ax.set_title(f'{etiqueta} · '+('2000 puntos' if tipo=='scatter' else 'Voronoi, k = 5'))
    elif tipo == 'codo':
        ax.plot(range(1,10), r['inercias'], 'o-', color='#1d4ed8', ms=5)
        kk = r['codo_visual']
        ax.scatter(kk,r['inercias'][kk-1], s=105, facecolors='none',
                   edgecolors='#dc2626', linewidths=2, zorder=4)
        ax.set(xlabel='Número de grupos k', ylabel='Inercia J', xticks=range(1,10),
               ylim=(0,None), title=f'{etiqueta} · codo visual en k = {kk}')
        # El acercamiento permite ver las mejoras marginales cerca de k = 5.
        ins = ax.inset_axes([0.51,0.43,0.46,0.49])
        ins.plot(range(3,10),r['inercias'][2:],'o-',color='#1d4ed8',ms=3)
        ins.axvline(kk,color='#dc2626',ls='--',lw=1)
        ins.set(xticks=[3,5,7,9], title='Detalle: k = 3…9')
        ins.tick_params(labelsize=7)
        ins.title.set_fontsize(8)
        ins.grid(alpha=.2)
        ax.grid(alpha=.2)
    else:
        ax.plot(range(2,10),r['siluetas'],'o-',color='#047857',ms=5)
        kk = r['k_silueta']
        ss = r['siluetas'][kk-2]
        ax.scatter(kk,ss,s=95,c='#dc2626',zorder=4)
        ax.annotate(f'Máximo: k = {kk}\nS = {ss:.4f}', (kk,ss),
                    xytext=(12,-38),textcoords='offset points',fontsize=9)
        ax.set(xlabel='Número de grupos k',ylabel='Silueta media',
               xticks=range(2,10),ylim=(0.4,1.0),
               title=f'{etiqueta} · máximo de silueta en k = {kk}')
        ax.grid(alpha=.2)

for tipo in ['scatter','voronoi','codo','silueta']:
    fig, axes = plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
    for ax, nombre in zip(axes,['original','modificado']): dibujar(ax,tipo,nombre)
    fig.savefig(FIGURAS/f'comparacion_{tipo}.png',dpi=180)
    plt.show()
    for nombre in ['original','modificado']:
        fig, ax = plt.subplots(figsize=(7,4.6),layout='constrained')
        dibujar(ax,tipo,nombre)
        fig.savefig(FIGURAS/f'{nombre}_{tipo}.png',dpi=180)
        plt.close(fig)

filas = []
for nombre,r in resultados.items():
    for k in range(1,10):
        filas.append(dict(escenario=nombre,k=k,inercia=r['inercias'][k-1],
                          silueta='' if k==1 else r['siluetas'][k-2]))
with (ENTREGA/'resultados.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['escenario','k','inercia','silueta'])
    w.writeheader(); w.writerows(filas)
resumen = dict(
    ejecutado_utc=datetime.now(timezone.utc).isoformat(), entorno='Google Colab' if EN_COLAB else 'Local',
    python=platform.python_version(), numpy=np.__version__, sklearn=sklearn.__version__,
    matplotlib=matplotlib.__version__, n_samples=2000, random_state_blobs=7,
    std=blob_std.tolist(), parametros_kmeans=resultados['original']['modelo'].get_params(),
    escenarios={nombre: {key: val for key,val in r.items()
        if key in ['inercias','siluetas','codo_visual','k_silueta','sha256_X']}
        | {'centros':r['centros'].tolist(), 'inercia_primer_kmeans':r['modelo'].inertia_}
        for nombre,r in resultados.items()})
(ENTREGA/'metricas.json').write_text(json.dumps(resumen,indent=2,ensure_ascii=False),encoding='utf-8')

orig, nuevo = resultados['original'], resultados['modificado']
def J(r,k): return r['inercias'][k-1]
def S(r,k): return r['siluetas'][k-2]
def mejora(r,k): return 100*(J(r,k)-J(r,k+1))/J(r,k)
reporte = f'''# Clustering K-medias ejericicio

## Ejercicio 1: separar los blobs y volver a elegir k

Usé una copia de `01 K-medias.ipynb`. Primero ejecuté las celdas originales y después repetí el experimento moviendo únicamente los centros. Conservé 2000 puntos, `random_state=7`, los cinco `std` y los mismos parámetros de KMeans. El bucle prueba k = 1,…,9. La silueta se calcula sobre todos los puntos para k = 2,…,9.

## Lo que observé

En los datos originales marcaría el codo en **k = 4**. La inercia baja de {J(orig,3):.3f} con k = 3 a {J(orig,4):.3f} con k = 4. Pasar de 4 a 5 sólo la reduce {mejora(orig,4):.2f} %. La silueta también prefiere **k = 4**, con {S(orig,4):.4f}, frente a {S(orig,5):.4f} en k = 5. Aunque se generaron cinco centros, eso no obliga a que los criterios elijan cinco grupos. En particular, los dos blobs inferiores de la izquierda están separados por sólo 0.5 unidades y pueden agruparse juntos con una penalización pequeña de inercia. No significa que los tres blobs izquierdos deban fusionarse en un único grupo.

Con los centros separados, el codo visual y la silueta coinciden en **k = 5**. La inercia pasa de {J(nuevo,4):.3f} en k = 4 a {J(nuevo,5):.3f} en k = 5: una reducción del {mejora(nuevo,4):.2f} %. De 5 a 6 sólo mejora {mejora(nuevo,5):.2f} %. La silueta alcanza {S(nuevo,5):.4f} en k = 5 y baja a {S(nuevo,6):.4f} en k = 6. A partir de cinco grupos, el modelo empieza a dividir nubes que ya están separadas.

Si el codo siguiera en 4, alejaría el par de centros más cercano respecto a sus desviaciones. Aumentar `std` sin alejarlos empeoraría la separación. El codo es una lectura visual de la curva; no es una regla matemática única. La inercia por sí sola siempre favorece más grupos.

## Inercias solicitadas

| Escenario | J(k = 3) | J(k = 5) | J(k = 8) | Codo visual | Máximo de silueta |
|---|---:|---:|---:|---:|---:|
| Original | {J(orig,3):.6f} | {J(orig,5):.6f} | {J(orig,8):.6f} | 4 | 4 ({S(orig,4):.6f}) |
| Modificado | {J(nuevo,3):.6f} | {J(nuevo,5):.6f} | {J(nuevo,8):.6f} | 5 | 5 ({S(nuevo,5):.6f}) |

Estas inercias pertenecen al mismo bucle `kmeans_per_k` en ambos escenarios. En la fuente, otra celda reasigna `kmeans` usando `good_init`; por eso el valor de esa variable no siempre corresponde al primer modelo. Aquí el primer KMeans y el modelo del bucle para k = 5 usan los mismos parámetros efectivos.

## Centros y desviaciones

| Blob | Centro original | Centro modificado | std conservado |
|---|---|---|---:|
| 1 | (0.2, 2.3) | (0.0, 4.0) | 0.4 |
| 2 | (-1.5, 2.3) | (3.8, 1.2) | 0.3 |
| 3 | (-2.8, 1.8) | (2.4, -3.2) | 0.1 |
| 4 | (-2.8, 2.8) | (-2.4, -3.2) | 0.1 |
| 5 | (-2.8, 1.3) | (-3.8, 1.2) | 0.1 |

Los círculos rojos del scatter representan una desviación estándar; no son límites de los blobs. Hay 400 puntos por nube. El esquema siguiente es aproximado; las posiciones exactas están en la tabla.

```text
Original                       Modificado
 y                              y
2.8   4 (0.1)                   4           1 (0.4)
2.3             2 (.3)  1 (.4)   1.2  5 (.1)       2 (.3)
1.8   3 (0.1)                  -3.2     4 (.1)  3 (.1)
1.3   5 (0.1)                      -3.8 -2.4  0  2.4 3.8 → x
     -2.8     -1.5     0.2 → x
```

## Comparación antes y después

### Scatter
![Scatter original y modificado](figuras/comparacion_scatter.png)

### Voronoi con k = 5
![Voronoi original y modificado](figuras/comparacion_voronoi.png)

### Codo
![Codo original y modificado](figuras/comparacion_codo.png)

### Silueta
![Silueta original y modificada](figuras/comparacion_silueta.png)

Las gráficas comparativas muestran todos los valores y amplían k = 3,…,9 en el codo. Las figuras iniciales de la notebook conservan los límites y la flecha fija de la fuente; esa flecha no calcula el codo. Los ocho PNG individuales están en `figuras/`.

## Reproducibilidad y ejecución

- Entorno de esta corrida: **{resumen['entorno']}**.
- Python {resumen['python']}; NumPy {resumen['numpy']}; scikit-learn {resumen['sklearn']}; Matplotlib {resumen['matplotlib']}.
- Fecha UTC de ejecución: {resumen['ejecutado_utc']}.
- La notebook conserva las celdas originales y añade esta comparación después de la sección de la imagen. Regenera `X` desde `make_blobs` para evitar usar los píxeles de la catarina.
- `metricas.json` incluye parámetros, centros, versiones y huellas de los datos. `resultados.csv` contiene las 18 inercias y 16 siluetas.
- Las aserciones comprueban 2000 puntos, 5 centros, 400 muestras por nube, residuos gaussianos iguales y parámetros iguales entre escenarios.
- La captura del entorno se entrega en `evidencias/`. La notebook `.ipynb` conserva las salidas ejecutadas.

## Fuente

[Enunciado del ejercicio](https://github.com/victoruccetina/inteligencia-artificial/blob/main/Clustering%20K-medias/Ejercicios/ejercicio-01.md) · [Notebook de referencia](https://github.com/victoruccetina/inteligencia-artificial/blob/main/Clustering%20K-medias/Notebooks/01%20K-medias.ipynb).
'''
(ENTREGA/'README.md').write_text(reporte,encoding='utf-8')
display(Markdown(reporte.split('## Comparación antes y después')[0]))
print('ENTORNO:',resumen['entorno'],'| scikit-learn',sklearn.__version__)
print('VALIDACIÓN: 2 escenarios; 2000 puntos; 5 centros; parámetros idénticos.')
print('RESULTADO: original k=4; separado k=5; silueta máxima =',f'{S(nuevo,5):.6f}')
print('Archivos guardados en:',ENTREGA.resolve())
if EN_COLAB:
    archive = shutil.make_archive('Clustering K-medias ejericicio', 'zip', ENTREGA)
    from google.colab import files
    files.download(archive)
