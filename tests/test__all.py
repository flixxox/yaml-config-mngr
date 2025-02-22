import yaml
import unittest

from cool_config import CoolConfig

class CoolConfigTest:

    def test_import(self):
        self.assertEqual(
            self.config['sub1/some_param'], 'sub1_param'
        )
        self.assertEqual(
            self.config['sub1/some_param2'], 12345.6
        )
        self.assertEqual(
            self.config['sub1/some_param3'], [1,2,3,4]
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5'], [1,2,3]
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5'], [1,2,3]
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5[0]'], 1
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5[1]'], 2
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5[2]'], 3
        )
        self.assertEqual(
            self.config['sub1/some_param4/some_param5[-1]'], 3
        )
        self.assertEqual(
            self.config['sub1/sub2/some_param'], 'sub2_param'
        )
        self.assertEqual(
            self.config['sub1/sub2/some_ref_param'], 'sub1_param'
        )
        self.assertEqual(
            self.config['sub2/some_param'], 'sub2_param'
        )
        self.assertEqual(
            self.config['sub2/some_ref_param'], 'main_param'
        )

    def test_ref_to_child(self):
        self.assertEqual(
            self.config['some_ref_param_to_a_list'], 1
        )
        self.config['main_system/some_values[1]'] = 2
        self.assertEqual(
            self.config['some_ref_param_to_a_list'], 2
        )
        self.assertEqual(
            self.config['reference_to_a_reference_does_not_work'], '<ref>main_system/some_values[1]'
        )
        self.assertEqual(
            self.config['reference_to_sub1'], 'sub1_param'
        )
        self.config['sub1/some_param'] = 'sub3_param'
        self.assertEqual(
            self.config['reference_to_sub1'], 'sub3_param'
        )
        self.assertEqual(
            self.config['reference_to_sub2'], 'sub2_param'
        )

    def test_ref_to_parent(self):
        self.assertEqual(
            self.config['some_complex_list[2]/reference_to_hello'], 'hello'
        )
        self.config['some_complex_list[0]/hello'] = 'hola'
        self.assertEqual(
            self.config['some_complex_list[2]/reference_to_hello'], 'hola'
        )
        self.assertEqual(
            self.config['some_complex_list[3]/reference_to_world'], 'world'
        )
        self.config['some_complex_list[1]/world'] = 'mundo'
        self.assertEqual(
            self.config['some_complex_list[3]/reference_to_world'], 'mundo'
        )
        self.assertEqual(
            self.config['main_system/sub1_param'], 3
        )

    def test_default(self):
        self.assertEqual(
            self.config['this_param_should_not_exist', 'default'], 'default'
        )
        self.assertEqual(
            self.config['some_complex_list[4]/does_not_exist', 'default'], 'default'
        )


class ConfigFromArgs(unittest.TestCase, CoolConfigTest):
    def setUp(self):
        args = {
            'config': 'example/config.yaml',
            'some_cli_arg': 'Hello World!'
        }

        self.config = CoolConfig.parse_config_from_args(args)

class ConfigFromPath(unittest.TestCase, CoolConfigTest):
    def setUp(self):
        self.config = CoolConfig.parse_config_from_path('example/config.yaml')

class ConfigFromDict(unittest.TestCase, CoolConfigTest):
    def setUp(self):
        with open('example/config.yaml', 'r') as f:    
            config = yaml.safe_load(f)
        self.config = CoolConfig.parse_config_from_dict(config, 'example/')


if __name__ == '__main__':
    unittest.main()