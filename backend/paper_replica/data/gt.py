"""Decodificacion del ground truth de DIVA-HisDB.

Portado de BibDataset2.genMask del repo oficial axelden/Few-shot-DIA-WACV2023.
La clase se codifica en bits del canal azul; el bit menos significativo marca
pixeles de frontera que el benchmark trata como fondo.

Indices de clase: 0=fondo, 1=comment, 2=decoration, 3=text.

Codigos pares observados en los datos: 2, 4, 6, 8, 10, 12 y 14. El 14
(=8+4+2, solapamiento de las tres clases) no lo contempla el codigo oficial,
asi que cae a fondo por omision. Se replica ese comportamiento a proposito:
pesa ~0.002 % de los pixeles y solo aparece en CS18 y en una pagina de CS863.
"""

import numpy as np
from skimage.morphology import dilation, disk


def decodificar_gt_diva(gt_rgb: np.ndarray, dilatar: bool = True) -> np.ndarray:
    azul = gt_rgb[:, :, 2]
    rojo = gt_rgb[:, :, 0]

    mascara = np.zeros(azul.shape, dtype=np.int64)

    fondo = ((azul % 2) == 1) | (rojo == 128)
    comment = azul == 2
    decoration = (azul == 4) | (azul == 6) | (azul == 12)
    text = (azul == 8) | (azul == 10)

    mascara[decoration] = 2
    mascara[comment] = 1
    mascara[text] = 3
    mascara[fondo] = 0

    if dilatar:
        # Nota: dilatar una imagen de etiquetas toma el maximo local, asi que
        # la clase de indice mayor (text=3) se expande sobre las menores.
        # Es el comportamiento del codigo oficial; se replica a proposito.
        mascara = dilation(mascara, disk(1))

    return mascara.astype(np.int64)
