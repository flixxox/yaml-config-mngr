# YAML Config Manager
A yaml config manager in Python. It provides the Config object that provides some advanced config reading functionalities ontop of the dictionary interface.

It provides:
- Easy acces with a filesystem like referencing of variables
- Tidier and reusable configs by merging multiple smaller ones into a single large config
- Namespaces to avoid conflicts
- Avoiding multiple parameter definitions by reusing config parameters

## Example

There is an example config in `example/`.
Parsing it and running `config.print()` gives:
```bash
sub1----------------------------------          
----some_param------------------------ sub1_param                                               
----some_param2----------------------- 12345.6                                                  
----some_param3----------------------- [1,2,3,4]                                                                                                                                                
----some_param4-----------------------          
--------some_param5------------------- [1,2,3]                                                  
----sub2------------------------------          
--------some_param-------------------- sub2_param                                               
--------some_ref_param---------------- <ref>../some_param                                       
--------global_ref_param-------------- <ref>/some_param                                         
sub2----------------------------------          
----some_param------------------------ sub2_param                                               
----some_ref_param-------------------- <ref>../some_param                                       
----global_ref_param------------------ <ref>/some_param                                         
some_param---------------------------- main_param                                               
some_ref_param_to_a_list-------------- <ref>main_system/some_values[1]                          
reference_to_a_reference_does_not_work <ref>some_ref_param_to_a_list                            
reference_to_sub1--------------------- <ref>sub1/some_param                                     
reference_to_sub2--------------------- <ref>sub2/some_param                                     
main_system---------------------------          
----some_values----------------------- [0,1,2,3,4]                                              
----sub1_param------------------------ <ref>../sub1/some_param4/some_param5[2]                  
some_complex_list[0]                            
----hello----------------------------- hello                                                    
some_complex_list[1]                            
----world----------------------------- world                                                    
some_complex_list[2]                            
----reference_to_hello---------------- <ref>../some_complex_list[0]/hello                       
some_complex_list[3]                            
----reference_to_world---------------- <ref>../some_complex_list[1]/world                       
config-------------------------------- example/config.yaml                                      
some_cli_arg-------------------------- Hello World!
```

This Config object provies a dict like interface:
```python
config["some_param"] -> "main_param"
```

If its okay to miss a parameter you can provide a default value in case of a miss:
```python
config["missing_param", "but we have a default"] -> "but we have a default"
```

You can access the parameters of any dictionary in a nested fashion:
```python
config["sub1/sub2/some_param"] -> "sub2_param"
```

If only the child config is present, you can reference to the parent config:
```python
config["sub1/sub2"]["../../main_system/some_values"] -> [0, 1, 2, 3, 4]
```

Just getting a single element:
```python
config["sub1/sub2"]["../../main_system/some_values[-1]"] -> 4
```

The Config provides support for referencing parameters. These parameters are strings that start with `<ref>`. For example, `config["some_complex_list[2]/reference_to_hello"]` contains `<ref>../some_complex_list[0]/hello`, which points to `"hello"`:
```python
config["some_complex_list[2]/reference_to_hello"] -> "hello"
```

Its also possible to refernce the root config by `<ref>/ANYPATH`:
```python
config["sub1/sub2/global_ref_param"] -> main_param
```