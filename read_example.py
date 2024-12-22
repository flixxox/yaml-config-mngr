from cool_config import Config

args = {
    'config': 'example_configs/config.yaml',
    'some_cli_arg': 'Hello World!'
}

config = Config.parse_config_from_args(args)

config.print()