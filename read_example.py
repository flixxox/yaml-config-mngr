from cool_config import Config

args = {
    'config': 'example_configs/config.yaml',
    'some_cli_arg': 'Hello World!'
}

config = Config.parse_config_from_args(args)

config.print()

print('\n~~~~~~~~~~~~~~~~~~~\n')

print('The Config object provies a dict like interface.')
print(f'So we can just do config["some_param"] -> {config["some_param"]}.\n')

print('If its okay to miss a parameter you can provide a default value in case of a miss.')
print(f'Like so: config["missing_param", "but we have a default"] -> {config["missing_param", "but we have a default"]}\n')

print('Accessing the parameters of any dictionary in a nested fashion:')
print(f'config["sub1/sub2/some_param"] -> {config["sub1/sub2/some_param"]}\n')

print('If we only have the child config, we can reference to the parent config.')
print(f'Like so: config["sub1/sub2"]["../../main_system/some_values"] -> {config["sub1/sub2"]["../../main_system/some_values"]}\n')

print('Just getting a single element:')
print(f'config["sub1/sub2"]["../../main_system/some_values[-1]"] -> {config["sub1/sub2"]["../../main_system/some_values[-1]"]}')