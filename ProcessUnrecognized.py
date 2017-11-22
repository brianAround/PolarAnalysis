from queue import PriorityQueue
from collections import namedtuple
from os.path import join


UnrecognizedTerm = namedtuple('UnrecognizedTerm', ['name', 'usages', 'positive', 'negative'])

file_path = 'Unrec Hillary Clinton.txt'

term_types = ['positive', 'negative', 'ambivalent']
include = {}

for term_type in term_types:
    include[term_type] = []

items = PriorityQueue()


with open(file_path, 'r', encoding='utf-16-le') as term_info:
    for line in term_info:
        values = line.strip().split('\t')
        if len(values) == 4:
            load = (10000 - int(values[1]), UnrecognizedTerm(values[0], int(values[1]), int(values[2]), int(values[3])))
            items.put(load)

choice = ''

while len(choice) == 0 or choice[0].lower() != 'q':
    current_term = items.get()[1]
    print('Term:', current_term[0])
    print('Total Usages:', current_term.usages, '\tPositive:', current_term.positive, '\tNegative:', current_term.negative)
    choice = input('Set as (P)ositive, (N)egative, or (A) for Neutral:')
    if len(choice) > 0:
        choice = choice[0].lower()
        for term_type in term_types:
            if choice == term_type[0]:
                include[term_type].append(current_term)

for term_type in term_types:
    print(term_type, ':', include[term_type])

add_choice = input('Add to extended term files?')
add_choice = add_choice[0].lower()
if add_choice == 'y':
    ext_data_path = join('data', 'extra')
    for term_type in term_types:
        if len(include[term_type]) > 0:
            out_path = join(ext_data_path, term_type + '.txt')
            with open(out_path, 'a', encoding='utf-16') as out_file:
                for new_term in include[term_type]:
                    out_file.write(new_term.name)
                    out_file.write('\n')


