
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

class CoolConfig:

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

        return CoolConfig('/', config_dict, None, get_root_dir(path))

    @staticmethod
    def parse_config_from_path(path):
        config = read_yaml(path)
        
        assert config is not None, 'Provided config seems to be empty' 

        return CoolConfig('/', config, None, get_root_dir(path))

    @staticmethod
    def parse_config_from_dict(raw_config, root_dir):
        assert raw_config is not None, 'Provided config seems to be empty' 

        return CoolConfig('/', raw_config, None, root_dir)

    def __init__(self, path, config_dict, parent_config, root_dir):
        self.path = path
        self.parent_config = parent_config
        self.root_dir = root_dir

        self.get_item_hook_fn = None

        # First, parse everything except the ref paths.
        # Parsing the ref paths then happens on the fly
        self.config = self.parse_except_ref(config_dict)

    # Initial Parsing

    def parse_except_ref(self, config_dict):
        # Parsing recursively creates a nested structure
        # of CoolConfig objects. For that, every dict encoutered
        # in the provided config is converted to a CoolConfig.
        # Additionally, configs are imported.
        parsed = {}
        for key, item in config_dict.items():
            parsed[key] = self.__parse_non_ref_item(key, item)
        return parsed

    def __parse_non_ref_item(self, key, item):
        parsed = item
        if isinstance(item, dict):
            path = os.path.join(self.path, key)
            parsed = CoolConfig(path, item, self, self.root_dir)
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
        return CoolConfig(
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

    # Main

    def print(self):
        lines = self.get_print_string(indent=0)
        max_k = max([len(line[0]) for line in lines])
        for line in lines:
            if '[' in line[0] and ']' in line[0]:
                print(line[0])
            else: 
                print(line[0].ljust(max_k, '-'), line[1])
     
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
        if isinstance(item, CoolConfig):
            lines.append([key, ''])
            lines += item.get_print_string(indent=indent+4)
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
        return f'CoolConfig: {self.config.__str__()}'

    def __getitem__(self, key):
        with_default = False
        if isinstance(key, tuple):
            assert len(key) == 2
            default = key[1]
            key = key[0]
            with_default = True
        
        res = self.__get_item_from_path(key)
        if res is None:
            if with_default:
                item = default
                location = self
            else:
                raise ValueError(f'Config is missing key "{key}"!')
        else:
            item = res[0]
            location = res[1]

        if self.__is_reference(item):
            path = location.__prepare_ref_path(item)
            res = location.__get_item_from_path(path)
            if res is None:
                raise RuntimeError(
                    f'Could not find ref path "{path}" from "{location.path}"! '
                    f'Referencing param: "{key}" from "{self.path}"!'
                )
            item = res[0]
        
        return item

    def __setitem__(self, key, value):
        if len(key.split('/')) == 1:
            value = self.__parse_non_ref_item(key, value)
            self.config[key] = value
            return

        # key is of the form: config1/config2/config3/param = value
        path = '/'.join(key.split('/')[:-1]) # config1/config2/config3
        containig_config = key.split('/')[-2] # config3
        key = key.split('/')[-1] # param

        # key can also be a list entry
        # In general, the path to config1, config2, config3 can
        # also lead through a list but this is handled by __get_item_from_path
        list_index = None
        if key.endswith(']'):
            list_index = key.split('[')[-1].replace(']', '')
            list_index = int(list_index)
            key = key.split('[')[0]

        # This checks if config1/config2/config3 exists
        # The location will be config1/config2 
        res = self.__get_item_from_path(path)
        if res is None:
            raise RuntimeError(
                f'Could not set value {value} for {key}. '
                f'Did not find parent {path}.'
            )
    
        location = res[1]
        value = location.__parse_non_ref_item(key, value)

        if list_index is not None:
            location[containig_config].config[key][list_index] = value
        else:
            location[containig_config].config[key] = value

    def __get_item_from_path(self, path):
        if path.startswith('../'):
            path = remove_from_start('../', path)
            if self.parent_config is None:
                raise RuntimeError('Error! There is no parent config.')
            else:
                return self.parent_config.__get_item_from_path(path)

        if path.startswith('/'):
            path = remove_from_start('/', path)
            return self.get_root_config().__get_item_from_path(path)

        cur_key = path.split('/')[0]
        list_index = None
        if cur_key.endswith(']'):
            list_index = cur_key.split('[')[-1].replace(']', '')
            list_index = int(list_index)
            cur_key = cur_key.split('[')[0]
        
        if self.has_key(cur_key):
            item = self.__get_item(cur_key)
            location = self

            if self.__is_reference(item):
                item, location = self.__parse_reference_item(item)

            if list_index is not None:
                if not isinstance(item, list) or len(item) <= list_index:
                    return None
                item = item[list_index]
                cur_key = f'{cur_key}[{list_index}]'

            if len(path.split('/')) == 1: # We are done
                return item, location
            else:
                if isinstance(item, CoolConfig):
                    path = remove_from_start(f'{cur_key}/', path)
                    return item.__get_item_from_path(path)
        return None

    def __prepare_ref_path(self, path):
        path = remove_from_start('<ref>', path)
        path = remove_from_end('/', path)
        return path

    def __get_item(self, key):
        self.assert_has_key(key)
        item = self.config[key]
        if self.get_item_hook_fn is not None:
            self.get_item_hook_fn(key, item)
        return item

    def __get_item_with_default(self, key, default):
        if self.has_key(key):
            item = self.config[key]
            if self.get_item_hook_fn is not None:
                self.get_item_hook_fn(key, item)
            return item
        else:
            return default
    
    def hash(self, exclude=[]):
        import hashlib
        from pprint import pformat
        return hashlib.md5(
            pformat(self.asdict(exclude=exclude)).encode('utf-8')
        ).hexdigest()

    def dump_to_file(self, filepath, exclude=[]):
        with open(filepath, 'w') as outfile:
            yaml.dump(self.asdict(exclude=exclude), outfile)

    def get_root_config(self):
        return self.get_root_config_of(self)

    def get_root_config_of(self, config):
        if config.path == '/':
            return config
        else:
            return config.parent_config.get_root_config()

    def __is_reference(self, item):
        return isinstance(item, str) and item.startswith('<ref>')

    def __parse_reference_item(self, item):
        return self.__parse_reference_item_from_location(item, self)

    def __parse_reference_item_from_location(self, item, location):
        path = location.__prepare_ref_path(item)
        res = location.__get_item_from_path(path)
        if res is None:
            raise RuntimeError(
                f'Could not find ref path "{path}" from "{location.path}"! '
                f'Referencing param: "{item}" from "{self.path}"!'
            )
        return res[0], res[1]

    # Hooks

    def register_custom_get_item_hook(self, hook_fn):
        self.get_item_hook_fn = hook_fn

    # Dict Ops

    def asdict(self, exclude=[]):
        def __parse_entry(v):
            if isinstance(v, CoolConfig):
                return v.asdict(exclude=exclude)
            if isinstance(v, list):
                res = []
                for elem in v:
                    res.append(__parse_entry(elem))
                return res
            return v

        config_dict = {}
        for k, v in self.items():
            if not k in exclude:
                config_dict[k] = __parse_entry(v)
        return config_dict

    def update(self, dict, prefix=''):
        for k, v in dict.items():
            self.config[f'{prefix}{k}'] = v

    def items(self):
        for k in self.config.keys():
            yield k, self.__getitem__(k)

    def keys(self):
        return self.config.keys()