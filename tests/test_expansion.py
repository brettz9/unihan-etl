# -*- coding: utf-8 -*-
"""Test expansion of multi-value fields in UNIHAN."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import pytest

from unihan_tabular import process


def test_expands_spaces(expanded_data):
    for item in expanded_data:
        for field in item.keys():
            if field in process.SPACE_DELIMITED_LIST_FIELDS and item[field]:
                assert isinstance(item[field], list)


def test_expand_kCantonese(expanded_data):
    # test kCantonese
    item = [i for i in expanded_data if i['ucn'] == 'U+342B'][0]
    if item['ucn'] == 'U+342B':
        assert set(item['kCantonese']) == set(['gun3', 'hung1', 'zung1'])
    else:
        assert False, "Missing field U+342B kCantonese"


@pytest.mark.parametrize("ucn,field,expected", [
    ("U+37AE", "kJapaneseKun", ['DERU', 'DASU']),
    ("U+37AE", "kJapaneseOn", ['SHUTSU', 'SUI']),
    ("U+37AE", "kDefinition", [
        'variant of 出 U+51FA, to go out, send out',
        'to stand',
        'to produce'
    ]),
])
def test_expand(expanded_data, ucn, field, expected):
    # test kDefinition (split on ;), kJapanese, kJapaneseKun
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert set(item[field]) == set(expected)


@pytest.mark.parametrize("ucn,expected", [
    ("U+346E", {  # U+346E	kMandarin	hún
        "zh-Hans": "hún",
        "zh-Hant": "hún"
    }),
    ("U+4FFE", {  # U+4FFE	kMandarin	bǐ bì
        "zh-Hans": "bǐ",
        "zh-Hant": "bì"
    })
])
def test_expand_kMandarin(expanded_data, ucn, expected):
    """
    The most customary pinyin reading for this character. When there are two
    values, then the first is preferred for zh-Hans (CN) and the second is
    preferred for zh-Hant (TW). When there is only one value, it is appropriate
    for both.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kMandarin'] == expected


@pytest.mark.parametrize("ucn,expected", [
    ("U+8303", {  # U+8303	kTotalStrokes	8 9
        "zh-Hans": 8,
        "zh-Hant": 9
    }),
    ("U+34D6", {  # U+34D6	kTotalStrokes	13
        "zh-Hans": 13,
        "zh-Hant": 13
    })
])
def test_expand_kTotalStrokes(expanded_data, ucn, expected):
    """
    The total number of strokes in the character (including the radical). When
    there are two values, then the first is preferred for zh-Hans (CN) and the
    second is preferred for zh-Hant (TW). When there is only one value, it is
    appropriate for both.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kTotalStrokes'] == expected


@pytest.mark.parametrize("ucn,expected", [
    ("U+5EFE", [{  # U+5EFE	kHanyuPinyin	10513.110,10514.010,10514.020:gǒng
        "locations": [
            {
                "volume": 1,
                "page": 513,
                "character": 110
            },
            {
                "volume": 1,
                "page": 514,
                "character": 10
            },
            {
                "volume": 1,
                "page": 514,
                "character": 20
            }
        ],
        "readings": [
            "gǒng"
        ]
    }]),
    ("U+5364", [{  # U+5364	kHanyuPinyin	10093.130:xī,lǔ 74609.020:lǔ,xī
        "locations": [
            {
                "volume": 1,
                "page": 93,
                "character": 130
            }
        ],
        "readings": [
            "xī",
            "lǔ"
        ]
    }, {
        "locations": [
            {
                "volume": 7,
                "page": 4609,
                "character": 20
            }
        ],
        "readings": [
            "lǔ",
            "xī"
        ]
    }]),
    ("U+34D8", [{  # U+34D8	kHanyuPinyin	10278.080,10278.090:sù
        "locations": [
            {
                "volume": 1,
                "page": 278,
                "character": 80
            },
            {
                "volume": 1,
                "page": 278,
                "character": 90
            }
        ],
        "readings": [
            "sù"
        ]
    }]),
    ("U+34CE", [{  # U+34CE	kHanyuPinyin	10297.260:qīn,qìn,qǐn
        "locations": [
            {
                "volume": 1,
                "page": 297,
                "character": 260
            }
        ],
        "readings": [
            "qīn", "qìn", "qǐn"
        ]
    }])
])
def test_expand_kHanyuPinyin(expanded_data, ucn, expected):
    """
    Each location has the form “ABCDE.XYZ” (as in “kHanYu”); multiple
    locations for a given pīnyīn reading are separated by “,” (comma). The
    list of locations is followed by “:” (colon), followed by a
    comma-separated list of one or more pīnyīn readings. Where multiple
    pīnyīn readings are associated with a given mapping, these are ordered as
    in HDZ (for the most part reflecting relative commonality). The following
    are representative records.

    | U+34CE | 㓎 | 10297.260: qīn,qìn,qǐn |
    | U+34D8 | 㓘 | 10278.080,10278.090: sù |
    | U+5364 | 卤 | 10093.130: xī,lǔ 74609.020: lǔ,xī |
    | U+5EFE | 廾 | 10513.110,10514.010,10514.020: gǒng |

    For example, the “kHanyuPinyin” value for 卤 U+5364 is
    10093.130: xī,lǔ 74609.020: lǔ,xī”. This means that 卤 U+5364 is found in
    kHanYu” at entries 10093.130 and 74609.020. The former entry has the two
    pīnyīn readings xī and lǔ (in that order), whereas the latter entry has
    the readings lǔ and xī (reversing the order).
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kHanyuPinyin'] == expected


