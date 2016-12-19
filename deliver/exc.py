# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound


class MissingFlowcellError(NoResultFound):
    pass
