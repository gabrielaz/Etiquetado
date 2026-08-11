"""Loop de entrenamiento de la fase 1.

Cada item del dataset es una pagina entera que se despliega en 34 parches; los
parches se procesan en micro-batches de cfg.micro_batch con acumulacion de
gradiente, de modo que el batch efectivo sea el de la pagina completa (como el
rearrange del codigo oficial) sin desbordar la T4.

Sin AMP y sin congelar BatchNorm: ver docs/replica-denardin/2026-08-10-plan-fase-1.md
"""

import copy

import torch

from paper_replica.config import Config
from paper_replica.data.dataset import DivaDataset
from paper_replica.losses import crear_ce_ponderada
from paper_replica.model import crear_modelo


def debe_cortar(epoca: int, ultima_mejora: int, cfg: Config) -> bool:
    """Early stopping del repo oficial: i - epoch_last_update > 20 and i > 50."""
    return (epoca - ultima_mejora) > cfg.patience and epoca > cfg.min_epochs


def paso_epoca(
    model, ds, loss_fn, optim, cfg: Config, device: str, entrenar_modo: bool
) -> float:
    model.train() if entrenar_modo else model.eval()
    total, n = 0.0, 0

    for idx in range(len(ds)):
        patches, masks = ds[idx]
        patches, masks = patches.to(device), masks.to(device)

        if entrenar_modo:
            optim.zero_grad()

        for i in range(0, len(patches), cfg.micro_batch):
            xb = patches[i : i + cfg.micro_batch]
            yb = masks[i : i + cfg.micro_batch]

            with torch.set_grad_enabled(entrenar_modo):
                out = model(xb)
                loss = loss_fn(out, yb)

            if entrenar_modo:
                # promedia sobre los micro-batches de la pagina
                (loss * len(xb) / len(patches)).backward()

            total += loss.item() * len(xb)
            n += len(xb)

        if entrenar_modo:
            optim.step()

    return total / n


def entrenar(
    manuscrito: str,
    cfg: Config,
    device: str = "cuda",
    max_epochs: int | None = None,
    log_cada: int = 1,
) -> dict:
    torch.manual_seed(42)

    ds_train = DivaDataset(manuscrito, "training", cfg, con_crops=True)
    ds_val = DivaDataset(manuscrito, "validation", cfg, con_crops=False)

    model = crear_modelo(cfg).to(device)
    loss_fn = crear_ce_ponderada(manuscrito, device=device)
    optim = torch.optim.Adam(
        model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
    )

    epochs = max_epochs if max_epochs is not None else cfg.epochs
    mejor_val = float("inf")
    mejor_epoca = 0
    mejor_state = copy.deepcopy(model.state_dict())
    historial = []

    for epoca in range(epochs):
        ds_train.set_epoch(epoca)

        train_loss = paso_epoca(
            model, ds_train, loss_fn, optim, cfg, device, entrenar_modo=True
        )
        val_loss = paso_epoca(
            model, ds_val, loss_fn, optim, cfg, device, entrenar_modo=False
        )

        historial.append(
            {"epoca": epoca, "train_loss": train_loss, "val_loss": val_loss}
        )

        if val_loss < mejor_val:
            mejor_val = val_loss
            mejor_epoca = epoca
            mejor_state = copy.deepcopy(model.state_dict())

        if epoca % log_cada == 0:
            print(
                f"[{manuscrito}] epoca {epoca:3d}  "
                f"train {train_loss:.4f}  val {val_loss:.4f}  "
                f"mejor {mejor_val:.4f} (ep {mejor_epoca})",
                flush=True,
            )

        if debe_cortar(epoca, mejor_epoca, cfg):
            print(f"[{manuscrito}] early stopping en epoca {epoca}", flush=True)
            break

    return {
        "mejor_epoca": mejor_epoca,
        "mejor_val_loss": mejor_val,
        "historial": historial,
        "state_dict": mejor_state,
    }
