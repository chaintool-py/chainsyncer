# standard imports
import logging
import unittest

# test imports
from tests.chainsyncer_base import TestBase


class TestThreadRange(TestBase):

    def test_hello(self):
        ThreadPoolRangeHistorySyncer(None, 3)
