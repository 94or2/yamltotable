# -*- coding: utf-8 -*-
from os.path import splitext
import argparse
import yaml
from tabular.tabular import Tabular, MarkdownTabular, AsciiDocTabular


def run(args):
    yml_file_name = args.yml_file
    output = args.output
    tabular_cls = Tabular
    out_ext = '.txt'
    if args.markdown:
        tabular_cls = MarkdownTabular
        out_ext = '.md'
    if args.asciidoc:
        tabular_cls = AsciiDocTabular
        out_ext = '.adoc'
    if args.csv:
        tabular_cls = Tabular
        out_ext = '.csv'

    with open(yml_file_name, 'r') as yml_file:
        data = yaml.load(yml_file)
    t = tabular_cls.from_dict(data, table_name='ポケモンの登場人物')
    result = t.render()
    if not output:
        output, ext = splitext(yml_file_name)
        output += out_ext
    with open(output, 'w') as out:
        out.write(result)
    print('output into {}'.format(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert yaml file into tabular text(csv, markdown, AsciiDoc)')
    parser.add_argument('yml_file', help='target yaml file to convert')
    parser.add_argument('-o', '--output',
                        help='output file name. If no designation, replace file extension following table style')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-md', '--markdown', action='store_true', default=1, help='as markdown style')
    group.add_argument('-ad', '--asciidoc', action='store_true', default=0, help='as AsciiDoc style')
    group.add_argument('--csv', action='store_true', default=0, help='as csv style')

    run(parser.parse_args())