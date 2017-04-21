# -*- coding: utf-8 -*-
"""Tests for unihan data download and processing."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import logging
import os
import shutil
import tempfile
import unittest
import zipfile
import pytest

from scripts import process
from scripts._compat import text_type
from scripts.process import (UNIHAN_DEST, UNIHAN_FIELDS,
                             UNIHAN_URL, UNIHAN_ZIP_FILEPATH, WORK_DIR,
                             Builder, default_config, zip_has_files)
from scripts.util import (merge_dict, ucn_to_unicode,
                          ucnstring_to_unicode)

from scripts.test import captureStdErr, get_datapath

try:
    import unittest2 as unittest  # NOQA
except ImportError:  # Python 2.7
    import unittest

log = logging.getLogger(__name__)


SAMPLE_DATA = """\
U+3400	kCantonese	jau1
U+3400	kDefinition	(same as U+4E18 丘) hillock or mound
U+3400	kMandarin	qiū
U+3401	kCantonese	tim2
U+3401	kDefinition	to lick; to taste, a mat, bamboo bark
U+3401	kHanyuPinyin	10019.020:tiàn
"""

test_config = merge_dict(default_config.copy(), {
    'source': UNIHAN_URL,
    'destination': UNIHAN_DEST,
    'zip_filepath': UNIHAN_ZIP_FILEPATH,
    'work_dir': WORK_DIR,
    'fields': UNIHAN_FIELDS,
    'files': 'Unihan_Readings.txt',
    'download': False
})


class MockBuilder(Builder):

    default_config = test_config


Builder = MockBuilder


class TestCase(unittest.TestCase):
    pass


class UnihanHelper(TestCase):

    config = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'test_config.yml'
    ))

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.mock_zip_filename = 'Unihan.zip'
        cls.mock_zip_filepath = os.path.join(
            cls.tempdir, cls.mock_zip_filename
        )
        zf = zipfile.ZipFile(cls.mock_zip_filepath, 'a')
        zf.writestr("Unihan_Readings.txt", SAMPLE_DATA.encode('utf-8'))
        zf.close()

        Builder.default_config['work_dir'] = cls.tempdir
        Builder.default_config['zip_filepath'] = cls.mock_zip_filepath
        Builder.default_config['destination'] = os.path.join(
            cls.tempdir, 'unihan.csv'
        )

        cls.mock_zip = zf

        super(UnihanHelper, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)
        super(UnihanHelper, cls).tearDownClass()


class UnihanMock(UnihanHelper):

    def test_builder_mock(self):

        assert test_config == Builder.default_config
        assert test_config != default_config

        b = Builder({})

        assert test_config == b.config
        assert default_config != b.config


class UnihanScriptsTestCase(UnihanHelper):

    def test_zip_has_files(self):
        assert zip_has_files(['Unihan_Readings.txt'], self.mock_zip)

        assert not zip_has_files(['Unihan_Cats.txt'], self.mock_zip)

    def test_has_unihan_zip(self):
        if os.path.isfile(UNIHAN_ZIP_FILEPATH):
            assert process.has_unihan_zip()
        else:
            assert not process.has_unihan_zip()

        assert process.has_unihan_zip(self.mock_zip_filepath)

    def test_in_fields(self):
        columns = ['hey', 'kDefinition', 'kWhat']
        result = process.in_fields('kDefinition', columns)

        assert result

    def test_filter_manifest(self):
        expected = {
            'Unihan_Variants.txt': [
                'kCompatibilityVariant',
                'kSemanticVariant',
                'kSimplifiedVariant',
                'kSpecializedSemanticVariant',
                'kTraditionalVariant',
                'kZVariant',
            ]
        }

        result = process.filter_manifest(['Unihan_Variants.txt'])

        assert set(result) == set(expected)

    def test_get_files(self):
        fields = ['kKorean', 'kRSUnicode']

        expected = ['Unihan_Readings.txt', 'Unihan_RadicalStrokeCounts.txt']

        result = process.get_files(fields)

        assert set(result) == set(expected)

    def test_save(self):

        src_filepath = self.mock_zip_filepath

        tempdir = tempfile.mkdtemp()

        dest_filepath = os.path.join(tempdir, self.mock_zip_filename)
        process.save(src_filepath, dest_filepath, shutil.copy)

        result = os.path.exists(dest_filepath)

        shutil.rmtree(tempdir)

        assert result

    def test_download(self):

        src_filepath = self.mock_zip_filepath

        tempdir = self.tempdir
        dest_filepath = os.path.join(tempdir, 'data', self.mock_zip_filename)

        process.download(src_filepath, dest_filepath, shutil.copy)

        result = os.path.dirname(os.path.join(dest_filepath, 'data'))
        assert result, "Creates data directory if doesn't exist."

    def test_extract(self):

        zf = process.extract(self.mock_zip_filepath)

        assert len(zf.infolist()) == 1
        assert zf.infolist()[0].file_size == 218
        assert zf.infolist()[0].filename == "Unihan_Readings.txt"

    def test_convert_only_output_requested_columns(self):
        fd, filename = tempfile.mkstemp()

        try:
            os.write(fd, SAMPLE_DATA.encode('utf-8'))

            csv_files = [
                filename
            ]

            columns = [
                'kTotalStrokes',
                'kPhonetic',
                'kCantonese',
                'kDefinition',
            ] + process.INDEX_FIELDS

            items = process.convert(csv_files, columns)

            notInColumns = []
            inColumns = ['kDefinition', 'kCantonese'] + process.INDEX_FIELDS

            # columns not selected in convert must not be in result.
            for v in items[0]:
                if v not in columns:
                    notInColumns.append(v)
                else:
                    inColumns.append(v)
        finally:
            os.remove(filename)

        assert [] == notInColumns, "Convert filters columns not specified."
        assert set(inColumns).issubset(set(columns)), (
            "Convert returns correct columns specified + ucn and char."
        )

    def test_convert_simple_data_format(self):
        """convert turns data into simple data format (SDF)."""
        csv_files = [
            get_datapath('Unihan_DictionaryLikeData.txt'),
            get_datapath('Unihan_Readings.txt'),
        ]

        columns = [
            'kTotalStrokes',
            'kPhonetic',
            'kCantonese',
            'kDefinition',
        ] + process.INDEX_FIELDS

        items = process.convert(csv_files, columns)

        header = items[0]
        assert header == columns

        rows = items[1:]  # NOQA

    def test_convert_keys_values_match(self):
        """convert returns values in the correct places."""
        pass


class UnihanHelperFunctions(UnihanHelper):

    """Utilities to retrieve unihan data in datapackage format."""

    def test_flatten_fields(self):

        single_dataset = {
            'Unihan_Readings.txt': [
                'kCantonese',
                'kDefinition',
                'kHangul',
            ]
        }

        expected = ['kCantonese', 'kDefinition', 'kHangul']
        results = process.get_fields(single_dataset)

        assert expected == results

        datasets = {
            'Unihan_NumericValues.txt': [
                'kAccountingNumeric',
                'kOtherNumeric',
                'kPrimaryNumeric',
            ],
            'Unihan_OtherMappings.txt': [
                'kBigFive',
                'kCCCII',
                'kCNS1986',
            ]
        }

        expected = [
            'kAccountingNumeric',
            'kOtherNumeric',
            'kPrimaryNumeric',
            'kBigFive',
            'kCCCII',
            'kCNS1986',
        ]

        results = process.get_fields(datasets)

        assert set(expected) == set(results)

    def test_pick_files(self):
        """Pick a white list of files to build from."""

        files = ['Unihan_Readings.txt', 'Unihan_Variants.txt']

        config = {
            'files': files,
            'zip_filepath': self.mock_zip_filepath
        }

        b = process.Builder(config)

        result = b.config.files
        expected = files

        assert result == expected, 'Returns only the files picked.'

    def test_raise_error_unknown_field(self):
        """Throw error if picking unknown field."""

        config = {
            'fields': ['kHello']
        }

        with pytest.raises(KeyError) as excinfo:
            process.Builder(config)
        excinfo.match('Field ([a-zA-Z].*) not found in file list.')

    def test_raise_error_unknown_file(self):
        """Throw error if picking unknown file."""

        config = {
            'files': ['Sparta.lol']
        }

        with pytest.raises(KeyError) as excinfo:
            process.Builder(config)
        excinfo.match('File ([a-zA-Z_\.\'].*) not found in file list.')

    def test_raise_error_unknown_field_filtered_files(self):
        """Throw error field not in file list, when files specified."""

        files = ['Unihan_Variants.txt']

        config = {
            'files': files,
            'fields': ['kDefinition'],
        }

        with pytest.raises(KeyError) as excinfo:
            process.Builder(config)
        excinfo.match('Field ([a-zA-Z].*) not found in file list.')

    def test_set_reduce_files_automatically_when_only_field_specified(self):
        """Picks file automatically if none specified and fields are."""

        fields = (
            process.UNIHAN_MANIFEST['Unihan_Readings.txt'] +
            process.UNIHAN_MANIFEST['Unihan_Variants.txt']
        )

        config = {
            'fields': fields,
        }

        b = process.Builder(config)

        expected = ['Unihan_Readings.txt', 'Unihan_Variants.txt']
        results = b.config.files

        assert set(expected) == set(results)

    def test_set_reduce_fields_automatically_when_only_files_specified(self):
        """Picks only necessary files when fields specified."""

        files = ['Unihan_Readings.txt', 'Unihan_Variants.txt']

        config = {
            'files': files
        }

        b = process.Builder(config)

        expected = process.get_fields(process.filter_manifest(files))
        results = b.config.fields

        assert set(expected) == set(results), (
            'Returns only the fields for files picked.'
        )


class ProcessTestCase(TestCase):

    def test_conversion_ucn_to_unicode(self):
        before = 'U+4E00'
        expected = '\u4e00'

        result = ucn_to_unicode(before)

        assert result == expected

        assert isinstance(result, text_type)

        # wide character
        before = 'U+20001'
        expected = '\U00020001'

        result = ucn_to_unicode(before)

        assert result == expected
        assert isinstance(result, text_type)

        before = '(same as U+7A69 穩) firm; stable; secure'
        expected = '(same as 穩 穩) firm; stable; secure'

        result = ucnstring_to_unicode(before)

        assert result == expected
        assert isinstance(result, text_type)


class CliArgTestCase(UnihanHelper):

    """Allows for creating a custom output of unihan data
    in datapackage.json format."""

    def test_no_args(self):
        """Works without arguments."""

        expected = test_config
        result = Builder.from_cli([]).config

        assert expected == result

    def test_cli_plus_defaults(self):
        """Test CLI args + defaults."""

        expectedIn = {'zip_filepath': self.mock_zip_filepath}
        result = Builder.from_cli(['-z', self.mock_zip_filepath]).config
        self.assertDictContainsSubset(expectedIn, result)

        expectedIn = {'fields': ['kDefinition']}
        result = Builder.from_cli(['-F', 'kDefinition']).config
        self.assertDictContainsSubset(expectedIn, result)

        expectedIn = {'fields': ['kDefinition']}
        result = Builder.from_cli(['-F', 'kDefinition']).config
        self.assertDictContainsSubset(expectedIn, result)

        expectedIn = {'fields': ['kDefinition', 'kXerox']}
        result = Builder.from_cli(['-F', 'kDefinition', 'kXerox']).config
        self.assertDictContainsSubset(
            expectedIn, result, msg="Accepts multiple fields."
        )

        expectedIn = {
            'fields': ['kDefinition', 'kXerox'], 'destination': 'data/ha.csv'
        }
        result = Builder.from_cli(
            ['-F', 'kDefinition', 'kXerox', '-d', 'data/ha.csv']).config
        self.assertDictContainsSubset(
            expectedIn, result, msg="Accepts multiple arguments."
        )

    def test_cli_exit_emessage_to_stderr(self):
        """Sends exception .message to stderr on exit."""

        with pytest.raises(SystemExit) as excinfo:
            with captureStdErr(
                Builder.from_cli, ['-d', 'data/output.csv', '-F', 'sdfa']
            ):
                pass
        excinfo.match('Field sdfa not found in file list.')
