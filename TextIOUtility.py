import codecs
import os
from os.path import join



def load_dictionary(file_path, has_values=False, target_dict=None, use_encoding='utf-8'):
    result = {} if target_dict is None else target_dict
    file_size = min(32, os.path.getsize(file_path))
    with open(file_path, 'rb') as f_enc:
        raw = f_enc.read(file_size)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            encoding = use_encoding
    with open(file_path, 'r', encoding=encoding) as f_handle:
        for line in f_handle:
            if has_values:
                values = line.strip().split('\t')
                if len(values) > 2:
                    key = values.pop(0)
                    value = values
                elif len(values) == 2:
                    key = values[0]
                    value = values[1]
                else:
                    key = values[0]
                    value = True
                result[key] = value
            else:
                result[line.strip()] = True
    return result


def dictionary_dump(file_path, target_dict):
    with open(file_path, 'w', encoding='utf-16') as out_file:
        for key_name in sorted([term for term in target_dict]):
            key_value = target_dict[key_name]
            if type(key_value) is list or type(key_value) is tuple:
                key_value = "\t".join([str(item) for item in key_value])
            else:
                key_value = str(key_value)
            out_file.write(key_name + '\t' + str(key_value) + '\n')



if __name__ == "__main__":
    negative = load_dictionary(join(join('data', 'model'),'negative.txt'))
    for t in sorted(negative.keys()):
        print(t, negative[t])

