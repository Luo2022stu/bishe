#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看数据库中招领物品和找寻物品的存储数据
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import sys

# 添加app目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 加载环境变量
load_dotenv('app/.env')

# 创建Flask应用
app = Flask(__name__)

# 配置数据库（与app.py相同的配置）
basedir = os.path.abspath(os.path.dirname(__file__))
database_type = os.getenv('DATABASE_TYPE', 'sqlite')

if database_type == 'sqlite':
    sqlite_path = os.getenv('SQLITE_DB_PATH', 'app/lost_found.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, sqlite_path)
    print(f'[*] 使用 SQLite 数据库: {os.path.join(basedir, sqlite_path)}')

# 创建数据库实例
db = SQLAlchemy(app)

# 定义数据模型（与app.py一致）
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class LostItem(db.Model):
    __tablename__ = 'lost_item'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), default='found')  # found (失物招领) 或 lost (失物找寻)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    contact = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, claimed, returned
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())

def print_separator(char='=', length=80):
    print(char * length)

def print_table(items, item_type):
    """打印物品表格"""
    if not items:
        print(f"\n[!] 没有找到{item_type}")
        return

    print(f"\n{'='*100}")
    print(f"[{item_type}] 共找到 {len(items)} 条记录")
    print(f"{'='*100}")
    print(f"{'ID':<5} {'类型':<8} {'标题':<20} {'类别':<10} {'地点':<20} {'状态':<10} {'浏览':<6} {'点赞':<6}")
    print(f"{'-'*100}")

    for item in items:
        type_name = '招领' if item.type == 'found' else '寻物'
        status_name = {
            'pending': '待认领',
            'claimed': '已认领',
            'returned': '已归还'
        }.get(item.status, item.status)
        
        print(f"{item.id:<5} {type_name:<8} {item.title[:18]:<20} {item.category:<10} {item.location[:18]:<20} {status_name:<10} {item.view_count:<6} {item.like_count:<6}")

def print_item_detail(item):
    """打印物品详细信息"""
    print(f"\n{'='*100}")
    print(f"[物品详情] ID: {item.id}")
    print(f"{'='*100}")
    print(f"类型:       {'招领' if item.type == 'found' else '寻物'}")
    print(f"标题:       {item.title}")
    print(f"描述:       {item.description}")
    print(f"类别:       {item.category}")
    print(f"地点:       {item.location}")
    if item.latitude and item.longitude:
        print(f"坐标:       {item.latitude}, {item.longitude}")
    print(f"联系方式:   {item.contact}")
    print(f"状态:       {item.status}")
    print(f"发布人ID:   {item.user_id}")
    print(f"浏览量:     {item.view_count}")
    print(f"点赞数:     {item.like_count}")
    print(f"创建时间:   {item.created_at}")
    print(f"更新时间:   {item.updated_at}")
    print(f"{'='*100}\n")

def main():
    with app.app_context():
        # 查询所有物品
        all_items = LostItem.query.order_by(LostItem.created_at.desc()).all()
        found_items = LostItem.query.filter_by(type='found').order_by(LostItem.created_at.desc()).all()
        lost_items = LostItem.query.filter_by(type='lost').order_by(LostItem.created_at.desc()).all()

        # 统计信息
        print("\n" + "="*100)
        print("数据库统计信息")
        print("="*100)
        print(f"总物品数:   {len(all_items)}")
        print(f"招领物品:   {len(found_items)}")
        print(f"寻物物品:   {len(lost_items)}")
        print(f"用户数:     {User.query.count()}")

        # 按状态统计
        pending = LostItem.query.filter_by(status='pending').count()
        claimed = LostItem.query.filter_by(status='claimed').count()
        returned = LostItem.query.filter_by(status='returned').count()
        print(f"\n状态统计:")
        print(f"  待认领:    {pending}")
        print(f"  已认领:    {claimed}")
        print(f"  已归还:    {returned}")

        # 显示招领物品列表
        print_table(found_items, '招领物品列表')

        # 显示寻物物品列表
        print_table(lost_items, '寻物物品列表')

        # 如果有物品，显示第一条详情
        if all_items:
            print("\n[示例] 显示第一条物品的详细信息:")
            print_item_detail(all_items[0])

        print("\n[*] 查看完成!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
