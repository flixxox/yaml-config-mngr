from cool_config import Config

args = {
    'config': 'example_configs/generic/config.yaml'
}

config = Config.parse_config_from_args(args)

config.print()