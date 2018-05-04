# -*- coding: utf-8 -*-
from os.path import splitext
import argparse
import yaml
import json
from tabular.tabular import Tabular, MarkdownTabular, AsciiDocTabular


def set_config(args):
    tabular_cls = Tabular
    file_name = args.yml_file
    name, ext = splitext(file_name)
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

    file_parser = yaml
    if args.json or ext == 'json':
        file_parser = json
    output = args.output
    if not output:
        output = name + out_ext
    table_name = args.tablename
    if not table_name:
        table_name = name
    return file_name, file_parser, tabular_cls, output, table_name


def run(args):
    file_name, file_parser, tabular_cls, output, table_name = set_config(args)
    with open(file_name, 'r') as yml_file:
        data = file_parser.load(yml_file)
    t = tabular_cls.from_dict(data, table_name=table_name)
    result = t.render()
    with open(output, 'w') as out:
        out.write(result)
    print('output into {}'.format(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert yaml file into tabular text(csv, markdown, AsciiDoc)')
    parser.add_argument('yml_file', help='target yaml file to convert')
    parser.add_argument('-o', '--output',
                        help='output file name. If no designation, replace file extension following table style')
    parser.add_argument('-t', '--tablename', help='set table name (default: file name base)')
    parser.add_argument('-j', '--json', action='store_true', default=0, help='json file convert mode')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-md', '--markdown', action='store_true', default=1, help='as markdown style')
    group.add_argument('-ad', '--asciidoc', action='store_true', default=0, help='as AsciiDoc style')
    group.add_argument('--csv', action='store_true', default=0, help='as csv style')

    run(parser.parse_args())