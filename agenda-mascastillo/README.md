# Agenda 2027 MasCastillo: tapa y contratapa

Formato **A4 apaisado (297 × 210 mm)** con 3 mm de sangrado, el mismo que el interior. El interior se usa tal cual: `fuente/A4_Interior_Compaginado.pdf`.

- Fondo naranja `#F7931E`. El logo es el oficial apilado del manual (dice "mas", sin tilde) y va todo en negro, como se pidió.
- Contratapa con la regla de oro, Mateo 7:12:
  - ideas 1 y 2: texto Reina-Valera 1960;
  - idea 3: la versión en voseo que pidió el cliente.
- El castillo es la ilustración vectorial original y va como textura suave.
- Tipografías: Nunito (titulares) y Nunito Sans (texto). Están en `fuentes/`.

## Archivos
- `ideas/Agenda-MasCastillo-3-ideas.svg`: un solo SVG con las 3 ideas (tapa y contratapa).
- `ideas/NN-…/Agenda-MasCastillo-NN-…-tapa-contratapa.pdf`: **PDF para la gráfica**. Página 1 tapa, página 2 contratapa, con sangrado y TrimBox. Las fuentes van incrustadas.
- `ideas/NN-…/tapa.svg` y `contratapa.svg`: para editar en Illustrator. La capa `Guias-NO-IMPRIMIR` marca el corte y el margen.
- `ideas/Agenda-MasCastillo-ideas.png` / `.pdf`: la lámina para mostrar.

## Ideas
1. **Franja:** el armado de la tapa original, con una franja negra con "AGENDA 2027". La contratapa repite la franja del otro lado y lleva el texto centrado.
2. **Logo protagonista:** naranja pleno, el logo gigante y una píldora negra con "AGENDA 2027". La contratapa es un texto grande con comillas.
3. **Castillo:** textura del castillo, el logo arriba y un "2027" gigante. La contratapa lleva el texto sobre una placa negra.

`python3 generar.py` regenera todo.
