import os
import yaml

def remove_from_start(to_remove, base):
    if base.startswith(to_remove):
        return base[len(to_remove):]
    return base

def remove_from_end(to_remove, base):
    if base.endswith(to_remove):
        return base[:len(to_remove)+1]
    return base

class Config:

    @staticmethod
    def parse_config_from_args(args):
        with open(args['config'], 'r') as f:    
            config = yaml.safe_load(f)
        
        assert config is not None, 'Provided config seems to be empty' 

        for k, v in args.items():
            if v is not None:
                if k in config.keys():
                    print(f'CLI config overwrite for "{k}"!')
                config[k] = v

        return Config('/', config, None)

    @staticmethod
    def parse_config_from_path(path):
        with open(path, 'r') as f:    
            config = yaml.safe_load(f)
        
        assert config is not None, 'Provided config seems to be empty' 

        return Config('/', config)

    def __init__(self, path, config, parent_config):
        self.path = path
        self.config = config
        self.parent_config = parent_config

    def print(self):
        max_key_length = max([len(k) for k in self.config.keys()])
        for key in self.config:
            print(key.ljust(max_key_length, '-'), str(self.config[key]).ljust(100, '-'))

    def assert_has_key(self, key):
        if not self.has_key(key):
            error_msg = f'Config is missing key "{key}".'
            raise ValueError(error_msg)

    def has_key(self, key):
        return key in self.config.keys()

    def __str__(self):
        return f'{self.path}: ' + self.config.__str__()

    def __getitem__(self, key):
        if isinstance(key, tuple):
            assert len(key) == 2
            default = key[1]
            key = key[0]
            return self.__get_item_with_default(key, default)
        else:
            return self.__get_item(key)
    
    def __get_item(self, key):
        self.assert_has_key(key)
        item = self.__parse_item(key, self.config[key])
        return item

    def __get_item_with_default(self, key, default):
        if self.has_key(key):    
            item = self.__parse_item(key, self.config[key])
            return item
        else:
            return self.__parse_item(key, default)

    def __parse_item(self, key, item):
        if isinstance(item, dict):
            path = os.path.join(self.path, key)
            return Config(path, item, self)
        elif isinstance(item, str):
            if item.startswith('<ref>'):
                path = self.__prepare_ref_path(item)
                result = self.__get_item_from_path(remove_from_start('<ref>', item))
                if result is None:
                    raise ValueError(f'Could not parse reference "{item}" from location "{self.path}"')
                return result
        # TODO: Parsing lists that contain dicts
        return item

    def __prepare_ref_path(self, path):
        path = remove_from_start('<ref>', path)
        path = remove_from_start('/', path)
        path = remove_from_end('/', path)
        return path

    def __get_item_from_path(self, path):
        if path.startswith('../'):
            path = remove_from_start('../', path)
            return self.parent_config.__get_item_from_path(path)
        cur = path.split('/')[0]
        if self.has_key(cur):
            item = self.__get_item(cur)
            if isinstance(item, Config):
                path = remove_from_start(f'{cur}/', path)
                return item.__get_item_from_path(path)
            else:
                return item
        else:
            return None 

    def __setitem__(self, key, value):
        self.config[key] = value
    
    # Dict Ops

    def asdict(self):
        return self.config

    def update(self, dict, prefix=''):
        for k, v in dict.items():
            self.config[f'{prefix}{k}'] = v

    def items(self):
        for k, v in self.config.items():
            yield k, self.__parse_item(k, v)

    def keys(self):
        return self.config.keys()