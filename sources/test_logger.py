__author__ = 'antoine'

import unittest
from logger import get_logger

logger = get_logger(__name__)

class TestLogger(unittest.TestCase):
    def test_logger(self):
        logger.info('generate by unittesting')

if __name__ == "__main__":
    unittest.main()