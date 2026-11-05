"""Render public archived Stage0 maps; no optimizer, agent or model training."""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, SymLogNorm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", choices=("sa", "analytical", "rl"), default="analytical")
    parser.add_argument("--step", type=int, choices=(0, 200, 400, 600, 800), default=800)
    parser.add_argument("--output", type=Path, default=Path("build/maps.png"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    paths = sorted((root / "data").glob("*/checkpoint_*.npz"))
    arrays = []
    for path in paths:
        with np.load(path, allow_pickle=False) as bundle:
            field = bundle["maps"]
            if field.shape != (4, 256, 256) or not np.isfinite(field).all():
                raise ValueError("expected finite four-channel 256-square maps")
            arrays.append(field)
    maxima = np.max(np.stack(arrays), axis=(0, 2, 3))
    with np.load(root / "data" / args.algorithm / f"checkpoint_{args.step:04}.npz", allow_pickle=False) as bundle:
        maps = bundle["maps"]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), layout="constrained")
    titles = ("Priority (background masked)", "Thermal proxy (not temperature)", "HPWL contribution (mm/pixel)", "Legality diagnostic")
    palettes = ("viridis", "inferno", "magma", "Reds")
    for i, ax in enumerate(axes):
        values = np.ma.masked_less(maps[i], 0) if i == 0 else maps[i]
        options = dict(cmap=palettes[i], origin="lower", interpolation="nearest")
        if i == 1:
            options["norm"] = PowerNorm(.6, vmin=0, vmax=max(float(maxima[i]), 1e-12))
        elif i == 2:
            options["norm"] = SymLogNorm(linthresh=max(float(maxima[i])*1e-3, 1e-12), vmin=0, vmax=max(float(maxima[i]), 1e-12))
        else:
            options.update(vmin=0, vmax=1 if i == 0 else max(float(maxima[i]), 1e-12))
        plot = ax.imshow(values, **options)
        ax.set_title(titles[i], fontsize=10)
        ax.set_xticks(np.arange(-.5, 256, 16), minor=True)
        ax.set_yticks(np.arange(-.5, 256, 16), minor=True)
        ax.grid(which="minor", alpha=.18)
        ax.tick_params(which="minor", length=0)
        ax.set_xlabel("pixel x")
        ax.set_ylabel("pixel y")
        fig.colorbar(plot, ax=ax, shrink=.75)
    fig.suptitle(f"Case7 | {args.algorithm} | step {args.step} | archived Stage0")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=300)
    plt.close(fig)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
