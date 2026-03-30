#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化智能存储柜数据
运行此脚本来创建初始存储柜
"""

import sys
import os

# 添加 app 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import app, db, SmartLocker

def init_lockers():
    """初始化存储柜数据"""

    with app.app_context():
        # 检查是否已有存储柜
        existing_count = SmartLocker.query.count()
        if existing_count > 0:
            print(f'已存在 {existing_count} 个存储柜')
            print('是否要重新创建所有存储柜？(这将删除现有数据) [y/N]: ', end='')
            choice = input().lower()
            if choice != 'y':
                print('取消操作')
                return

            # 删除所有现有存储柜
            SmartLocker.query.delete()
            db.session.commit()
            print('已删除所有现有存储柜')

        # 创建存储柜列表
        lockers_data = [
            {'number': 'A001', 'location': '图书馆一楼大厅'},
            {'number': 'A002', 'location': '图书馆一楼大厅'},
            {'number': 'A003', 'location': '图书馆一楼大厅'},
            {'number': 'A004', 'location': '图书馆一楼大厅'},
            {'number': 'A005', 'location': '图书馆一楼大厅'},
            {'number': 'B001', 'location': '教学楼A栋1楼'},
            {'number': 'B002', 'location': '教学楼A栋1楼'},
            {'number': 'B003', 'location': '教学楼A栋2楼'},
            {'number': 'B004', 'location': '教学楼A栋2楼'},
            {'number': 'B005', 'location': '教学楼A栋3楼'},
            {'number': 'C001', 'location': '食堂一楼入口'},
            {'number': 'C002', 'location': '食堂一楼入口'},
            {'number': 'C003', 'location': '食堂二楼入口'},
            {'number': 'D001', 'location': '宿舍区1号楼'},
            {'number': 'D002', 'location': '宿舍区2号楼'},
            {'number': 'D003', 'location': '宿舍区3号楼'},
            {'number': 'D004', 'location': '宿舍区4号楼'},
            {'number': 'E001', 'location': '体育馆入口'},
            {'number': 'E002', 'location': '体育馆入口'},
            {'number': 'E003', 'location': '实验楼1楼'},
        ]

        # 添加存储柜
        for locker_data in lockers_data:
            locker = SmartLocker(
                locker_number=locker_data['number'],
                location=locker_data['location']
            )
            db.session.add(locker)

        db.session.commit()

        print(f'\n✓ 成功创建 {len(lockers_data)} 个存储柜')
        print('\n存储柜列表：')
        print('-' * 60)
        print(f'{"柜号":<10} {"位置":<40}')
        print('-' * 60)
        for locker in SmartLocker.query.order_by(SmartLocker.locker_number).all():
            print(f'{locker.locker_number:<10} {locker.location:<40}')
        print('-' * 60)

if __name__ == '__main__':
    try:
        init_lockers()
        print('\n初始化完成！')
    except Exception as e:
        print(f'\n✗ 初始化失败: {e}')
        import traceback
        traceback.print_exc()