@pytest.mark.parametrize("ucn,expected", [
    ("U+34B9", [{  # U+34B9	kHanYu	10254.060 10254.100
        "volume": 1,
        "page": 254,
        "character": 60
    }, {
        "volume": 1,
        "page": 254,
        "character": 100
    }]),
    ('U+34AD', [{  # U+34AD	kHanYu	10273.120
        "volume": 1,
        "page": 273,
        "character": 120
    }])
])
def test_expand_HanYu(expanded_data, ucn, expected):
    """
    The character references are given in the form “ABCDE.XYZ”, in which: “A”
    is the volume number [1..8]; “BCDE” is the zero-padded page number
    [0001..4809]; “XY” is the zero-padded number of the character on the page
    [01..32]; “Z” is “0” for a character actually in the dictionary, and
    greater than 0 for a character assigned a “virtual” position in the
    dictionary. For example, 53024.060 indicates an actual HDZ character, the
    6th character on Page 3,024 of Volume 5 (i.e. 籉 [U+7C49]). Note that the
    Volume 8 “BCDE” references are in the range [0008..0044] inclusive,
    referring to the pagination of the “Appendix of Addendum” at the end of
    that volume (beginning after p. 5746).

    The first character assigned a given virtual position has an index ending
    in 1; the second assigned the same virtual position has an index ending in
    2; and so on.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kHanYu'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+4E9D      kRSAdobe_Japan1_6       C+17245+7.2.6 C+17245+28.2.6
    ("U+4E9D", [{
        "type": "C",
        "cid": 17245,
        "radical": 7,
        "strokes": 2,
        "strokes-residue": 6
    }, {
        "type": "C",
        "cid": 17245,
        "radical": 28,
        "strokes": 2,
        "strokes-residue": 6
    }]),
    # U+4E9E      kRSAdobe_Japan1_6       C+4108+7.2.6
    ("U+4E9E", [{
        "type": "C",
        "cid": 4108,
        "radical": 7,
        "strokes": 2,
        "strokes-residue": 6
    }]),
    # U+4E30      kRSAdobe_Japan1_6       C+14301+2.1.3 V+15386+2.1.3
    ("U+4E30", [{
        "type": "C",
        "cid": 14301,
        "radical": 2,
        "strokes": 1,
        "strokes-residue": 3
    }, {
        "type": "V",
        "cid": 15386,
        "radical": 2,
        "strokes": 1,
        "strokes-residue": 3
    }]),
])
def test_expand_kRSAdobe_Japan1_6(expanded_data, ucn, expected):
    """
    The value consists of a number of space-separated entries. Each entry
    consists of three pieces of information separated by a plus sign:

    1) C or V. “C” indicates that the Unicode code point maps directly to the
    Adobe-Japan1-6 CID that appears after it, and “V” indicates that it is
    considered a variant form, and thus not directly encoded.

    2) The Adobe-Japan1-6 CID.

    3) Radical-stroke data for the indicated Adobe-Japan1-6 CID. The
    radical-stroke data consists of three pieces separated by periods: the
    KangXi radical (1-214), the number of strokes in the form the radical
    takes in the glyph, and the number of strokes in the residue. The standard
    Unicode radical-stroke form can be obtained by omitting the second value,
    and the total strokes in the glyph from adding the second and third
    values.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kRSAdobe_Japan1_6'] == expected


