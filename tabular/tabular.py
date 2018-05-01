# -*- coding: utf-8 -*-
from copy import deepcopy
from collections import OrderedDict
import yaml


# <-- yamlファイルを順序を保持して読み込むためのおまじない
def represent_odict(dumper, instance):
    return dumper.represent_mapping('tag:yaml.org,2002:map', instance.items())


def construct_odict(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(OrderedDict, represent_odict)
yaml.add_constructor('tag:yaml.org,2002:map', construct_odict)
# おまじないおわり-->


class Tabular(object):
    def __init__(self, columns, table_name=None, delimiter=None,):
        self._columns = columns
        self._record = []
        self._table_name = table_name if table_name else ''
        self._delimiter = delimiter if delimiter else ','

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self._table_name, self._record)

    @classmethod
    def _from_dict(cls, dic, **kwargs):
        cols = cls.extract_columns(dic)
        tabular = cls(cols, **kwargs)
        tabular.add_record(dic)
        return tabular

    @classmethod
    def from_dict(cls, dic, table_name=None):
        """
        データをレコードに書き込んで Tabular インスタンスを返す

        要素に dict や list を含む場合は Tabular インスタンスに変換される
        :param dic: dict
        :param table_name: テーブルの名前
        :return: Tabular インスタンス
        """
        if not isinstance(dic, dict):
            raise TypeError('dictを指定してください: dic={}'.format(dic))
        result_dic = {}
        for key, value in dic.items():
            if isinstance(value, dict):
                value = cls.from_dict(value, table_name=key)
            if isinstance(value, list):
                value = [cls.from_dict(val, table_name=key) if isinstance(val, dict) else val for val in value]
                child_tabular = cls.from_dict({key: value[0]}, table_name=key)
                for val in value[1:]:
                    tmp_tabular = cls.from_dict({key: val})
                    child_tabular.union(tmp_tabular)
                value = child_tabular
            result_dic[key] = value
        tabular = cls._from_dict(result_dic, table_name=table_name)
        return tabular

    @classmethod
    def extract_columns(cls, data, columns=None):
        """
        深さ優先探索で dict のキーを順序を保持しつつ取り出す

        キーの重複を set で解消すると順序が崩れるので1つずつ判定してリストに追加する
        :param data: dict or list or string
        :param columns: 既に存在するカラムを指定。破壊的な変更が加わることに注意
        :return: columns
        """
        if not columns:
            columns = []

        if isinstance(data, list):
            for d in data:
                cls.extract_columns(d, columns=columns)
        if isinstance(data, dict):
            for k in data.keys():
                if k not in columns:
                    columns.append(k)
            for val in data.values():
                if isinstance(val, dict):
                    cls.extract_columns(val, columns)
                elif isinstance(val, list):
                    for v in val:
                        cls.extract_columns(v, columns)
        if isinstance(data, str):
            if data not in columns:
                columns.append(data)
        return columns

    def add_record(self, dic):
        """dic要素からcolumnsとして指定されたものを読み込んで新しいレコードに追加する"""
        record = {}
        for col_name in self._columns:
            record[col_name] = dic.get(col_name, '')
        self._record.append(record)

    def union(self, tabular):
        """2つのtabularオブジェクトのレコードをまとめる"""
        self.record.extend(tabular.record)

    # TODO: 残念な感じなので直したい
    def normalized_record(self):
        """
        テーブル出力用に正規化されたレコードを返す。

        ex)
            self._records = {
                            'key': 'val',
                            'key2: [100, 200, 300],
                            'key3: {'k1': 'v1', 'k2': 'v2'},
                          }
            --normalize-->
            records = [{'key: 'val', 'key2': 100, 'key3': None, 'k1': None, 'k2': None},
                       {'key: 'val', 'key2': 200, 'key3': None, 'k1': None, 'k2': None},
                       ...
                       {'key: 'val', 'key2': None, 'key3': None, 'k1': 'v1, 'k2': 'v2}]
                       {'key: 'val', 'key2': None, 'key3': None, 'k1': 'v1, 'k2': 'v2}]

        :return: [{},{},...] = 正規化されたレコード(list オブジェクト
        """
        records = []
        for org_record in self.record:
            record = {}
            queue = []  # 通常の値を取得し切った dict を元にレコードを複製するため、value が list のものは後回しにする
            for key, value in org_record.items():
                if isinstance(value, Tabular):
                    value = value.normalized_record()
                if isinstance(value, list):
                    queue.append([key, value])
                    continue
                record[key] = value
            if not queue:
                records.append(record)
            else:
                for key, value in queue:
                    for val in value:
                        new_record = deepcopy(record)
                        if isinstance(val, dict):
                            # ex1) key='parent' and k='child' -> new key='parend_child'
                            # ex2) key='parent' and k='parent_child' -> new key='parent_child'
                            renamed_record = {'{}_{}'.format(key, k) if key not in k else k: v
                                              for k, v in val.items()}
                        else:
                            renamed_record = {key: v for v in val}
                        new_record.update(renamed_record)
                        records.append(new_record)
        return records

    @property
    def columns(self):
        return self._columns

    @property
    def record(self):
        return self._record

    @property
    def table_name(self):
        return self._table_name

    @table_name.setter
    def table_name(self, text):
        self._table_name = text

    @property
    def prefix(self):
        return ''

    @property
    def suffix(self):
        return self._delimiter

    @property
    def header(self):
        return self._generate_string_record(self._columns)

    @property
    def end_of_table(self):
        return ''

    def _generate_string_record(self, values):
        """
        指定されたデリメタで区切り、装飾を加えた文字列を返す。末尾に改行コードを含める

        :param values:
        :return:
        """
        return self.prefix + self._delimiter.join(str(v) if v else '' for v in values) + self.suffix + '\n'

    def render(self, normalize=True):
        """
        表を出力する

        デフォルトで normalize=True であり、レコードに破壊的な変更が加わる
        :param normalize:
        :return:
        """
        if normalize:
            records = self.normalized_record()
            self._columns = []
            for r in records:
                for col in r.keys():
                    if col not in self._columns:
                        self._columns.append(col)
        else:
            records = self.record
        res = self.header
        for record in records:
            res += self._generate_string_record([record.get(key, '') for key in self._columns])
        res += self.end_of_table
        return res


class MarkdownTabular(Tabular):
    def __init__(self, columns, **kwargs):
        super().__init__(columns, delimiter='|', **kwargs)

    @property
    def prefix(self):
        return '|'

    @property
    def suffix(self):
        return '|'

    @property
    def title(self):
        title = self.table_name
        if not title:
            title = ''
        return '## {}\n\n'.format(title)

    @property
    def header(self):
        return self.title + super().header + self._generate_string_record(':--' for _ in range(len(self._columns)))


class AsciiDocTabular(Tabular):
    def __init__(self, columns, **kwargs):
        super().__init__(columns, delimiter='|', **kwargs)

    @property
    def prefix(self):
        return '|'

    @property
    def title(self):
        title = self.table_name
        if not title:
            title = ''
        return '.{}\n'.format(title)

    @property
    def header(self):
        return self.title + '|===\n' + super().header

    @property
    def end_of_table(self):
        return '|===\n'