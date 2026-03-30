#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'app')
from app import app, db, SmartLocker, LockerItem

with app.app_context():
    print('柜子状态:')
    print('-'*60)
    print(f'{"柜号":<10} {"位置":<30} {"状态":<10}')
    print('-'*60)
    for l in SmartLocker.query.order_by(SmartLocker.locker_number).all():
        print(f'{l.locker_number:<10} {l.location:<30} {l.status:<10}')
    print('-'*60)
    print(f'\n存储的物品: {LockerItem.query.count()} 件')
