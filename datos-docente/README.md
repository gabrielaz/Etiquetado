# Datos enviados por el docente — issue #1

Imágenes adjuntas por `gabrielaz` (dueño del repo) en
[issue #1 — "Aplicar tu replicacion del paper a los datos que te envio"](https://github.com/gabrielaz/Etiquetado/issues/1),
para aplicarles la réplica de De Nardin et al. (WACV 2024) implementada en
`colab/entrenar_segmentador_layout.ipynb`.

## Archivos

| Archivo | Dimensiones | Peso | MD5 | Origen |
|---|---|---|---|---|
| `train/train_1.jpg` | 2808×3952 | 3.4 MB | `0d312a7998adaba70da0f217d812e7a8` | cuerpo del issue, adjunto 1 |
| `train/train_2.jpg` | 2808×3952 | 3.1 MB | `5627de726fbea92fa7db31fd2d6f2dac` | cuerpo del issue, adjunto 2 |
| `train/train_3.jpg` | 2656×3376 | 3.1 MB | `826e2e4e2bdfa1baccd2548031b79b38` | cuerpo del issue, adjunto 3 |
| `test/test_1.jpg` | 2864×3880 | 3.2 MB | `a819870d1bc6dd07ccc07dd054eeb0a7` | comentario del issue |

El cuerpo del issue son las de **train**; el comentario ("esos serian para train... aqui te
mando los archivos para test") son las de **test**.

## Cómo se descargaron

Los adjuntos de GitHub (`user-attachments`) requieren autenticación — sin token devuelven
`Not Found` en 9 bytes:

```bash
curl -sL -H "Authorization: token $(gh auth token)" \
  -o train/train_1.jpg "https://github.com/user-attachments/assets/<uuid>"
```

UUIDs de los adjuntos:

- train_1 — `9e9f59fc-ced7-476b-98a4-759f4b53dd4f`
- train_2 — `f8c74305-9185-4791-9ed8-6a040ec5cfc5`
- train_3 — `b72f5a23-97b0-4244-9ddc-f957d55fc6b9`
- test_1 — `265fdde2-9b08-4b54-a1fc-f0315df3fc0a`

## Hallazgos al inspeccionar los adjuntos

### 1. Los 3 adjuntos de "test" son el mismo archivo

El comentario del issue trae 3 imágenes, pero los tres UUIDs devuelven bytes idénticos
(mismo MD5 `a819870d1bc6dd07ccc07dd054eeb0a7`):

- `265fdde2-9b08-4b54-a1fc-f0315df3fc0a`
- `e29cce0d-4fd0-45b7-b4d5-15c933790548`
- `8e40374a-a021-4014-8d3a-2978110f12c3`

Se conservó una sola copia (`test/test_1.jpg`). **Hay 1 página de test, no 3.** Falta
preguntarle al docente si tenía otras dos distintas.

### 2. No vino ground truth

Las 4 imágenes son JPG crudos, sin máscaras ni anotaciones. El F1 del paper se calcula
contra GT pixel-precise anotado por un experto, así que el GT se construye en este proyecto
(ver `backend/scripts/build_gt_pixel.py`) — no es el GT oficial del dataset.

### 3. Correspondencia con manuscritos — inferida, no confirmada

El paper entrena one-shot con **1 página por manuscrito** (3 manuscritos = 3 páginas). Las 3
imágenes de train encajan con ese setup, pero eso es una **inferencia** a partir de que
tienen dimensiones y metadatos distintos entre sí:

- `train_1` — 2808×3952, sin EXIF
- `train_2` — 2808×3952, EXIF Canon EOS 5D Mark II (2012)
- `train_3` — 2656×3376, EXIF con datos TIFF/LZW

El docente no dijo a qué manuscrito pertenece cada una, ni a cuál pertenece la de test
(2864×3880, que no coincide con ninguna de las tres). Por eso los archivos se llaman
`train_N` / `test_N` y no `bookN`.

## Relación con el dataset del paper

Son manuscritos árabes con texto principal + marginalia densa, o sea el mismo dominio que el
dataset de Bukhari et al. (2012) que usa el paper (32 páginas de 3 manuscritos). No está
confirmado que sean literalmente páginas de ese dataset; el dataset no tiene descarga
pública directa conocida.
