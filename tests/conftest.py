# Copyright (C) Inco - All Rights Reserved.
#
# Written by Rafael Viotti <viotti@inco.vc>, November 2022.
#
# Unauthorized copying of this file, via any medium, is strictly prohibited. Proprietary and confidential.
#
# Refs
# ====
#
#  • http://towardsdatascience.com/pytest-with-marking-mocking-and-fixtures-in-10-minutes-678d7ccd2f70
#  • http://medium.com/worldsensing-techblog/tips-and-tricks-for-unit-tests-b35af5ba79b1.
#

'''Conftest module.'''

def pytest_configure(config):
    config.addinivalue_line('markers', 'smoke: mark test as smoke')
    config.addinivalue_line('markers', 'enigmatic: mark test as enigmatic')
    config.addinivalue_line('markers', 'limitation: test reveals an intentional limitation of the API')
    config.addinivalue_line('markers', 'slow: mark test as slow')
