import logging
import sys

logger = logging.getLogger(__name__)

if sys.platform == 'darwin':
    try:
        import pyanc350.v3
        logger.info('found pyanc350.v3 shared library')
    except OSError:
        logger.warning('could not find pyanc350.v3 shared library')
    except Exception as e:
        logger.warning('pyanc350.v3 import failed: %s', e)
else:
    try:
        import pyanc350.v2
        logger.info('found anc350v2.dll')
    except OSError:
        logger.warning('could not find anc350v2.dll')
    except Exception as e:
        logger.warning('pyanc350.v2 import failed: %s', e)

    try:
        import pyanc350.v3
        logger.info('found anc350v3.dll')
    except OSError:
        logger.warning('could not find anc350v3.dll')
    except Exception as e:
        logger.warning('pyanc350.v3 import failed: %s', e)

    try:
        import pyanc350.v4
        logger.info('found anc350v4.dll')
    except OSError:
        logger.warning('could not find anc350v4.dll')
    except Exception as e:
        logger.warning('pyanc350.v4 import failed: %s', e)