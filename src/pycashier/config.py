from pathlib import Path

import click
import tomlkit

from ._checks import check_file_permissions
from .term import term


def save_params(ctx: click.Context) -> None:
    """save parameters to config file

    Args:
        ctx: Click context.
    """
    cmd = ctx.info_name
    all_params = {k: v for k, v in ctx.params.items() if v}
    save_type = all_params.pop("save_config")
    try:
        config_file = Path(ctx.obj["configfile"])
    except TypeError:
        raise click.BadParameter("use `--save-config` with a specified `--config`")

    if config_file.is_file():
        term.print(f"Updating current config file at [hl]{config_file}")
        try:
            with config_file.open("r") as f:
                config = tomlkit.load(f)
        except Exception as e:
            term.print(
                f"[ConfigFileError] failed to load config file: {config_file}", err=True
            )
            term.print(e, err=True)
            term.quit()

    else:
        term.print(f"Staring a config file at [hl]{config_file}")
        config = tomlkit.document()

    if save_type == "explicit":
        params = {}
        for k, v in all_params.items():
            if param_source := ctx.get_parameter_source(k):
                if param_source.value != 3:
                    params[k] = v
    else:
        params = all_params.copy()

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
        for param in null_hints[cmd]:
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

    check_file_permissions()
    config_file = Path(filename)
    if config_file.is_file():
        global_params = {}
        try:
            with config_file.open("r") as f:
                params = tomlkit.load(f)
        except Exception as e:
            term.print(
                f"[ConfigFileError] failed to load config file: {config_file}", err=True
            )
            term.print(e, err=True)
            term.quit()

        if params:
            global_params = params.pop("global", {})

            ctx.default_map = params.get(ctx.info_name, {})

            # use not shadowing name for input
            if ctx.default_map and "input" in ctx.default_map:
                ctx.default_map["input_"] = ctx.default_map.pop("input")

            # populate 'default_map' with global params
            for k, v in global_params.items():
                ctx.default_map.setdefault(k, v)  # type: ignore
        if global_params:
            ctx.obj.update(**{"global": global_params})
        ctx.obj["config-loaded"] = True

    # using default pycashier can cause unexpected behavior?
    elif config_file != Path("pycashier.toml"):
        term.print(
            f"[InputError]: Specified config file ({filename}) does not exist.",
            err=True,
        )
        term.quit()
