import sys
from pathlib import Path

import click
import tomlkit

from .term import term


def save_params(ctx: click.Context) -> None:
    """save parameters to config file

    Args:
        ctx: Click context.
    """
    cmd = ctx.info_name
    params = {k: v for k, v in ctx.params.items() if v}
    save_type = params.pop("save_config")

    try:
        config_file = Path(ctx.obj["configfile"])
    except TypeError:
        raise click.BadParameter("use `--save-config` with a specified `--config`")

    if config_file.is_file():
        term.print(f"Updating current config file at [hl]{config_file}")
        with config_file.open("r") as f:
            config = tomlkit.load(f)
    else:
        term.print(f"Staring a config file at [hl]{config_file}")
        config = tomlkit.document()

    if save_type == "explicit":
        params = {k: v for k, v in params.items() if ctx.get_parameter_source(k).value != 3}  # type: ignore

    # use readable name for input
    if "input_" in params:
        params["input"] = params.pop("input_")

    # sanitize the path's for writing to toml
    for k in ["input", "pipeline", "output"]:
        if k in params.keys():
            params[k] = str(params[k])

    config[cmd] = params  # type: ignore

    null_hints = {"extract": ["filter_count", "fastp_args"], "merge": ["fastp_args"]}
    if cmd in null_hints.keys() and save_type == "full":
        for param in null_hints[cmd]:  # type: ignore
            if param not in params.keys():
                config[cmd].add(tomlkit.comment(f"{param} ="))  # type: ignore

    with config_file.open("w") as f:
        f.write(tomlkit.dumps(config))

    term.print("Exiting...")
    ctx.exit()


def load_params(ctx: click.Context, param: str, filename: Path) -> None:
    """load parameters from config file

    Args:
        ctx: Click context.
        param: Invoked command and config table head.
        filename: Config filename.
    """
    ctx.obj = {"configfile": filename}

    if not filename or ctx.resilient_parsing:
        return

    ctx.default_map = {}
    if Path(filename).is_file():
        with Path(filename).open("r") as f:
            params = tomlkit.load(f)

        if params:
            global_params = params.pop("global", {})

            ctx.default_map = params.get(ctx.info_name, {})

            # use not shadowing name for input
            if ctx.default_map and "input" in ctx.default_map:
                ctx.default_map["input_"] = ctx.default_map.pop("input")

            # populate 'default_map' with global params
            for k, v in global_params.items():
                ctx.default_map.setdefault(k, v)  # type: ignore

        ctx.obj.update(**{"global": global_params, "config-loaded": True})

    # using default pycashier can cause unexpected behavior?
    elif Path(filename) != Path("pycashier.toml"):
        term.print(
            f"[InputError]: Specified config file ({filename}) does not exist.",
            err=True,
        )
        sys.exit(1)
