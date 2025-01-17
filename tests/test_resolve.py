# -*- coding: utf-8 -*-

"""Tests for the bioregistry client."""

import unittest
from typing import Iterable, Tuple

import bioregistry


class TestResolve(unittest.TestCase):
    """Tests for getting Bioregistry content."""

    def test_resolve(self):
        """Test prefixes can be resolved properly."""
        for expected, query in [
            ('ncbitaxon', 'ncbitaxon'),
            ('ncbitaxon', 'NCBITaxon'),
            ('ncbitaxon', 'taxonomy'),
            ('bel', 'SCOMP'),
            ('bel', 'SFAM'),
            ('eccode', 'ec-code'),
            ('eccode', 'EC_CODE'),
            ('chembl.compound', 'chembl.compound'),
            ('chembl.compound', 'chemblcompound'),
            ('chembl', 'chembl'),
        ]:
            with self.subTest(query=query):
                self.assertEqual(expected, bioregistry.normalize_prefix(query))

    def test_get(self):
        """Test getting content from the bioregistry."""
        ncbitaxon_entry = bioregistry.get('ncbitaxon')
        self.assertIn('synonyms', ncbitaxon_entry)
        self.assertIn('NCBI_Taxon_ID', ncbitaxon_entry['synonyms'])
        self.assertIn('miriam', ncbitaxon_entry)
        self.assertIn('obofoundry', ncbitaxon_entry)
        self.assertIn('ols', ncbitaxon_entry)
        self.assertIn('wikidata', ncbitaxon_entry)

    def test_validate_none(self):
        """Test validation of identifiers for a prefix that does not exist."""
        self.assertIsNone(bioregistry.validate('lol', 'lol:nope'))

    def test_validate_true(self):
        """Test that validation returns true."""
        self.assert_validate([
            ('eccode', '1'),
            ('eccode', '1.1'),
            ('eccode', '1.1.1'),
            ('eccode', '1.1.1.1'),
            ('eccode', '1.1.123.1'),
            ('eccode', '1.1.1.123'),
            # Namespace in LUI: Standard rule for upper-casing
            ('chebi', '24867'),
            ('chebi', 'CHEBI:1234'),
            # BANANA
            ('vario', '0376'),  # this showcases the banana problem where the namespace in LUI is weird
            ('VariO', '0376'),
            ('did', 'sov:WRfXPg8dantKVubE3HX8pw'),
            ('did', 'did:sov:WRfXPg8dantKVubE3HX8pw'),
            ('go.ref', '0000041'),
            ('go.ref', 'GO_REF:0000041'),
        ])

    def assert_validate(self, examples: Iterable[Tuple[str, str]]) -> None:
        """Validate the examples."""
        for prefix, identifier in examples:
            is_valid = bioregistry.validate(prefix, identifier)
            if is_valid is False:
                with self.subTest(prefix=prefix, identifier=identifier):
                    self.fail(msg=f'CURIE {prefix}:{identifier}')

    def test_validate_false(self):
        """Test that validation returns false."""
        for prefix, identifier in [
            ('chebi', 'A1234'),
            ('chebi', 'chebi:1234'),
        ]:
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertFalse(bioregistry.validate(prefix, identifier))

    def test_lui(self):
        """Test the LUI makes sense (spoilers, they don't).

        Discussion is ongoing at:

        - https://github.com/identifiers-org/identifiers-org.github.io/issues/151
        """
        for prefix in bioregistry.read_registry():
            if not bioregistry.namespace_in_lui(prefix):
                continue
            if bioregistry.get_banana(prefix):
                continue  # rewrite rules are applied to prefixes with bananas
            if prefix in {'ark', 'obi'}:
                continue  # these patterns on identifiers.org are garb
            with self.subTest(prefix=prefix):
                re_pattern = bioregistry.get_pattern(prefix)
                miriam_prefix = bioregistry.get_identifiers_org_prefix(prefix)
                self.assertTrue(
                    re_pattern.startswith(f'^{miriam_prefix.upper()}') or re_pattern.startswith(miriam_prefix.upper()),
                    msg=f'{prefix} pattern: {re_pattern}',
                )