@pytest.mark.parametrize("field,ucn,expected", [
    # U+4E55      kRSJapanese     4.6
    ('kRSJapanese', 'U+4E55', [{
        "radical": 4,
        "strokes": 6
    }]),
    # U+4E99      kRSKangXi       7.4
    ('kRSKangXi', 'U+4E99', [{
        "radical": 7,
        "strokes": 4
    }]),
    # U+4E9A      kRSKangXi       1.5
    ('kRSKangXi', 'U+4E9A', [{
        "radical": 1,
        "strokes": 5
    }]),
    # U+4E54      kRSKanWa        37.3
    ('kRSKanWa', 'U+4E54', [{
        "radical": 37,
        "strokes": 3
    }]),
    # U+4E55      kRSKanWa        4.6
    ('kRSKanWa', 'U+4E55', [{
        "radical": 4,
        "strokes": 6
    }]),
    # U+5378      kRSKorean       26.7
    ('kRSKorean', 'U+5378', [{
        "radical": 26,
        "strokes": 7
    }]),
])
def test_expand_radical_stroke_counts(expanded_data, field, ucn, expected):
    """kRSJapanese
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item[field] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+3491      kRSUnicode      9.13
    ('U+3491', [{
        "radical": 9,
        "strokes": 13,
        "simplified": False
    }]),
    # U+4336       kRSUnicode      120'.3
    ('U+4336', [{
        "radical": 120,
        "strokes": 3,
        "simplified": True
    }]),
])
def test_expand_kRSUnihan(expanded_data, ucn, expected):
    """
    The standard radical/stroke count for this character in the form
    “radical.additional strokes”. The radical is indicated by a number in the
    range (1..214) inclusive. An apostrophe (') after the radical indicates a
    simplified version of the given radical. The “additional strokes” value is
    the residual stroke-count, the count of all strokes remaining after
    eliminating all strokes associated with the radical.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kRSUnicode'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+34BC      kCheungBauer    055/08;TLBO;mang4
    ('U+34BC', [{
        "radical": 55,
        "strokes": 8,
        "cangjie": "TLBO",
        "readings": [
            "mang4"
        ]
    }]),
    # U+356C  kCheungBauer    030/04;;gung1
    ('U+356C', [{
        "radical": 30,
        "strokes": 4,
        "cangjie": None,
        "readings": [
            "gung1"
        ]
    }]),
    # U+3598  kCheungBauer    030/07;RMMV;san2,seon2
    ('U+3598', [{
        "radical": 30,
        "strokes": 7,
        "cangjie": "RMMV",
        "readings": [
            "san2",
            "seon2"
        ]
    }])
])
def test_expand_kCheungBauer(expanded_data, ucn, expected):
    """
    Each data value consists of three pieces, separated by semicolons:

    (1) the character’s radical-stroke index as a three-digit radical, slash,
    two-digit stroke count;
    (2) the character’s cangjie input code (if any); and
    (3) a comma-separated list of Cantonese readings using the jyutping
    romanization in alphabetical order.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kCheungBauer'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+34D6      kCihaiT 170.105
    ("U+34D6", [{
        "page": 170,
        "row": 1,
        "position": 5
    }])
])
def test_expand_kCihaiT(expanded_data, ucn, expected):
    """
    The position is indicated by a decimal number. The digits to the left of
    the decimal are the page number. The first digit after the decimal is the
    row on the page, and the remaining two digits after the decimal are the
    position on the row.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kCihaiT'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+9F7C  kDaeJaweon      2075.100
    ("U+9F7C", {
        "page": 2075,
        "position": 10,
        "virtual": 0
    }),
    # U+4E37  kDaeJaweon      0162.211
    ("U+4E37", {
        "page": 162,
        "position": 21,
        "virtual": 1
    }),
])
def test_expand_kDaeJaweon(expanded_data, ucn, expected):
    """
    The position is in the form “page.position” with the final digit in the
    position being “0” for characters actually in the dictionary and “1” for
    characters not found in the dictionary and assigned a “virtual” position in
    the dictionary.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kDaeJaweon'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+342C      kFenn   871P
    ("U+342C", [{
        "phonetic": 871,
        "frequency": "P"
    }]),
    # U+3431      kFenn   281K
    ("U+3431", [{
        "phonetic": 281,
        "frequency": "K"
    }]),
    # U+9918      kFenn   31A
    ("U+9918", [{
        "phonetic": 31,
        "frequency": "A"
    }]),
])
def test_expand_kFenn(expanded_data, ucn, expected):
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kFenn'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+4E0B      kHanyuPinlu     xià(6430) xia(249)
    ("U+4E0B", [{
        "phonetic": "xià",
        "frequency": 6430
    }, {
        "phonetic": "xia",
        "frequency": 249
    }]),
    # U+4E09      kHanyuPinlu     sān(3030)
    ("U+4E09", [{
        "phonetic": "sān",
        "frequency": 3030
    }])
])
def test_expand_kHanyuPinlu(expanded_data, ucn, expected):
    """
    Immediately following the pronunciation, a numeric string appears in
    parentheses: e.g. in “ā(392)” the numeric string “392” indicates the sum
    total of the frequencies of the pronunciations of the character as given in
    HYPLCD.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kHanyuPinlu'] == expected


@pytest.mark.parametrize("ucn,expected", [
    # U+4E00  kHDZRadBreak    ⼀[U+2F00]:10001.010
    ('U+4E00', {
        "radical": "⼀",
        "ucn": "U+2F00",
        "location": "10001.010"
    }),
    # U+4E59  kHDZRadBreak    ⼄[U+2F04]:10047.040
    ('U+4E59', {
        "radical": "⼄",
        "ucn": "U+2F04",
        "location": "10047.040"
    }),
])
def test_expand_kHDZRadBreak(expanded_data, ucn, expected):
    """
    Hanyu Da Zidian has a radical break beginning at this character’s position.
    The field consists of the radical (with its Unicode code point), a colon,
    and then the Hanyu Da Zidian position as in the kHanyu field.
    """
    item = [i for i in expanded_data if i['ucn'] == ucn][0]
    assert item['kHDZRadBreak'] == expected
