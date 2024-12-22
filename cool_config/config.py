
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

def get_root_dir(path):
    return '/'.join(path.split('/')[:-1])

def read_yaml(path):
    with open(path, 'r') as f:    
        config = yaml.safe_load(f)
    return config

class Config:

    @staticmethod
    def parse_config_from_args(args, path=None):
        if path is None:
            path = args['config']
        
        config_dict = read_yaml(path)
        
        assert config_dict is not None, 'Provided config seems to be empty' 

        for k, v in args.items():
            if v is not None:
                if k in config_dict.keys():
                    print(f'CLI config overwrite for "{k}"!')
                config_dict[k] = v

        return Config('/', config_dict, None, get_root_dir(path))

    @staticmethod
    def parse_config_from_path(path):
        config = read_yaml(path)
        
        assert config is not None, 'Provided config seems to be empty' 

        return Config('/', config, None, get_root_dir(path))

    def __init__(self, path, config_dict, parent_config, root_dir):
        self.path = path
        self.parent_config = parent_config
        self.root_dir = root_dir

        # First, parse everything except the ref paths.
        # Parsing the ref paths is then initiated by
        # the root config
        self.config = self.parse_except_ref(config_dict)
        if parent_config is None:
            self.parse_ref_paths()

    # Initial Parsing

    def parse_except_ref(self, config_dict):
        parsed = {}
        for key, item in config_dict.items():
            parsed[key] = self.__parse_non_ref_item(key, item)
        return parsed

    def __parse_non_ref_item(self, key, item):
        parsed = item
        if isinstance(item, dict):
            path = os.path.join(self.path, key)
            parsed = Config(path, item, self, self.root_dir)
        elif isinstance(item, str):
            if item.startswith('<import>'):
                parsed = self.__parse_import(key, item)
        elif isinstance(item, list):
            parsed = []
            for item_item in item:
                parsed.append(self.__parse_non_ref_item(key, item_item))
        return parsed
    
    def __parse_import(self, key, item):
        item = remove_from_start('<import>', item)
        path = self.__parse_import_path(item)
        config_dict = read_yaml(path)
        return Config(
            os.path.join(self.path, key),
            config_dict,
            self,
            self.root_dir
        )

    def __parse_import_path(self, path):
        path = remove_from_end('/', path)
        if path.startswith('/'):
            # Absolute path
            return path
        else:
            # Relative Path
            return os.path.join(self.root_dir, path)

    def parse_ref_paths(self):
        for key, item in self.config.items():
            if isinstance(item, str) and item.startswith('<ref>'):
                self.config[key] = self.__parse_ref_path(item)
            elif isinstance(item, Config):
                item.parse_ref_paths()

    def __parse_ref_path(self, item):
        path = self.__prepare_ref_path(item)
        result = self.__get_item_from_path(remove_from_start('<ref>', item))
        if result is None:
            raise ValueError(f'Could not parse reference "{item}" from location "{self.path}"')
        return result

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
        list_index = None
        if cur.endswith(']'):
            list_index = cur.split('[')[-1].replace(']', '')
            list_index = int(list_index)
            cur = cur.split('[')[0]

        if self.has_key(cur):
            item = self.__get_item(cur)
            if list_index is not None:
                if not isinstance(item, list):
                    print(f'Error! Specified a list in ref path but received {item}!')
                    return None
                item = item[list_index]

            if isinstance(item, Config):
                path = remove_from_start(f'{cur}/', path)
                return item.__get_item_from_path(path)
            else:
                return item
        else:
            return None 

    # Main

    def print(self):
        lines = self.get_print_string(indent=0)
        max_k = max([len(line[0]) for line in lines])
        max_v = max([len(line[1]) for line in lines])
        for line in lines:
            print(line[0].ljust(max_k, '-'), line[1].ljust(max_v, '-'))
     
    def get_print_string(self, indent=0):
        key_prefix = ''.join(['-' for _ in range(indent)])
        lines = []
        for key, item in self.config.items():
            key = f'{key_prefix}{key}'
            cur_lines = self.__get_lines_for_item(key, item, indent)[0]
            lines += cur_lines
        return lines

    def __get_lines_for_item(self, key, item, indent):
        has_dict = False
        lines = []
        if isinstance(item, Config):
            lines.append([key, ''])
            lines += item.get_print_string(indent=indent+3)
            has_dict = True
        elif isinstance(item, list):
            list_lines = []
            for i, item_item in enumerate(item):
                cur_list_lines, cur_has_dict = self.__get_lines_for_item(f'{key}[{i}]', item_item, indent)
                list_lines += cur_list_lines
                has_dict = has_dict or cur_has_dict
            
            if has_dict:
                lines += list_lines
            else:
                lines = [[key, '[' + ','.join([line[1] for line in list_lines]) + ']']]
        else:
            lines.append(
                [key, str(item)]
            )
        return lines, has_dict

    def assert_has_key(self, key):
        if not self.has_key(key):
            error_msg = f'Config is missing key "{key}".'
            raise ValueError(error_msg)

    def has_key(self, key):
        return key in self.config.keys()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Config: {self.config.__str__()}'

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
        return self.config[key]

    def __get_item_with_default(self, key, default):
        if self.has_key(key):    
            item = self.__parse_item(key, self.config[key])
            return item
        else:
            return self.__parse_item(key, default)

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