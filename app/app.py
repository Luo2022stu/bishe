from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import or_
import os
import hashlib
import secrets
import base64

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
database_type = os.getenv('DATABASE_TYPE', 'sqlite')

if database_type == 'mysql':
    # MySQL 配置
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_database = os.getenv('MYSQL_DATABASE', 'lost_found')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    print(f'[√] 使用 MySQL 数据库: {mysql_host}:{mysql_port}/{mysql_database}')

elif database_type == 'postgresql':
    # PostgreSQL 配置
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = os.getenv('POSTGRES_PORT', '5432')
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', '')
    postgres_database = os.getenv('POSTGRES_DATABASE', 'lost_found')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_database}'
    print(f'[√] 使用 PostgreSQL 数据库: {postgres_host}:{postgres_port}/{postgres_database}')

elif database_type == 'mssql':
    # SQL Server 配置
    mssql_host = os.getenv('MSSQL_HOST', 'localhost')
    mssql_port = os.getenv('MSSQL_PORT', '1433')
    mssql_user = os.getenv('MSSQL_USER', 'sa')
    mssql_password = os.getenv('MSSQL_PASSWORD', '')
    mssql_database = os.getenv('MSSQL_DATABASE', 'lost_found')
    mssql_driver = os.getenv('MSSQL_DRIVER', 'ODBC+Driver+17+for+SQL+Server')
    
    # SQL Server 连接字符串
    connection_string = f'mssql+pyodbc://{mssql_user}:{mssql_password}@{mssql_host}:{mssql_port}/{mssql_database}?driver={mssql_driver}'
    app.config['SQLALCHEMY_DATABASE_URI'] = connection_string
    print(f'[√] 使用 SQL Server 数据库: {mssql_host}:{mssql_port}/{mssql_database}')

else:
    # SQLite 配置（默认）
    sqlite_path = os.getenv('SQLITE_DB_PATH', 'lost_found.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, sqlite_path)
    print(f'[√] 使用 SQLite 数据库: {os.path.join(basedir, sqlite_path)}')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrets.token_hex(32)

db = SQLAlchemy(app)

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=True)  # 真实姓名
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')  # user, admin
    credit_score = db.Column(db.Integer, default=100)  # 信用分，初始100
    is_muted = db.Column(db.Boolean, default=False)  # 是否被禁言
    muted_until = db.Column(db.DateTime, nullable=True)  # 禁言截止时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.sha256(password.encode()).hexdigest()

    def is_muted_now(self):
        """检查当前是否被禁言"""
        if not self.is_muted:
            return False
        if self.muted_until:
            now = datetime.now(timezone.utc)
            if self.muted_until.tzinfo is None:
                muted_end = self.muted_until.replace(tzinfo=timezone.utc)
            else:
                muted_end = self.muted_until
            if now > muted_end:
                # 禁言期已过，自动解除
                self.is_muted = False
                self.muted_until = None
                db.session.commit()
                return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name or self.username,  # 如果没有设置name，则使用username
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'credit_score': self.credit_score,
            'is_muted': self.is_muted,
            'muted_until': self.muted_until.strftime('%Y-%m-%d %H:%M:%S') if self.muted_until else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 验证码存储（生产环境应使用Redis）
verification_codes = {}

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), default='found')  # found (失物招领) 或 lost (失物找寻)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=True)  # 纬度
    longitude = db.Column(db.Float, nullable=True)  # 经度
    contact = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, claimed, returned
    audit_status = db.Column(db.String(20), default='pending')  # pending (待审核), approved (已通过), rejected (已拒绝)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    view_count = db.Column(db.Integer, default=0)  # 浏览量
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    images = db.Column(db.Text, nullable=True)  # 图片列表，以逗号分隔的base64字符串
    is_hidden = db.Column(db.Boolean, default=False)  # 是否被隐藏
    hidden_until = db.Column(db.DateTime, nullable=True)  # 隐藏截止时间
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self, check_like=False, current_user_id=None):
        username = '未知'
        if self.user_id:
            try:
                user = User.query.get(self.user_id)
                username = user.username if user else '未知'
            except:
                username = '未知'

        data = {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact': self.contact,
            'status': self.status,
            'audit_status': self.audit_status,
            'user_id': self.user_id,
            'username': username,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'is_hidden': self.is_hidden,
            'hidden_until': self.hidden_until.strftime('%Y-%m-%d %H:%M:%S') if self.hidden_until else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'images': self.images.split(',') if self.images and isinstance(self.images, str) else []
        }

        # 检查当前用户是否已点赞
        if check_like and current_user_id:
            is_liked = ItemLike.query.filter_by(
                user_id=current_user_id,
                item_id=self.id
            ).first() is not None
            data['is_liked'] = is_liked
        else:
            data['is_liked'] = False

        return data

# 社区交流数据模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='交流')  # 交流、建议、求助
    image = db.Column(db.Text, nullable=True)  # 帖子图片（base64格式）
    audit_status = db.Column(db.String(20), default='pending')  # pending (待审核), approved (已通过), rejected (已拒绝)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    view_count = db.Column(db.Integer, default=0)  # 浏览量
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    comment_count = db.Column(db.Integer, default=0)  # 评论数
    is_hidden = db.Column(db.Boolean, default=False)  # 是否被隐藏
    hidden_until = db.Column(db.DateTime, nullable=True)  # 隐藏截止时间
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_comments=False):
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'image': self.image,
            'audit_status': self.audit_status,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知用户',
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'is_hidden': self.is_hidden,
            'hidden_until': self.hidden_until.strftime('%Y-%m-%d %H:%M:%S') if self.hidden_until else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        if include_comments:
            # 只返回顶级评论（parent_id 为 None 的评论）
            top_level_comments = [c for c in self.comments if c.parent_id is None]
            data['comments'] = [comment.to_dict() for comment in top_level_comments]
        return data

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # 回复评论
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'content': self.content,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知用户',
            'parent_id': self.parent_id,
            'like_count': self.like_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'replies': [reply.to_dict() for reply in self.replies] if self.replies else []
        }

# 举报记录模型
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 举报人
    target_type = db.Column(db.String(20), nullable=False)  # 'item' (物品) 或 'post' (帖子)
    target_id = db.Column(db.Integer, nullable=False)  # 被举报内容的ID
    reason = db.Column(db.String(200), nullable=False)  # 举报原因
    status = db.Column(db.String(20), default='pending')  # pending (待处理), processed (已处理)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref=db.backref('reports_made', lazy=True))

    def to_dict(self):
        reporter_name = '未知'
        if self.reporter:
            reporter_name = self.reporter.username

        # 获取被举报内容的信息
        target_info = None
        target_author_name = '未知'
        if self.target_type == 'item':
            item = LostItem.query.get(self.target_id)
            if item:
                if item.user_id:
                    author = User.query.get(item.user_id)
                    target_author_name = author.username if author else '未知'
                target_info = {
                    'id': item.id,
                    'title': item.title,
                    'type': item.type,
                    'author_id': item.user_id,
                    'author_name': target_author_name
                }
        elif self.target_type == 'post':
            post = Post.query.get(self.target_id)
            if post:
                if post.user_id:
                    author = User.query.get(post.user_id)
                    target_author_name = author.username if author else '未知'
                target_info = {
                    'id': post.id,
                    'title': post.title,
                    'author_id': post.user_id,
                    'author_name': target_author_name
                }

        return {
            'id': self.id,
            'reporter_id': self.reporter_id,
            'reporter_name': reporter_name,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'target_info': target_info,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('post_likes', lazy=True))
    post = db.relationship('Post', backref=db.backref('likes', lazy=True))

# 物品点赞模型
class ItemLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('lost_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('item_likes', lazy=True))
    item = db.relationship('LostItem', backref=db.backref('likes', lazy=True))

# 推送通知模型
class SystemNotification(db.Model):
    """系统推送通知"""
    __tablename__ = 'system_notification'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tag = db.Column(db.String(50), default='公告')  # 公告、系统、活动等
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tag': self.tag,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 评论点赞模型
class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('comment_likes', lazy=True))
    comment = db.relationship('Comment', backref=db.backref('likes', lazy=True))

# 浏览历史模型
class BrowseHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'found' 或 'lost' 或 'post'
    item_id = db.Column(db.Integer, nullable=False)  # 物品ID或帖子ID
    title = db.Column(db.String(200), nullable=False)
    viewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('browse_histories', lazy=True, order_by='desc(BrowseHistory.viewed_at)'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'title': self.title,
            'viewed_at': self.viewed_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 用户设置模型
class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    email_notification = db.Column(db.Boolean, default=True)
    sms_notification = db.Column(db.Boolean, default=False)
    show_location = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default='light')

    user = db.relationship('User', backref=db.backref('settings', uselist=False, lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_notification': self.email_notification,
            'sms_notification': self.sms_notification,
            'show_location': self.show_location,
            'theme': self.theme
        }

# 智能存储柜模型
class SmartLocker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_number = db.Column(db.String(20), unique=True, nullable=False)  # 柜子编号，如 A001
    location = db.Column(db.String(200), nullable=False)  # 柜子位置
    status = db.Column(db.String(20), default='available')  # available(可用), occupied(占用), maintenance(维护)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关联存储的物品
    items = db.relationship('LockerItem', backref='locker', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'locker_number': self.locker_number,
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 存储柜物品模型
class LockerItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('smart_locker.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)  # 物品名称
    description = db.Column(db.Text)  # 物品描述
    pickup_code = db.Column(db.String(10), unique=True, nullable=False)  # 取件码
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 存入者ID
    recipient_phone = db.Column(db.String(20))  # 接收人手机号
    status = db.Column(db.String(20), default='pending')  # pending(待取), claimed(已取), expired(过期)
    stored_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 存入时间
    picked_up_at = db.Column(db.DateTime)  # 取出时间
    expires_at = db.Column(db.DateTime)  # 过期时间

    # 关联发送者和接收者
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_locker_items')

    def to_dict(self):
        try:
            sender_name = None
            if hasattr(self, 'sender') and self.sender:
                try:
                    if hasattr(self.sender, 'username'):
                        sender_name = self.sender.username
                except:
                    pass

            locker_number = None
            locker_location = None
            if hasattr(self, 'locker') and self.locker:
                try:
                    if hasattr(self.locker, 'locker_number'):
                        locker_number = self.locker.locker_number
                    if hasattr(self.locker, 'location'):
                        locker_location = self.locker.location
                except:
                    pass

            stored_at = None
            if self.stored_at:
                try:
                    stored_at = self.stored_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass

            picked_up_at = None
            if self.picked_up_at:
                try:
                    picked_up_at = self.picked_up_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass

            expires_at = None
            if self.expires_at:
                try:
                    expires_at = self.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass

            return {
                'id': self.id,
                'locker_id': self.locker_id,
                'locker_number': locker_number,
                'locker_location': locker_location,
                'item_name': self.item_name,
                'description': self.description,
                'pickup_code': self.pickup_code,
                'sender_id': self.sender_id,
                'sender_name': sender_name,
                'recipient_phone': self.recipient_phone,
                'status': self.status,
                'stored_at': stored_at,
                'picked_up_at': picked_up_at,
                'expires_at': expires_at
            }
        except Exception as e:
            # 如果出现错误，返回基本数据
            return {
                'id': getattr(self, 'id', None),
                'locker_id': getattr(self, 'locker_id', None),
                'item_name': getattr(self, 'item_name', None),
                'description': getattr(self, 'description', None),
                'pickup_code': getattr(self, 'pickup_code', None),
                'sender_id': getattr(self, 'sender_id', None),
                'recipient_phone': getattr(self, 'recipient_phone', None),
                'status': getattr(self, 'status', None),
                'error': str(e)
            }

# 用户反馈模型
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)  # 反馈内容
    reply = db.Column(db.Text)  # 管理员回复
    status = db.Column(db.String(20), default='pending')  # pending(待处理), replied(已回复)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    replied_at = db.Column(db.DateTime)  # 回复时间

    user = db.relationship('User', backref='feedbacks')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'content': self.content,
            'reply': self.reply,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'replied_at': self.replied_at.strftime('%Y-%m-%d %H:%M:%S') if self.replied_at else None
        }

# 用户通知模型
class UserNotification(db.Model):
    """用户个人通知"""
    __tablename__ = 'user_notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # comment(评论), like(点赞), reply(回复), feedback(反馈回复), mute(禁言通知), audit(审核通知), pending_audit(待审核通知)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)  # 是否已读
    related_id = db.Column(db.Integer)  # 关联ID(帖子ID/评论ID等)
    related_type = db.Column(db.String(50))  # 关联类型(post/comment/feedback等)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'is_read': self.is_read,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 好友关系模型
class Friendship(db.Model):
    """好友关系"""
    __tablename__ = 'friendship'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending(待验证), accepted(已通过), rejected(已拒绝)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', foreign_keys=[user_id], backref='sent_friendships')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='received_friendships')

    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 聊天消息模型
class ChatMessage(db.Model):
    """聊天消息"""
    __tablename__ = 'chat_message'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 发送取件码短信函数
def send_pickup_code_sms(phone, pickup_code, item_name, locker_number):
    """
    发送取件码短信给接收人

    Args:
        phone: 接收人手机号
        pickup_code: 取件码
        item_name: 物品名称
        locker_number: 柜号
    """
    try:
        # 构建短信内容
        message = f"【校园失物招领系统】您有一个物品待取：{item_name}，柜号：{locker_number}，取件码：{pickup_code}。请于7天内凭取件码取件。"

        # 在实际应用中，这里应该调用短信API发送短信
        # 例如：阿里云短信、腾讯云短信等
        # send_sms(phone, message)

        # 为了演示，我们在控制台打印取件码信息
        print(f'[智能柜] 取件码短信发送到 {phone}:')
        print(f'       内容: {message}')

        # 这里可以记录短信发送日志
        print(f'[智能柜] 短信发送成功 - 手机号: {phone}, 取件码: {pickup_code}, 物品: {item_name}, 柜号: {locker_number}')

    except Exception as e:
        print(f'[智能柜] 发送取件码短信失败: {e}')
        # 短信发送失败不影响物品存入流程

# 初始化数据库
with app.app_context():
    db.create_all()
    # 刷新元数据以解决缓存问题
    db.metadata.reflect(bind=db.engine)
    # 创建默认管理员账户（如果不存在）
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@school.edu', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('默认管理员账户已创建: admin / admin123')

# 用户认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未登录'}), 401
        # 简单验证，实际应用应使用JWT
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '未登录'}), 401
        # 简单验证，实际应用应解析JWT获取用户角色
        return f(*args, **kwargs)
    return decorated_function

# 用户认证API
@app.route('/api/auth/send-code', methods=['POST'])
def send_verification_code():
    """发送验证码"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': '请输入手机号'}), 400
    
    # 验证手机号格式
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({'error': '手机号格式不正确'}), 400
    
    # 检查手机号是否已注册
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': '该手机号已被注册'}), 400
    
    # 生成6位验证码
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # 存储验证码（5分钟有效期）
    verification_codes[phone] = {
        'code': code,
        'expire_time': datetime.utcnow().timestamp() + 300  # 5分钟后过期
    }
    
    # 在实际应用中，这里应该调用短信API发送验证码
    # 为了演示，我们在控制台打印验证码
    print(f'验证码已发送到 {phone}: {code}')
    
    return jsonify({
        'message': '验证码已发送',
        'code': code  # 仅用于演示，生产环境不应返回验证码
    })

@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code():
    """验证验证码"""
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    
    if not phone or not code:
        return jsonify({'error': '请提供手机号和验证码'}), 400
    
    # 检查验证码是否存在
    if phone not in verification_codes:
        return jsonify({'error': '验证码不存在或已过期'}), 400
    
    # 检查验证码是否过期
    stored_data = verification_codes[phone]
    if datetime.utcnow().timestamp() > stored_data['expire_time']:
        del verification_codes[phone]
        return jsonify({'error': '验证码已过期'}), 400
    
    # 验证验证码
    if stored_data['code'] != code:
        return jsonify({'error': '验证码错误'}), 400
    
    # 验证成功，删除验证码
    del verification_codes[phone]
    
    return jsonify({'message': '验证码正确'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    name = data.get('name', username)  # 如果没有提供name，则使用username
    email = data.get('email')
    phone = data.get('phone')
    code = data.get('code')
    password = data.get('password')
    role = data.get('role', 'user')  # 默认为普通用户

    if not username or not email or not phone or not code or not password:
        return jsonify({'error': '请填写完整信息'}), 400

    # 验证手机号格式
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({'error': '手机号格式不正确'}), 400

    # 验证角色类型
    if role not in ['user', 'admin']:
        return jsonify({'error': '角色类型不正确'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    # 检查邮箱是否已注册
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 400

    # 检查手机号是否已注册
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': '该手机号已被注册'}), 400

    # 验证验证码（如果验证码已使用，需要重新发送）
    # 这里简化处理，实际应用应该在验证成功后标记验证码已使用

    user = User(username=username, name=name, email=email, phone=phone, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': '注册成功',
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 简单返回用户信息，实际应用应返回JWT token
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'token': f'token_{user.id}_{secrets.token_hex(16)}'
    })

@app.route('/api/auth/send-reset-code', methods=['POST'])
def send_reset_code():
    """发送重置密码验证码"""
    data = request.json
    phone = data.get('phone')
    
    if not phone:
        return jsonify({'error': '请输入手机号'}), 400
    
    # 验证手机号格式
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({'error': '手机号格式不正确'}), 400
    
    # 检查手机号是否已注册
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'error': '该手机号未注册'}), 400
    
    # 生成6位验证码
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # 存储验证码（5分钟有效期）
    verification_codes[phone] = {
        'code': code,
        'expire_time': datetime.utcnow().timestamp() + 300  # 5分钟后过期
    }
    
    # 在实际应用中，这里应该调用短信API发送验证码
    # 为了演示，我们在控制台打印验证码
    print(f'重置密码验证码已发送到 {phone}: {code}')
    
    return jsonify({
        'message': '验证码已发送',
        'code': code  # 仅用于演示，生产环境不应返回验证码
    })

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.json
    phone = data.get('phone')
    code = data.get('code')
    new_password = data.get('new_password')
    
    if not phone or not code or not new_password:
        return jsonify({'error': '请填写完整信息'}), 400
    
    # 验证手机号格式
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({'error': '手机号格式不正确'}), 400
    
    # 验证密码长度
    if len(new_password) < 6:
        return jsonify({'error': '密码长度至少6位'}), 400
    
    # 检查验证码是否存在
    if phone not in verification_codes:
        return jsonify({'error': '验证码不存在或已过期'}), 400
    
    # 检查验证码是否过期
    stored_data = verification_codes[phone]
    if datetime.utcnow().timestamp() > stored_data['expire_time']:
        del verification_codes[phone]
        return jsonify({'error': '验证码已过期'}), 400
    
    # 验证验证码
    if stored_data['code'] != code:
        return jsonify({'error': '验证码错误'}), 400
    
    # 查找用户
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 更新密码
    user.set_password(new_password)
    db.session.commit()
    
    # 验证成功，删除验证码
    del verification_codes[phone]
    
    return jsonify({'message': '密码重置成功'})

@app.route('/api/auth/user', methods=['GET'])
def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if user:
            return jsonify({'user': user.to_dict()})
        return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

# API路由
@app.route('/api/items', methods=['GET'])
def get_items():
    """获取物品列表，支持按类型筛选和限制数量"""
    item_type = request.args.get('type', '').strip()  # found 或 lost
    limit = request.args.get('limit', '').strip()
    now = datetime.now(timezone.utc)

    query = LostItem.query.filter_by(audit_status='approved').filter(
        (LostItem.is_hidden == False) | (LostItem.hidden_until < now)
    )

    # 按类型筛选
    if item_type in ['found', 'lost']:
        query = query.filter_by(type=item_type)

    # 限制数量
    if limit and limit.isdigit():
        limit_num = int(limit)
        items = query.order_by(LostItem.created_at.desc()).limit(limit_num).all()
    else:
        items = query.order_by(LostItem.created_at.desc()).all()

    return jsonify([item.to_dict() for item in items])

@app.route('/api/items', methods=['POST'])
def create_item():
    try:
        # 判断是否为FormData（上传图片）
        if 'Content-Type' in request.headers and 'multipart/form-data' in request.headers['Content-Type']:
            # FormData格式
            data = request.form
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            # 验证必填字段
            required_fields = ['title', 'description', 'category', 'location', 'contact']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'缺少必填字段: {field}'}), 400

            user_id = None
            if token and token.startswith('token_'):
                try:
                    user_id = int(token.split('_')[1])
                    # 检查用户是否被禁言
                    user = User.query.get(user_id)
                    if user and user.is_muted_now():
                        return jsonify({'error': '您已被禁言，无法发布物品'}), 403
                except:
                    pass

            # 处理图片上传
            images = []
            for key in request.files:
                file = request.files[key]
                if file and file.filename:
                    # 读取图片为base64
                    import base64
                    file_data = file.read()
                    images.append(base64.b64encode(file_data).decode('utf-8'))

            # 转换经纬度为浮点数或None
            latitude = None
            longitude = None
            if data.get('latitude'):
                try:
                    latitude = float(data['latitude'])
                except:
                    pass
            if data.get('longitude'):
                try:
                    longitude = float(data['longitude'])
                except:
                    pass

            new_item = LostItem(
                type=data.get('type', 'found'),  # 默认为失物招领
                title=data['title'],
                description=data['description'],
                category=data['category'],
                location=data['location'],
                latitude=latitude,  # 纬度
                longitude=longitude,  # 经度
                contact=data['contact'],
                user_id=user_id,
                images=','.join(images) if images else None
            )
        else:
            # JSON格式
            data = request.json
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            # 验证必填字段
            required_fields = ['title', 'description', 'category', 'location', 'contact']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'缺少必填字段: {field}'}), 400

            user_id = None
            if token and token.startswith('token_'):
                try:
                    user_id = int(token.split('_')[1])
                    # 检查用户是否被禁言
                    user = User.query.get(user_id)
                    if user and user.is_muted_now():
                        return jsonify({'error': '您已被禁言，无法发布物品'}), 403
                except:
                    pass

            # 转换经纬度为浮点数或None
            latitude = None
            longitude = None
            if data.get('latitude'):
                try:
                    latitude = float(data['latitude'])
                except:
                    pass
            if data.get('longitude'):
                try:
                    longitude = float(data['longitude'])
                except:
                    pass

            new_item = LostItem(
                type=data.get('type', 'found'),  # 默认为失物招领
                title=data['title'],
                description=data['description'],
                category=data['category'],
                location=data['location'],
                latitude=latitude,  # 纬度
                longitude=longitude,  # 经度
                contact=data['contact'],
                user_id=user_id
            )

        db.session.add(new_item)
        db.session.commit()

        # 给管理员发送审核通知
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notification = UserNotification(
                user_id=admin.id,
                type='pending_audit',
                title='新物品待审核',
                content=f'用户{"已登录" if user_id else "匿名"}发布了新的{"失物招领" if new_item.type == "found" else "失物找寻"}信息: "{new_item.title}"',
                is_read=False,
                related_id=new_item.id,
                related_type='item'
            )
            db.session.add(notification)
        db.session.commit()

        return jsonify(new_item.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        print(f"创建物品失败: {str(e)}")
        import traceback
        traceback.print_exc()

        # 解析数据库错误
        error_msg = str(e)
        if 'NOT NULL constraint failed' in error_msg:
            return jsonify({'error': '数据验证失败：缺少必填字段'}), 400
        elif 'UNIQUE constraint failed' in error_msg:
            return jsonify({'error': '数据重复'}), 400
        elif 'could not convert' in error_msg:
            return jsonify({'error': '数据类型错误：请检查输入格式'}), 400

        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = LostItem.query.get_or_404(item_id)
    data = request.json
    
    # 检查权限
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token and token.startswith('token_'):
        try:
            user_id = int(token.split('_')[1])
            user = User.query.get(user_id)
            if user and user.role != 'admin' and item.user_id != user_id:
                return jsonify({'error': '无权限操作'}), 403
        except:
            pass
    
    if 'status' in data:
        item.status = data['status']
    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = LostItem.query.get_or_404(item_id)

    # 检查权限
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token and token.startswith('token_'):
        try:
            user_id = int(token.split('_')[1])
            user = User.query.get(user_id)
            if user and user.role != 'admin' and item.user_id != user_id:
                return jsonify({'error': '无权限操作'}), 403
        except:
            pass

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'})

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """获取单个物品详情"""
    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({'error': '物品不存在'}), 404

    # 检查是否被隐藏
    now = datetime.now(timezone.utc)
    if item.is_hidden and (item.hidden_until is None or item.hidden_until > now):
        return jsonify({'error': '该内容已被隐藏'}), 403

    item_dict = item.to_dict()

    # 添加发布者用户名
    if item.user_id:
        user = User.query.get(item.user_id)
        item_dict['username'] = user.username if user else '未知'
    else:
        item_dict['username'] = '未知'

    return jsonify(item_dict)

@app.route('/api/items/<int:item_id>/like', methods=['POST'])
def like_item(item_id):
    """物品点赞/取消点赞"""
    item = LostItem.query.get_or_404(item_id)

    # 检查登录状态
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    # 检查是否已经点赞
    existing_like = ItemLike.query.filter_by(
        user_id=user_id,
        item_id=item_id
    ).first()

    if existing_like:
        # 取消点赞
        db.session.delete(existing_like)
        item.like_count -= 1
        liked = False
    else:
        # 添加点赞
        like = ItemLike(user_id=user_id, item_id=item_id)
        db.session.add(like)
        item.like_count += 1
        liked = True

    db.session.commit()
    return jsonify({
        'like_count': item.like_count,
        'liked': liked
    })

@app.route('/api/items/<int:item_id>/like/check', methods=['GET'])
def check_item_like_status(item_id):
    """检查用户是否已点赞该物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'liked': False})

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'liked': False})

    existing_like = ItemLike.query.filter_by(
        user_id=user_id,
        item_id=item_id
    ).first()

    return jsonify({'liked': existing_like is not None})

@app.route('/api/items/search', methods=['GET'])
def search_items():
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    now = datetime.now(timezone.utc)

    print(f'[搜索] 关键词: "{keyword}", 分类: "{category}"')  # 调试日志

    try:
        query = LostItem.query.filter(
            (LostItem.is_hidden == False) | (LostItem.hidden_until < now)
        )
        if keyword:
            # 支持多关键词搜索：将关键词按空格分割，任意一个匹配即可
            keywords = [k.strip() for k in keyword.split() if k.strip()]

            if keywords:
                # 对每个关键词构建搜索条件
                conditions = []
                for kw in keywords:
                    conditions.append(LostItem.title.contains(kw))
                    conditions.append(LostItem.description.contains(kw))
                    conditions.append(LostItem.location.contains(kw))
                    conditions.append(LostItem.category.contains(kw))

                # 使用OR连接所有条件（任意关键词匹配任意字段即可）
                if conditions:
                    query = query.filter(or_(*conditions))
        if category:
            query = query.filter(LostItem.category == category)

        items = query.filter_by(audit_status='approved').order_by(LostItem.created_at.desc()).all()
        print(f'[搜索] 找到 {len(items)} 条结果')  # 调试日志

        return jsonify([item.to_dict() for item in items])
    except Exception as e:
        print(f'[搜索] 错误: {str(e)}')
        print(f'[搜索] 错误类型: {type(e).__name__}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

# 统计数据API（公开接口）
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取系统统计数据"""
    found_count = LostItem.query.filter_by(type='found').count()
    lost_count = LostItem.query.filter_by(type='lost').count()
    users_count = User.query.count()
    posts_count = Post.query.count()

    return jsonify({
        'found_count': found_count,
        'lost_count': lost_count,
        'users_count': users_count,
        'posts_count': posts_count
    })


# ============================================================================
# AI图像识别服务模块
# ============================================================================

def recognize_with_baidu(image_data):
    """使用百度AI通用物体识别API识别图片内容，同时进行OCR文字识别"""
    try:
        from aip import AipImageClassify
        from aip import AipOcr
        
        app_id = os.getenv('BAIDU_APP_ID')
        api_key = os.getenv('BAIDU_API_KEY')
        secret_key = os.getenv('BAIDU_SECRET_KEY')
        
        if not app_id or not api_key or not secret_key:
            return None, "百度AI配置不完整"
        
        # 1. 物体识别
        image_classify_client = AipImageClassify(app_id, api_key, secret_key)
        object_result = image_classify_client.advancedGeneral(image_data)
        
        if 'error_code' in object_result:
            return None, f"百度AI识别失败: {object_result.get('error_msg', '未知错误')}"
        
        # 解析物体识别结果
        items = object_result.get('result', [])
        if not items:
            return None, "未识别到任何物体"
        
        # 取置信度最高的结果
        best_item = max(items, key=lambda x: x.get('score', 0))
        
        # 转换为统一格式
        recognition_result = {
            'category': '其他',
            'subcategory': '未分类',
            'description': best_item.get('keyword', '未知物体'),
            'suggestions': ['请补充物品的详细描述', '或重新上传更清晰的图片'],
            'details': {
                'baidu_result': best_item,
                'root': best_item.get('root', ''),
                'score': best_item.get('score', 0)
            },
            'confidence': best_item.get('score', 0),
            'ocr_text': None,
            'ocr_details': None
        }
        
        # 尝试根据百度AI的root字段映射到我们的分类
        root = best_item.get('root', '').lower()
        keyword = best_item.get('keyword', '').lower()
        
        # 分类映射（可根据百度AI的返回结果扩展）
        if '电子设备' in root or '手机' in keyword or '电脑' in keyword or '耳机' in keyword:
            recognition_result['category'] = '电子设备'
            recognition_result['subcategory'] = '其他'
        elif '证件' in root or '卡片' in keyword or '钱包' in keyword:
            recognition_result['category'] = '证件卡片'
            recognition_result['subcategory'] = '其他'
        elif '生活用品' in root or '钥匙' in keyword or '水杯' in keyword:
            recognition_result['category'] = '生活用品'
            recognition_result['subcategory'] = '其他'
        elif '书籍' in root or '文具' in keyword:
            recognition_result['category'] = '书籍文具'
            recognition_result['subcategory'] = '其他'
        elif '服装' in root or '鞋' in keyword or '衣服' in keyword:
            recognition_result['category'] = '服装'
            recognition_result['subcategory'] = '其他'
        
        # 2. OCR文字识别（尝试识别图片中的文字）
        try:
            ocr_client = AipOcr(app_id, api_key, secret_key)
            ocr_result = ocr_client.basicGeneral(image_data)
            
            if 'words_result' in ocr_result and ocr_result['words_result']:
                # 提取所有文字行
                lines = [item['words'] for item in ocr_result['words_result']]
                recognition_result['ocr_text'] = '\n'.join(lines)
                recognition_result['ocr_details'] = ocr_result
                # 如果识别到文字，可以添加到描述或建议中
                if lines:
                    recognition_result['suggestions'].append(f'识别到文字: {lines[0][:30]}...')
        except Exception as ocr_error:
            # OCR失败不影响主要结果，仅记录日志
            print(f'[AI识别] 百度OCR识别失败: {ocr_error}')
        
        return recognition_result, None
        
    except ImportError:
        return None, "未安装百度AI SDK (baidu-aip)"
    except Exception as e:
        return None, f"百度AI识别异常: {str(e)}"


def recognize_with_tencent(image_data):
    """使用腾讯云AI图像识别API识别图片内容，同时进行OCR文字识别"""
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.tiia.v20190529 import tiia_client, models as tiia_models
        import base64
        import json
        
        secret_id = os.getenv('TENCENT_CLOUD_SECRET_ID')
        secret_key = os.getenv('TENCENT_CLOUD_SECRET_KEY')
        region = os.getenv('TENCENT_CLOUD_REGION', 'ap-guangzhou')
        
        if not secret_id or not secret_key:
            return None, "腾讯云AI配置不完整"
        
        # 使用腾讯云图像分析API
        cred = credential.Credential(secret_id, secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = "tiia.tencentcloudapi.com"
        
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        
        client = tiia_client.TiiaClient(cred, region, client_profile)
        
        # 构建请求参数
        req = tiia_models.DetectLabelRequest()
        req.ImageBase64 = base64.b64encode(image_data).decode('utf-8')
        
        resp = client.DetectLabel(req)
        
        # 解析响应
        labels = resp.Labels if hasattr(resp, 'Labels') else []
        
        if not labels:
            return None, "未识别到任何物体"
        
        # 取置信度最高的结果
        best_label = max(labels, key=lambda x: x.Confidence)
        
        # 转换为统一格式
        recognition_result = {
            'category': '其他',
            'subcategory': '未分类',
            'description': best_label.Name,
            'suggestions': ['请补充物品的详细描述', '或重新上传更清晰的图片'],
            'details': {
                'tencent_result': {
                    'name': best_label.Name,
                    'confidence': best_label.Confidence,
                    'first_category': best_label.FirstCategory if hasattr(best_label, 'FirstCategory') else '',
                    'second_category': best_label.SecondCategory if hasattr(best_label, 'SecondCategory') else ''
                }
            },
            'confidence': best_label.Confidence / 100.0,  # 腾讯云返回0-100的置信度
            'ocr_text': None,
            'ocr_details': None
        }
        
        # 尝试根据腾讯云的分类映射到我们的分类
        first_category = getattr(best_label, 'FirstCategory', '').lower()
        second_category = getattr(best_label, 'SecondCategory', '').lower()
        
        if '电子' in first_category or '电子' in second_category or '手机' in best_label.Name or '电脑' in best_label.Name:
            recognition_result['category'] = '电子设备'
            recognition_result['subcategory'] = '其他'
        elif '证件' in first_category or '卡片' in second_category or '钱包' in best_label.Name:
            recognition_result['category'] = '证件卡片'
            recognition_result['subcategory'] = '其他'
        elif '生活' in first_category or '日常' in second_category or '钥匙' in best_label.Name or '水杯' in best_label.Name:
            recognition_result['category'] = '生活用品'
            recognition_result['subcategory'] = '其他'
        elif '书籍' in first_category or '文具' in second_category:
            recognition_result['category'] = '书籍文具'
            recognition_result['subcategory'] = '其他'
        elif '服装' in first_category or '鞋' in second_category or '衣服' in best_label.Name:
            recognition_result['category'] = '服装'
            recognition_result['subcategory'] = '其他'
        
        # 2. OCR文字识别（尝试识别图片中的文字）
        try:
            # 导入腾讯云OCR模块
            from tencentcloud.ocr.v20181119 import ocr_client, models as ocr_models
            
            ocr_http_profile = HttpProfile()
            ocr_http_profile.endpoint = "ocr.tencentcloudapi.com"
            ocr_client_profile = ClientProfile()
            ocr_client_profile.httpProfile = ocr_http_profile
            
            ocr_client_instance = ocr_client.OcrClient(cred, region, ocr_client_profile)
            
            ocr_req = ocr_models.GeneralAccurateOCRRequest()
            ocr_req.ImageBase64 = base64.b64encode(image_data).decode('utf-8')
            
            ocr_resp = ocr_client_instance.GeneralAccurateOCR(ocr_req)
            
            # 解析OCR响应
            if hasattr(ocr_resp, 'TextDetections') and ocr_resp.TextDetections:
                # 提取所有文字行
                lines = [item.DetectedText for item in ocr_resp.TextDetections]
                recognition_result['ocr_text'] = '\n'.join(lines)
                recognition_result['ocr_details'] = {
                    'text_detections': [
                        {
                            'text': item.DetectedText,
                            'confidence': item.Confidence,
                            'polygon': item.Polygon if hasattr(item, 'Polygon') else []
                        }
                        for item in ocr_resp.TextDetections
                    ]
                }
                # 如果识别到文字，可以添加到描述或建议中
                if lines:
                    recognition_result['suggestions'].append(f'识别到文字: {lines[0][:30]}...')
        except ImportError:
            # OCR SDK可能未安装或版本不同，忽略
            print('[AI识别] 腾讯云OCR SDK未安装或导入失败，跳过文字识别')
        except TencentCloudSDKException as ocr_error:
            # OCR失败不影响主要结果，仅记录日志
            print(f'[AI识别] 腾讯云OCR识别失败: {ocr_error}')
        except Exception as ocr_error:
            print(f'[AI识别] 腾讯云OCR识别异常: {ocr_error}')
        
        return recognition_result, None
        
    except ImportError:
        return None, "未安装腾讯云AI SDK (tencentcloud-sdk-python)"
    except TencentCloudSDKException as e:
        return None, f"腾讯云AI识别失败: {str(e)}"
    except Exception as e:
        return None, f"腾讯云AI识别异常: {str(e)}"


def recognize_with_paddlepaddle(image_data):
    """使用百度飞桨(PaddlePaddle)进行图像识别"""
    try:
        import paddle
        import numpy as np
        from PIL import Image
        import io
        
        # 检查PaddlePaddle是否安装
        # 加载预训练模型（使用ResNet50）
        from paddle.vision.models import resnet50
        from paddle.vision import transforms as T
        
        # 加载模型
        model = resnet50(pretrained=True)
        model.eval()
        
        # 图像预处理
        transform = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 将字节数据转换为PIL图像
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        
        # 应用预处理
        input_tensor = transform(image)
        input_batch = input_tensor.unsqueeze(0)  # 添加批次维度
        
        # 推理
        with paddle.no_grad():
            output = model(input_batch)
        
        # 获取预测结果
        probabilities = paddle.nn.functional.softmax(output[0], axis=0)
        top5_probs, top5_indices = paddle.topk(probabilities, k=5)
        
        # 加载ImageNet类别标签
        import json
        import urllib.request
        try:
            url = "https://storage.googleapis.com/download.tensorflow.org/data/imagenet_class_index.json"
            response = urllib.request.urlopen(url)
            imagenet_classes = json.loads(response.read().decode())
            # 将索引映射到类别名称
            idx_to_class = {int(k): v[1] for k, v in imagenet_classes.items()}
        except:
            # 如果无法加载在线标签，使用本地映射
            idx_to_class = {}
            # 简单映射一些常见类别
            common_classes = {
                0: 'tench', 1: 'goldfish', 2: 'great_white_shark',  # 仅示例
                # 实际项目中应使用完整的1000个类别映射
            }
            idx_to_class = common_classes
        
        # 获取最佳预测
        top_idx = top5_indices[0].item()
        top_prob = top5_probs[0].item()
        top_class = idx_to_class.get(top_idx, f'class_{top_idx}')
        
        # 转换为统一格式
        recognition_result = {
            'category': '其他',
            'subcategory': '未分类',
            'description': top_class.replace('_', ' '),
            'suggestions': ['请补充物品的详细描述', '或重新上传更清晰的图片'],
            'details': {
                'paddle_result': {
                    'top_class': top_class,
                    'confidence': top_prob,
                    'top5': [
                        {'class': idx_to_class.get(idx.item(), f'class_{idx.item()}'), 'confidence': prob.item()}
                        for idx, prob in zip(top5_indices, top5_probs)
                    ]
                }
            },
            'confidence': top_prob,
            'ocr_text': None,
            'ocr_details': None
        }
        
        # 尝试根据预测类别映射到系统分类
        top_class_lower = top_class.lower()
        if 'phone' in top_class_lower or 'computer' in top_class_lower or 'laptop' in top_class_lower or 'tablet' in top_class_lower or 'headphone' in top_class_lower:
            recognition_result['category'] = '电子设备'
            recognition_result['subcategory'] = '其他'
        elif 'wallet' in top_class_lower or 'card' in top_class_lower or 'id' in top_class_lower or 'passport' in top_class_lower:
            recognition_result['category'] = '证件卡片'
            recognition_result['subcategory'] = '其他'
        elif 'key' in top_class_lower or 'bottle' in top_class_lower or 'cup' in top_class_lower or 'umbrella' in top_class_lower:
            recognition_result['category'] = '生活用品'
            recognition_result['subcategory'] = '其他'
        elif 'book' in top_class_lower or 'notebook' in top_class_lower or 'pen' in top_class_lower:
            recognition_result['category'] = '书籍文具'
            recognition_result['subcategory'] = '其他'
        elif 'clothing' in top_class_lower or 'shoe' in top_class_lower or 'hat' in top_class_lower or 'bag' in top_class_lower:
            recognition_result['category'] = '服装'
            recognition_result['subcategory'] = '其他'
        
        return recognition_result, None
        
    except ImportError as e:
        return None, f"未安装PaddlePaddle或相关依赖: {str(e)}"
    except Exception as e:
        return None, f"PaddlePaddle识别异常: {str(e)}"


def get_ai_recognition_result(image_data, filename):
    """
    获取AI识别结果，优先使用云服务，失败时回退到文件名匹配
    返回: (recognition_result, error_message, service_used)
    """
    ai_service = os.getenv('AI_SERVICE', 'none').lower()
    
    # 尝试使用百度AI
    if ai_service == 'baidu':
        result, error = recognize_with_baidu(image_data)
        if result:
            result['filename_info'] = {
                'original': filename,
                'recognition_based_on': 'baidu_ai',
                'suggestion': '基于百度AI图像识别结果'
            }
            return result, None, 'baidu'
        else:
            # 百度AI失败，记录日志并继续尝试文件名匹配
            print(f'[AI识别] 百度AI识别失败: {error}')
    
    # 尝试使用腾讯云AI
    elif ai_service == 'tencent':
        result, error = recognize_with_tencent(image_data)
        if result:
            result['filename_info'] = {
                'original': filename,
                'recognition_based_on': 'tencent_ai',
                'suggestion': '基于腾讯云AI图像识别结果'
            }
            return result, None, 'tencent'
        else:
            # 腾讯云AI失败，记录日志并继续尝试文件名匹配
            print(f'[AI识别] 腾讯云AI识别失败: {error}')
    
    # 尝试使用百度飞桨(PaddlePaddle)
    elif ai_service == 'paddlepaddle':
        result, error = recognize_with_paddlepaddle(image_data)
        if result:
            result['filename_info'] = {
                'original': filename,
                'recognition_based_on': 'paddlepaddle',
                'suggestion': '基于百度飞桨图像识别结果'
            }
            return result, None, 'paddlepaddle'
        else:
            # PaddlePaddle失败，记录日志并继续尝试文件名匹配
            print(f'[AI识别] 百度飞桨识别失败: {error}')
    
    # 使用文件名匹配（模拟AI识别）
    return None, "使用文件名关键词匹配", 'filename'


# ============================================================================
# AI识别API
# ============================================================================

# AI识别API
@app.route('/api/ai/recognize', methods=['POST'])
def ai_recognize():
    """AI识别图片中的物品"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': '未上传图片'}), 400

        file = request.files['image']
        image_data = file.read()
        
        # 调用AI识别服务
        recognition_result, error_msg, service_used = get_ai_recognition_result(image_data, file.filename)
        
        # 如果AI服务返回了结果，直接返回
        if recognition_result is not None:
            return jsonify(recognition_result)
        
        # 否则，使用文件名关键词匹配（原逻辑）
        # 注意：这里保留原有的文件名匹配逻辑作为后备方案
        # 由于代码较长，我们在此调用一个辅助函数来执行文件名匹配
        return jsonify(recognize_with_filename(file.filename, image_data))

    except Exception as e:
        return jsonify({'error': f'识别失败: {str(e)}'}), 500


@app.route('/api/ai/match-items', methods=['POST'])
def ai_match_items():
    """AI识别图片并匹配已发布的物品"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': '未上传图片'}), 400

        file = request.files['image']
        image_data = file.read()

        # 1. AI识别上传的图片
        recognition_result, error_msg, service_used = get_ai_recognition_result(image_data, file.filename)

        # 如果AI识别失败，使用文件名匹配
        if not recognition_result:
            recognition_result = recognize_with_filename(file.filename, image_data)

        # 2. 基于识别结果搜索匹配的物品
        category = recognition_result.get('category', '')
        description = recognition_result.get('description', '')

        # 获取所有已审核的物品
        items_query = LostItem.query.filter_by(audit_status='approved')
        now = datetime.now(timezone.utc)
        items_query = items_query.filter(
            (LostItem.is_hidden == False) | (LostItem.hidden_until < now)
        )

        # 按类别筛选
        if category and category != '其他' and category != '未分类':
            items_query = items_query.filter_by(category=category)

        # 获取所有候选物品
        items = items_query.order_by(LostItem.created_at.desc()).all()

        # 计算匹配分数
        matched_items = []

        for item in items:
            score = 0
            match_reasons = []

            # 类别匹配（50分）
            if category and item.category == category:
                score += 50
                match_reasons.append(f'类别匹配: {category}')

            # 标题关键词匹配（30分）
            if description:
                title_lower = item.title.lower()
                desc_lower = description.lower()
                common_words = set(desc_lower.split()) & set(title_lower.split())
                if common_words:
                    score += 30
                    match_reasons.append(f'关键词匹配: {", ".join(common_words)}')

            # 描述匹配（20分）
            if item.description:
                item_desc_lower = item.description.lower()
                desc_lower = description.lower()
                if desc_lower in item_desc_lower:
                    score += 20
                    match_reasons.append('描述相似')

            # 只保留匹配分数 >= 40 的物品
            if score >= 40:
                matched_items.append({
                    'item': item.to_dict(),
                    'score': score,
                    'match_reasons': match_reasons
                })

        # 按匹配分数降序排序
        matched_items.sort(key=lambda x: x['score'], reverse=True)
        matched_items = matched_items[:20]  # 限制返回20个

        # 添加发布者信息
        for matched in matched_items:
            item_dict = matched['item']
            if item_dict.get('user_id'):
                user = User.query.get(item_dict['user_id'])
                item_dict['username'] = user.username if user else '未知'
            else:
                item_dict['username'] = '未知'

        return jsonify({
            'recognition_result': recognition_result,
            'matched_items': matched_items,
            'total_matches': len(matched_items),
            'service_used': service_used
        })

    except Exception as e:
        return jsonify({'error': f'匹配失败: {str(e)}'}), 500


def recognize_with_filename(filename, image_data):
    """基于文件名的关键词匹配识别（原有逻辑）"""
    # 简化的AI识别逻辑（使用关键词匹配）
    # 实际项目中可以集成百度AI、腾讯云AI等
    # 这里模拟识别结果
    recognition_result = {
        'category': '其他',
        'subcategory': '未分类',
        'description': '无法识别具体物品',
        'suggestions': ['请尝试拍摄更清晰的照片', '可以添加物品描述进行搜索'],
        'details': {},
        'confidence': 0.0
    }

    # 基于图片文件名的简单识别（模拟）
    if filename is None:
        filename = ""
    filename = filename.lower()

    # 尝试从文件路径中提取更多信息
    # 有些浏览器会包含路径信息，比如 "C:\\Users\\xxx\\Desktop\\手机照片.jpg"
    # 提取可能的物品名称
    import re

    # 移除常见的文件扩展名和路径
    filename_clean = re.sub(r'[\\\/\._\-\s]+', ' ', filename)
    filename_clean = filename_clean.replace('jpg', '').replace('jpeg', '').replace('png', '').replace('webp', '')
    filename_clean = filename_clean.replace('img', '').replace('image', '').replace('photo', '').replace('picture', '')
    filename_clean = filename_clean.replace('微信图片', '').replace('wx', '').replace('照片', '')
    filename_clean = filename_clean.strip()

    # 提取可能的品牌和型号信息
    brand = None
    model = None
    color = None
    
    # 品牌关键词映射
    brand_keywords = {
        '苹果': ['苹果', 'iphone', 'ipad', 'macbook', 'airpods', 'apple'],
        '华为': ['华为', 'huawei', 'honor', '荣耀'],
        '小米': ['小米', 'mi', 'redmi', '红米'],
        '三星': ['三星', 'samsung', 'galaxy'],
        'oppo': ['oppo'],
        'vivo': ['vivo'],
        '索尼': ['索尼', 'sony'],
        '联想': ['联想', 'lenovo'],
        '戴尔': ['戴尔', 'dell'],
        '惠普': ['惠普', 'hp'],
        '耐克': ['耐克', 'nike'],
        '阿迪达斯': ['阿迪达斯', 'adidas'],
        '李宁': ['李宁', 'lining'],
        '安踏': ['安踏', 'anta']
    }
    
    # 颜色关键词
    color_keywords = ['黑', '白', '红', '蓝', '绿', '黄', '灰', '银', '金', '粉', '紫', '棕', '橙']
    
    # 尝试从文件名中提取品牌和型号
    for brand_name, keywords in brand_keywords.items():
        if any(keyword in filename_clean for keyword in keywords):
            brand = brand_name
            # 尝试提取型号（数字序列）
            model_match = re.search(r'(\d+[a-z]*\d*)', filename_clean)
            if model_match:
                model = model_match.group(1)
            break
    
    # 尝试提取颜色
    for c in color_keywords:
        if c in filename_clean:
            color = c
            break

    # 如果清理后的文件名包含中文或英文关键词，进行匹配
    # 证件卡片类
    card_keywords = ['钱包', 'wallet', '卡包', 'card', '身份证', 'idcard', '学生证', 'student', '银行卡', 'bank', '信用卡', 'credit']
    if any(keyword in filename or keyword in filename_clean for keyword in card_keywords):
        if any(keyword in filename or keyword in filename_clean for keyword in ['钱包', 'wallet', '卡包', 'card']):
            recognition_result = {
                'category': '证件卡片',
                'subcategory': '钱包/卡包',
                'description': '证件卡片类物品',
                'suggestions': ['请描述钱包的颜色、品牌、内部物品数量', '是否有挂饰或特殊标记'],
                'details': {'type': '钱包/卡包'},
                'confidence': 0.7
            }
        elif any(keyword in filename or keyword in filename_clean for keyword in ['身份证', 'idcard', '学生证', 'student']):
            recognition_result = {
                'category': '证件卡片',
                'subcategory': '证件',
                'description': '重要证件',
                'suggestions': ['请描述证件类型', '姓名是否可见', '是否有封面'],
                'details': {'type': '证件'},
                'confidence': 0.8
            }
        elif any(keyword in filename or keyword in filename_clean for keyword in ['银行卡', 'bank', '信用卡', 'credit']):
            recognition_result = {
                'category': '证件卡片',
                'subcategory': '银行卡',
                'description': '银行卡类物品',
                'suggestions': ['请描述银行卡发卡行', '卡面颜色'],
                'details': {'type': '银行卡'},
                'confidence': 0.7
            }

    # 电子设备类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['手机', 'phone', 'mobile', '苹果', 'iphone', '安卓', 'android', '华为', '小米', 'oppo', 'vivo']):
        # 构建更具体的描述
        desc = '手机'
        if brand:
            desc = f'{brand}手机'
            if model:
                desc = f'{brand} {model}手机'
        elif '苹果' in filename_clean or 'iphone' in filename_clean:
            desc = '苹果手机'
        elif '华为' in filename_clean or 'huawei' in filename_clean:
            desc = '华为手机'
        elif '小米' in filename_clean or 'mi' in filename_clean:
            desc = '小米手机'
        
        recognition_result = {
            'category': '电子设备',
            'subcategory': '手机',
            'description': desc,
            'suggestions': ['请描述手机品牌、型号', '颜色', '是否有手机壳或贴膜', '屏幕是否完好'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '手机'},
            'confidence': 0.8
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['电脑', 'laptop', 'notebook', 'macbook', '笔记本']):
        desc = '笔记本电脑'
        if brand:
            desc = f'{brand}笔记本电脑'
            if model:
                desc = f'{brand} {model}笔记本电脑'
        recognition_result = {
            'category': '电子设备',
            'subcategory': '电脑',
            'description': desc,
            'suggestions': ['请描述电脑品牌、型号', '颜色', '贴纸或贴膜情况', '尺寸大小'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '笔记本电脑'},
            'confidence': 0.8
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['平板', 'ipad', 'tablet', 'pad']):
        desc = '平板电脑'
        if brand:
            desc = f'{brand}平板电脑'
            if model:
                desc = f'{brand} {model}平板电脑'
        recognition_result = {
            'category': '电子设备',
            'subcategory': '平板电脑',
            'description': desc,
            'suggestions': ['请描述平板品牌、尺寸', '颜色', '是否有保护套'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '平板电脑'},
            'confidence': 0.8
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['耳机', 'earphone', 'headphone', 'airpods', '索尼']):
        desc = '耳机'
        if brand:
            desc = f'{brand}耳机'
            if model:
                desc = f'{brand} {model}耳机'
        recognition_result = {
            'category': '电子设备',
            'subcategory': '耳机',
            'description': desc,
            'suggestions': ['请描述耳机品牌、型号', '颜色', '有线或无线', '左/右耳机或完整'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '耳机'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['充电器', 'charger', '数据线', 'cable', 'usb', 'type-c', 'lightning']):
        recognition_result = {
            'category': '电子设备',
            'subcategory': '充电配件',
            'description': '充电器或数据线',
            'suggestions': ['请描述设备类型（安卓/苹果/Type-C）', '品牌', '长度'],
            'details': {'type': '充电配件'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['手表', 'watch', '手环', 'band']):
        desc = '智能手表或手环'
        if brand:
            desc = f'{brand}智能手表'
        recognition_result = {
            'category': '电子设备',
            'subcategory': '智能穿戴',
            'description': desc,
            'suggestions': ['请描述品牌、型号', '颜色', '表带材质'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '智能穿戴'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['充电宝', '移动电源', 'powerbank', 'power bank', '充电宝']):
        recognition_result = {
            'category': '电子设备',
            'subcategory': '充电设备',
            'description': '充电宝/移动电源',
            'suggestions': ['请描述容量大小', '品牌', '颜色', '接口类型（USB/Type-C）'],
            'details': {'type': '充电宝/移动电源'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['u盘', 'usb', '闪存盘', 'flash', 'u disk', '优盘']):
        recognition_result = {
            'category': '电子设备',
            'subcategory': '存储设备',
            'description': 'U盘/闪存盘',
            'suggestions': ['请描述容量大小', '品牌', '颜色', '接口类型（USB 2.0/3.0）'],
            'details': {'type': 'U盘/闪存盘'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['硬盘', 'harddisk', 'hdd', 'ssd', '移动硬盘']):
        recognition_result = {
            'category': '电子设备',
            'subcategory': '存储设备',
            'description': '硬盘/移动硬盘',
            'suggestions': ['请描述容量大小', '品牌', '类型（机械/固态）', '接口类型'],
            'details': {'type': '硬盘/移动硬盘'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['鼠标', 'mouse', '键盘', 'keyboard', '键鼠']):
        desc = '鼠标或键盘'
        if '鼠标' in filename_clean or 'mouse' in filename_clean:
            desc = '鼠标'
        elif '键盘' in filename_clean or 'keyboard' in filename_clean:
            desc = '键盘'
        recognition_result = {
            'category': '电子设备',
            'subcategory': '电脑外设',
            'description': desc,
            'suggestions': ['请描述品牌、型号', '颜色', '有线或无线', '是否有特殊功能'],
            'details': {'type': desc},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['摄像头', 'camera', 'webcam', '相机', '摄影']):
        recognition_result = {
            'category': '电子设备',
            'subcategory': '摄像设备',
            'description': '摄像头/相机',
            'suggestions': ['请描述品牌、型号', '类型（网络摄像头/数码相机）', '颜色'],
            'details': {'type': '摄像头/相机'},
            'confidence': 0.7
        }

    # 书籍文具类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['书', 'book', '教材', '课本', '笔记', 'notebook']):
        recognition_result = {
            'category': '书籍文具',
            'subcategory': '书籍',
            'description': '书籍类物品',
            'suggestions': ['请描述书名、作者', '出版社', '封面颜色', '是否有笔记或标记'],
            'details': {'type': '书籍'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['笔', 'pen', 'pencil', '文具', 'stationery']):
        recognition_result = {
            'category': '书籍文具',
            'subcategory': '文具',
            'description': '文具类物品',
            'suggestions': ['请描述文具类型和数量', '品牌', '颜色', '是否有包装'],
            'details': {'type': '文具'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['包', 'bag', '书包', 'backpack', '背包', '手提包']):
        recognition_result = {
            'category': '书籍文具',
            'subcategory': '包袋',
            'description': '包类物品',
            'suggestions': ['请描述包的类型、大小', '颜色和品牌', '是否有挂饰', '内部物品'],
            'details': {'type': '包袋'},
            'confidence': 0.7
        }

    # 生活用品类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['钥匙', 'key', '锁', 'lock']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '钥匙',
            'description': '钥匙类物品',
            'suggestions': ['请描述钥匙的类型（宿舍/教室/车钥匙）', '数量', '是否有钥匙扣或挂饰', '品牌特征'],
            'details': {'type': '钥匙'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['水杯', 'cup', 'bottle', '保温杯', '水壶']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '水杯',
            'description': '水杯类物品',
            'suggestions': ['请描述水杯的材质', '颜色和图案', '品牌', '容量大小'],
            'details': {'type': '水杯'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['伞', 'umbrella', '雨伞']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '雨伞',
            'description': '雨伞类物品',
            'suggestions': ['请描述雨伞颜色和图案', '折叠还是长柄', '品牌', '是否有破损'],
            'details': {'type': '雨伞'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['眼镜', 'glass', '太阳镜', 'sunglass']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '眼镜',
            'description': '眼镜类物品',
            'suggestions': ['请描述眼镜的类型（近视/太阳/老花）', '镜框颜色和材质', '品牌', '是否有眼镜盒'],
            'details': {'type': '眼镜'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['帽子', 'hat', 'cap', '头巾']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '帽子',
            'description': '帽类物品',
            'suggestions': ['请描述帽子的类型和颜色', '品牌', '是否有装饰物'],
            'details': {'type': '帽子'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['围巾', 'scarf', '手套', 'glove']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '配饰',
            'description': '围巾或手套',
            'suggestions': ['请描述物品类型', '颜色和图案', '材质', '品牌'],
            'details': {'type': '配饰'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['口罩', 'mask', '医用口罩', '防护口罩']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '防护用品',
            'description': '口罩',
            'suggestions': ['请描述口罩类型（医用/普通）', '颜色', '品牌', '是否有独立包装'],
            'details': {'type': '口罩'},
            'confidence': 0.8
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['纸巾', 'tissue', '湿巾', '湿纸巾', '纸']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '卫生用品',
            'description': '纸巾/湿巾',
            'suggestions': ['请描述纸巾类型（抽纸/手帕纸）', '品牌', '是否有包装'],
            'details': {'type': '纸巾/湿巾'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['毛巾', 'towel', '浴巾', '手巾']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '卫生用品',
            'description': '毛巾/浴巾',
            'suggestions': ['请描述毛巾大小', '颜色和图案', '材质', '是否有标签'],
            'details': {'type': '毛巾/浴巾'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['梳子', 'comb', '镜子', 'mirror', '化妆镜']):
        desc = '梳子或镜子'
        if '梳子' in filename_clean or 'comb' in filename_clean:
            desc = '梳子'
        elif '镜子' in filename_clean or 'mirror' in filename_clean:
            desc = '镜子'
        recognition_result = {
            'category': '生活用品',
            'subcategory': '个人护理',
            'description': desc,
            'suggestions': ['请描述物品材质', '颜色', '品牌', '是否有包装'],
            'details': {'type': desc},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['牙刷', 'toothbrush', '牙膏', 'toothpaste', '牙具']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '个人护理',
            'description': '牙刷/牙膏',
            'suggestions': ['请描述品牌', '颜色', '是否有包装'],
            'details': {'type': '牙刷/牙膏'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['剪刀', 'scissors', '刀', 'knife', '工具']):
        recognition_result = {
            'category': '生活用品',
            'subcategory': '工具',
            'description': '剪刀或刀具',
            'suggestions': ['请描述工具类型', '大小', '颜色', '是否有保护套'],
            'details': {'type': '工具'},
            'confidence': 0.6
        }

    # 服装类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['衣服', 'cloth', '外套', 'coat', 'jacket', 'shirt', '上衣']):
        desc = '上衣'
        if brand:
            desc = f'{brand}上衣'
        recognition_result = {
            'category': '服装',
            'subcategory': '上衣',
            'description': desc,
            'suggestions': ['请描述衣服的类型（外套/毛衣/T恤等）', '颜色和图案', '品牌', '尺码信息'],
            'details': {'brand': brand, 'color': color, 'type': '上衣'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['裤子', 'pants', 'jean', '短裤', '短']):
        desc = '裤子'
        if brand:
            desc = f'{brand}裤子'
        recognition_result = {
            'category': '服装',
            'subcategory': '下装',
            'description': desc,
            'suggestions': ['请描述裤子类型（牛仔裤/休闲裤等）', '颜色', '品牌', '尺码信息'],
            'details': {'brand': brand, 'color': color, 'type': '裤子'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['鞋', 'shoe', '运动鞋', 'sneaker', '皮鞋']):
        desc = '鞋子'
        if brand:
            desc = f'{brand}鞋子'
            if model:
                desc = f'{brand} {model}鞋子'
        recognition_result = {
            'category': '服装',
            'subcategory': '鞋类',
            'description': desc,
            'suggestions': ['请描述鞋子类型和品牌', '颜色', '尺码', '新旧程度', '是否有特殊标识'],
            'details': {'brand': brand, 'model': model, 'color': color, 'type': '鞋子'},
            'confidence': 0.7
        }

    # 体育用品类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['球', 'ball', '篮球', 'basketball', '足球', 'soccer', '羽毛球', 'badminton', '乒乓球', 'pingpong']):
        recognition_result = {
            'category': '体育用品',
            'subcategory': '球类',
            'description': '球类物品',
            'suggestions': ['请描述球的类型', '品牌', '颜色', '是否有签名或标记'],
            'details': {'type': '球类'},
            'confidence': 0.7
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['球拍', 'racket', '球鞋', '体育', 'sport']):
        recognition_result = {
            'category': '体育用品',
            'subcategory': '运动器材',
            'description': '体育器材',
            'suggestions': ['请描述器材类型和品牌', '颜色', '型号', '是否有使用痕迹'],
            'details': {'type': '运动器材'},
            'confidence': 0.6
        }

    # 珠宝首饰类
    elif any(keyword in filename or keyword in filename_clean for keyword in ['项链', 'necklace', '手链', 'bracelet', '戒指', 'ring', '耳环', 'earring']):
        recognition_result = {
            'category': '珠宝首饰',
            'subcategory': '首饰',
            'description': '首饰类物品',
            'suggestions': ['请描述首饰类型', '材质（金/银/其他）', '颜色', '品牌', '是否有特殊图案或刻字'],
            'details': {'type': '首饰'},
            'confidence': 0.7
        }

    # 其他物品
    elif any(keyword in filename or keyword in filename_clean for keyword in ['包', 'bag', '箱子', 'box', '行李', 'luggage']):
        recognition_result = {
            'category': '其他',
            'subcategory': '包箱类',
            'description': '包箱类物品',
            'suggestions': ['请描述物品类型和大小', '颜色和品牌', '是否有锁', '特殊标识'],
            'details': {'type': '包箱类'},
            'confidence': 0.6
        }
    elif any(keyword in filename or keyword in filename_clean for keyword in ['玩具', 'toy', '公仔', '玩偶']):
        recognition_result = {
            'category': '其他',
            'subcategory': '玩具',
            'description': '玩具类物品',
            'suggestions': ['请描述玩具类型', '颜色', '品牌', '是否有破损'],
            'details': {'type': '玩具'},
            'confidence': 0.6
        }

    # 尝试解析EXIF元数据
    try:
        from PIL import Image
        from io import BytesIO
        import PIL.ExifTags
        
        img_stream = BytesIO(image_data)
        img = Image.open(img_stream)
        
        exif_data = {}
        # 尝试获取EXIF数据，兼容不同PIL版本
        exif = None
        if hasattr(img, 'getexif'):
            exif = img.getexif()
        elif hasattr(img, '_getexif'):
            exif = img._getexif()
        
        if exif:
            for tag, value in exif.items():
                decoded = PIL.ExifTags.TAGS.get(tag, tag)
                exif_data[decoded] = value
            
            # 提取有用的EXIF信息
            exif_info = {}
            if 'Make' in exif_data:
                exif_info['camera_brand'] = exif_data['Make']
            if 'Model' in exif_data:
                exif_info['camera_model'] = exif_data['Model']
            if 'DateTime' in exif_data:
                exif_info['capture_time'] = exif_data['DateTime']
            if 'ImageWidth' in exif_data and 'ImageHeight' in exif_data:
                exif_info['dimensions'] = f"{exif_data['ImageWidth']}x{exif_data['ImageHeight']}"
            
            if exif_info:
                recognition_result['exif'] = exif_info
                # 如果EXIF中有相机品牌，可以辅助识别
                if 'camera_brand' in exif_info and recognition_result['category'] == '其他':
                    recognition_result['category'] = '电子设备'
                    recognition_result['subcategory'] = '相机'
                    recognition_result['description'] = f"{exif_info['camera_brand']}相机"
                    recognition_result['confidence'] = 0.9
    except Exception as e:
        # EXIF解析失败，忽略
        pass

    # 如果识别结果仍然是默认的，尝试根据文件名中的数字序列猜测
    if recognition_result['category'] == '其他' and recognition_result['description'] == '无法识别具体物品':
        # 检查文件名中是否有数字序列（可能是型号）
        model_match = re.search(r'(\d+[a-z]*\d*)', filename_clean)
        if model_match:
            recognition_result['description'] = f'型号可能为 {model_match.group(1)} 的物品'
            recognition_result['suggestions'] = ['请补充物品的详细描述', '或重新上传更清晰的图片']
            recognition_result['confidence'] = 0.3

    # 添加文件名信息，帮助用户理解识别过程
    recognition_result['filename_info'] = {
        'original': filename if filename else '',
        'cleaned': filename_clean,
        'recognition_based_on': 'filename_keywords',
        'suggestion': '为确保准确识别，请确保文件名包含物品名称（如：iphone_手机.jpg、黑色钱包.jpg）'
    }
    
    # 添加OCR相关字段（文件名匹配无OCR，设为None）
    recognition_result['ocr_text'] = None
    recognition_result['ocr_details'] = None

    return recognition_result

# 推送通知API
@app.route('/api/system-notifications', methods=['GET'])
def get_system_notifications():
    """获取系统推送通知列表"""
    try:
        notifications = SystemNotification.query.filter_by(is_active=True).order_by(
            SystemNotification.created_at.desc()
        ).limit(5).all()
        return jsonify([notif.to_dict() for notif in notifications])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-notifications/<int:notif_id>', methods=['GET'])
def get_system_notification_detail(notif_id):
    """获取单个系统推送通知详情"""
    try:
        notification = SystemNotification.query.get(notif_id)
        if not notification:
            return jsonify({'error': '通知不存在'}), 404
        return jsonify(notification.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-notifications', methods=['POST'])
def create_system_notification():
    """创建系统推送通知（需要管理员权限）"""
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': '标题和内容不能为空'}), 400

        # 创建系统推送通知（用于首页重要推送版块）
        notification = SystemNotification(
            title=data['title'],
            content=data['content'],
            tag=data.get('tag', '公告'),
            is_active=True
        )

        db.session.add(notification)
        db.session.flush()  # 获取通知ID

        # 给所有用户发送个人通知
        all_users = User.query.all()
        for user in all_users:
            user_notification = UserNotification(
                user_id=user.id,
                type='system',
                title=data['title'],
                content=data['content'],
                is_read=False,
                related_id=notification.id,
                related_type='system_notification'
            )
            db.session.add(user_notification)

        db.session.commit()

        print(f'[系统通知] 创建了新的系统通知，已发送给 {len(all_users)} 个用户')

        return jsonify(notification.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 管理员专用的系统通知管理API
@app.route('/api/admin/system-notifications', methods=['GET'])
def admin_get_system_notifications():
    """管理员获取所有系统推送通知列表"""
    try:
        notifications = SystemNotification.query.order_by(
            SystemNotification.created_at.desc()
        ).all()
        return jsonify([notif.to_dict() for notif in notifications])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-notifications', methods=['POST'])
def admin_create_system_notification():
    """管理员创建系统推送通知"""
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': '标题和内容不能为空'}), 400

        # 创建系统推送通知（用于首页重要推送版块）
        notification = SystemNotification(
            title=data['title'],
            content=data['content'],
            tag=data.get('tag', '公告'),
            is_active=True
        )

        db.session.add(notification)
        db.session.flush()  # 获取通知ID

        # 给所有用户发送个人通知
        all_users = User.query.all()
        for user in all_users:
            user_notification = UserNotification(
                user_id=user.id,
                type='system',
                title=data['title'],
                content=data['content'],
                is_read=False,
                related_id=notification.id,
                related_type='system_notification'
            )
            db.session.add(user_notification)

        db.session.commit()

        print(f'[系统通知] 管理员创建了新的系统通知，已发送给 {len(all_users)} 个用户')

        return jsonify(notification.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-notifications/<int:notif_id>/toggle', methods=['PUT'])
def admin_toggle_system_notification(notif_id):
    """管理员切换系统通知的启用/停用状态"""
    try:
        notification = SystemNotification.query.get_or_404(notif_id)
        notification.is_active = not notification.is_active
        db.session.commit()
        return jsonify(notification.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/system-notifications/<int:notif_id>', methods=['DELETE'])
def admin_delete_system_notification(notif_id):
    """管理员删除系统推送通知"""
    try:
        notification = SystemNotification.query.get_or_404(notif_id)

        # 同时删除相关的用户通知
        UserNotification.query.filter_by(
            related_id=notif_id,
            related_type='system_notification'
        ).delete()

        db.session.delete(notification)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notif_id>', methods=['PUT'])
def update_notification(notif_id):
    """更新推送通知（需要管理员权限）"""
    try:
        notification = SystemNotification.query.get_or_404(notif_id)
        data = request.get_json()

        if 'title' in data:
            notification.title = data['title']
        if 'content' in data:
            notification.content = data['content']
        if 'tag' in data:
            notification.tag = data['tag']
        if 'is_active' in data:
            notification.is_active = data['is_active']

        db.session.commit()
        return jsonify(notification.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notif_id>', methods=['DELETE'])
def delete_notification(notif_id):
    """删除推送通知（需要管理员权限）"""
    try:
        notification = SystemNotification.query.get_or_404(notif_id)
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 社区交流API
@app.route('/api/posts', methods=['GET'])
def get_posts():
    """获取帖子列表"""
    category = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    now = datetime.now(timezone.utc)

    try:
        query = Post.query.filter_by(audit_status='approved').filter(
            (Post.is_hidden == False) | (Post.hidden_until < now)
        )
        if category:
            query = query.filter_by(category=category)
        if keyword:
            query = query.filter(
                (Post.title.contains(keyword)) |
                (Post.content.contains(keyword))
            )

        posts = query.order_by(Post.created_at.desc()).all()
        return jsonify([post.to_dict() for post in posts])
    except Exception as e:
        print(f'[帖子搜索] 错误: {str(e)}')
        print(f'[帖子搜索] 错误类型: {type(e).__name__}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """获取帖子详情"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    # 检查是否被隐藏
    now = datetime.now(timezone.utc)
    if post.is_hidden and (post.hidden_until is None or post.hidden_until > now):
        return jsonify({'error': '该内容已被隐藏'}), 403

    post.view_count += 1
    db.session.commit()

    # 检查当前用户是否已点赞
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    is_liked = False
    if token and token.startswith('token_'):
        try:
            user_id = int(token.split('_')[1])
            existing_like = PostLike.query.filter_by(user_id=user_id, post_id=post_id).first()
            is_liked = existing_like is not None
        except:
            pass

    post_data = post.to_dict(include_comments=True)
    post_data['is_liked'] = is_liked
    return jsonify(post_data)


@app.route('/api/posts/hot', methods=['GET'])
def get_hot_posts():
    """获取热帖列表（基于浏览量、点赞数和评论数）"""
    limit = int(request.args.get('limit', 5))
    now = datetime.now(timezone.utc)

    # 计算热度分数：浏览量 + 点赞数*2 + 评论数*3
    from sqlalchemy import func, desc

    posts = Post.query.filter_by(audit_status='approved').filter(
        (Post.is_hidden == False) | (Post.hidden_until < now)
    ).order_by(
        desc(
            Post.view_count + Post.like_count * 2 + Post.comment_count * 3
        )
    ).limit(limit).all()

    return jsonify([post.to_dict() for post in posts])

@app.route('/api/posts', methods=['POST'])
def create_post():
    """创建帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    # 检查用户是否被禁言
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if user.is_muted_now():
        return jsonify({'error': '您已被禁言，无法发布帖子'}), 403

    # 检查是否是表单数据（FormData）
    is_form_data = request.content_type and 'multipart/form-data' in request.content_type

    if is_form_data:
        # 使用FormData上传
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '交流')
        image_file = request.files.get('image')

        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400

        # 处理图片
        image_data = None
        if image_file and image_file.filename:
            try:
                image_bytes = image_file.read()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
            except Exception as e:
                print(f"图片处理失败: {e}")
                return jsonify({'error': '图片处理失败'}), 400

        post = Post(
            title=title,
            content=content,
            category=category,
            image=image_data,
            user_id=user_id
        )
    else:
        # JSON上传，不包含图片
        data = request.json
        if not data.get('title') or not data.get('content'):
            return jsonify({'error': '标题和内容不能为空'}), 400

        post = Post(
            title=data['title'],
            content=data['content'],
            category=data.get('category', '交流'),
            image=data.get('image'),
            user_id=user_id
        )

    db.session.add(post)
    db.session.commit()

    # 给管理员发送审核通知
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notification = UserNotification(
            user_id=admin.id,
            type='pending_audit',
            title='新帖子待审核',
            content=f'用户 {user.username} 发布了新帖子: "{post.title}"',
            is_read=False,
            related_id=post.id,
            related_type='post'
        )
        db.session.add(notification)
    db.session.commit()

    return jsonify(post.to_dict()), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """更新帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401
    
    post = Post.query.get_or_404(post_id)
    if post.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403
    
    data = request.json
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    if 'category' in data:
        post.category = data['category']
    
    post.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(post.to_dict())

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_user_post(post_id):
    """删除帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401
    
    post = Post.query.get_or_404(post_id)
    user = User.query.get(user_id)
    
    if post.user_id != user_id and (not user or user.role != 'admin'):
        return jsonify({'error': '无权限操作'}), 403
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': '帖子已删除'})

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    """点赞/取消点赞帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    post = Post.query.get_or_404(post_id)
    user = User.query.get(user_id)
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=user_id).first()

    if existing_like:
        db.session.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        liked = False
    else:
        like = PostLike(post_id=post_id, user_id=user_id)
        db.session.add(like)
        post.like_count += 1
        liked = True

        # 给帖主发送点赞通知
        if post.user_id != user_id:
            notification = UserNotification(
                user_id=post.user_id,
                type='like',
                title='您的帖子收到了点赞',
                content=f'{user.username} 点赞了您的帖子"{post.title}"',
                is_read=False,
                related_id=post.id,
                related_type='post'
            )
            db.session.add(notification)

    db.session.commit()
    return jsonify({'liked': liked, 'like_count': post.like_count})

@app.route('/api/posts/<int:post_id>/like/check', methods=['GET'])
def check_post_like_status(post_id):
    """检查用户是否已点赞该帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'liked': False})

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'liked': False})

    existing_like = PostLike.query.filter_by(
        user_id=user_id,
        post_id=post_id
    ).first()

    return jsonify({'liked': existing_like is not None})

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_public_post_comments(post_id):
    """获取帖子的所有评论"""
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.desc()).all()

    # 获取当前用户ID
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = None
    if token and token.startswith('token_'):
        try:
            user_id = int(token.split('_')[1])
        except:
            pass

    # 为每个评论添加点赞状态
    comments_data = []
    for comment in comments:
        comment_dict = comment.to_dict()
        if user_id:
            existing_like = CommentLike.query.filter_by(user_id=user_id, comment_id=comment.id).first()
            comment_dict['is_liked'] = existing_like is not None
        else:
            comment_dict['is_liked'] = False

        # 为回复也添加点赞状态
        if comment_dict.get('replies'):
            for reply in comment_dict['replies']:
                if user_id:
                    existing_like = CommentLike.query.filter_by(user_id=user_id, comment_id=reply['id']).first()
                    reply['is_liked'] = existing_like is not None
                else:
                    reply['is_liked'] = False

        comments_data.append(comment_dict)

    return jsonify(comments_data)

@app.route('/api/comments/<int:comment_id>/replies', methods=['POST'])
def create_reply(comment_id):
    """回复评论"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    # 检查用户是否被禁言
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if user.is_muted_now():
        return jsonify({'error': '您已被禁言，无法发表回复'}), 403

    parent_comment = Comment.query.get_or_404(comment_id)
    data = request.json

    if not data.get('content'):
        return jsonify({'error': '回复内容不能为空'}), 400

    reply = Comment(
        post_id=parent_comment.post_id,
        content=data['content'],
        user_id=user_id,
        parent_id=comment_id
    )
    db.session.add(reply)

    # 更新帖子的评论计数
    post = Post.query.get(parent_comment.post_id)
    post.comment_count += 1

    # 给被回复的评论作者发送通知
    if parent_comment.user_id != user_id:
        notification = UserNotification(
            user_id=parent_comment.user_id,
            type='reply',
            title='您的评论收到了回复',
            content=f'{user.username} 回复了您的评论: {data["content"][:50]}...' if len(data['content']) > 50 else data['content'],
            is_read=False,
            related_id=reply.id,
            related_type='comment'
        )
        db.session.add(notification)

    db.session.commit()
    print(f'[回复] 用户 {user.username} 回复了评论 {comment_id}，内容：{data["content"]}')

    return jsonify(reply.to_dict())

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    # 检查用户是否被禁言
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if user.is_muted_now():
        return jsonify({'error': '您已被禁言，无法发表评论'}), 403

    post = Post.query.get_or_404(post_id)
    data = request.json

    if not data.get('content'):
        return jsonify({'error': '评论内容不能为空'}), 400

    comment = Comment(
        post_id=post_id,
        content=data['content'],
        user_id=user_id,
        parent_id=data.get('parent_id')
    )
    db.session.add(comment)
    post.comment_count += 1

    # 如果是回复评论,给评论作者发送通知
    parent_id = data.get('parent_id')
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if parent_comment and parent_comment.user_id != user_id:
            notification = UserNotification(
                user_id=parent_comment.user_id,
                type='reply',
                title='您的评论收到了回复',
                content=f'{user.username} 回复了您的评论: {data["content"][:50]}...' if len(data['content']) > 50 else data['content'],
                is_read=False,
                related_id=comment.id,
                related_type='comment'
            )
            db.session.add(notification)

    # 给帖主发送评论通知(如果是新评论)
    elif post.user_id != user_id:
        notification = UserNotification(
            user_id=post.user_id,
            type='comment',
            title='您的帖子收到了新评论',
            content=f'{user.username} 评论了您的帖子"{post.title}": {data["content"][:50]}...' if len(data['content']) > 50 else data['content'],
            is_read=False,
            related_id=post.id,
            related_type='post'
        )
        db.session.add(notification)

    db.session.commit()
    return jsonify(comment.to_dict()), 201

@app.route('/api/comments/<int:comment_id>', methods=['GET'])
def get_comment_detail(comment_id):
    """获取评论详情"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    return jsonify(comment.to_dict())

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """删除评论"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get(user_id)
    post = Post.query.get(comment.post_id)

    # 权限检查：评论作者、管理员、或帖主
    if comment.user_id != user_id and (not user or user.role != 'admin') and (not post or post.user_id != user_id):
        return jsonify({'error': '无权限操作'}), 403

    db.session.delete(comment)
    if post:
        post.comment_count = max(0, post.comment_count - 1)
    db.session.commit()
    return jsonify({'message': '评论已删除'})

@app.route('/api/report', methods=['POST'])
def create_report():
    """举报内容（物品或帖子）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    # 检查用户是否被禁言
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    if user.is_muted_now():
        return jsonify({'error': '您已被禁言，无法进行举报'}), 403

    data = request.json
    target_type = data.get('target_type')  # 'item' 或 'post'
    target_id = data.get('target_id')
    reason = data.get('reason')

    if not target_type or not target_id:
        return jsonify({'error': '缺少必要参数'}), 400

    if target_type not in ['item', 'post']:
        return jsonify({'error': '无效的举报类型'}), 400

    if not reason or len(reason) > 200:
        return jsonify({'error': '举报原因不能为空且不超过200字'}), 400

    # 检查是否已经举报过该内容
    existing_report = Report.query.filter_by(
        reporter_id=user_id,
        target_type=target_type,
        target_id=target_id
    ).first()

    if existing_report:
        return jsonify({'error': '您已经举报过该内容'}), 400

    # 验证被举报内容是否存在
    target = None
    if target_type == 'item':
        target = LostItem.query.get(target_id)
        if not target:
            return jsonify({'error': '物品不存在'}), 404
    elif target_type == 'post':
        target = Post.query.get(target_id)
        if not target:
            return jsonify({'error': '帖子不存在'}), 404

    # 检查该内容被举报次数（已处理的举报）
    processed_count = Report.query.filter_by(
        target_type=target_type,
        target_id=target_id,
        status='processed'
    ).count()

    # 如果已被举报超过5次，隐藏3天
    if processed_count >= 5:
        author = User.query.get(target.user_id) if target.user_id else None
        if author:
            # 发送告诫通知
            notification = UserNotification(
                user_id=author.id,
                type='system',
                title='您的作品多次被举报',
                content=f'您发布的{"物品" if target_type == "item" else "帖子"}已被多次举报，已被隐藏3天。请谨慎发言，维护良好的社区环境。',
                is_read=False,
                related_id=target.id,
                related_type=target_type
            )
            db.session.add(notification)

        # 隐藏内容3天
        target.is_hidden = True
        target.hidden_until = datetime.now(timezone.utc) + timedelta(days=3)
        db.session.commit()
        return jsonify({'message': '该内容因多次举报已被隐藏3天'}), 200

    # 创建举报记录
    report = Report(
        reporter_id=user_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        status='pending'
    )
    db.session.add(report)

    db.session.commit()

    return jsonify({
        'message': '举报成功',
        'report': report.to_dict()
    }), 201

@app.route('/api/report/check', methods=['GET'])
def check_report_status():
    """检查用户是否已举报过某内容"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'reported': False})

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'reported': False})

    target_type = request.args.get('target_type')  # 'item' 或 'post'
    target_id = request.args.get('target_id')

    if not target_type or not target_id:
        return jsonify({'reported': False})

    try:
        target_id = int(target_id)
    except:
        return jsonify({'reported': False})

    if target_type not in ['item', 'post']:
        return jsonify({'reported': False})

    existing_report = Report.query.filter_by(
        reporter_id=user_id,
        target_type=target_type,
        target_id=target_id
    ).first()

    return jsonify({'reported': existing_report is not None})

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    """管理员获取所有举报"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])

@app.route('/api/admin/reports/<int:report_id>/audit', methods=['POST'])
def audit_report(report_id):
    """管理员审核举报"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    report = Report.query.get_or_404(report_id)
    data = request.get_json()
    action = data.get('action')  # 'approve' (通过举报) 或 'reject' (拒绝举报)

    if action not in ['approve', 'reject']:
        return jsonify({'error': '无效的操作'}), 400

    if report.status != 'pending':
        return jsonify({'error': '该举报已被处理'}), 400

    if action == 'approve':
        # 通过举报：扣除作者信用分10分
        target = None
        if report.target_type == 'item':
            target = LostItem.query.get(report.target_id)
        elif report.target_type == 'post':
            target = Post.query.get(report.target_id)

        if target:
            # 扣除被举报内容作者的信用分10分
            if target.user_id:
                author = User.query.get(target.user_id)
                if author:
                    author.credit_score = max(0, author.credit_score - 10)

                    # 检查信用分是否为0，如果是则禁言一周
                    if author.credit_score == 0 and not author.is_muted:
                        author.is_muted = True
                        author.muted_until = datetime.now(timezone.utc) + timedelta(days=7)

                        # 发送禁言通知
                        notification = UserNotification(
                            user_id=author.id,
                            type='mute',
                            title='您已被禁言',
                            content='由于您的信用分已降为0,您已被禁言一周。请遵守社区规范。',
                            is_read=False,
                            related_id=None,
                            related_type='mute'
                        )
                        db.session.add(notification)

                    # 检查该内容被举报次数（已处理的举报）
                    processed_count = Report.query.filter_by(
                        target_type=report.target_type,
                        target_id=report.target_id,
                        status='processed'
                    ).count()

                    # 如果已被举报超过5次，才隐藏内容3天
                    if processed_count >= 5:
                        target.is_hidden = True
                        target.hidden_until = datetime.now(timezone.utc) + timedelta(days=3)

                    # 发送审核通过通知（信用分扣除）
                    notification = UserNotification(
                        user_id=author.id,
                        type='audit',
                        title='您发布的内容被举报',
                        content=f'您发布的{"物品" if report.target_type == "item" else "帖子"}因举报已被扣除信用分10分。请谨慎发言，维护良好的社区环境。',
                        is_read=False,
                        related_id=target.id,
                        related_type=report.target_type
                    )
                    db.session.add(notification)

        report.status = 'processed'

    elif action == 'reject':
        # 拒绝举报：不删除内容
        report.status = 'processed'

    db.session.commit()

    return jsonify({'message': f'举报审核{"通过" if action == "approve" else "拒绝"}成功', 'status': report.status})

@app.route('/api/admin/reports/approve-all', methods=['POST'])
def approve_all_reports():
    """一键通过所有待处理举报"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    # 获取所有待处理的举报
    pending_reports = Report.query.filter_by(status='pending').all()

    if not pending_reports:
        return jsonify({'message': '没有待处理的举报', 'count': 0})

    approved_count = 0

    for report in pending_reports:
        try:
            # 获取被举报内容
            target = None
            if report.target_type == 'item':
                target = LostItem.query.get(report.target_id)
            elif report.target_type == 'post':
                target = Post.query.get(report.target_id)

            if target:
                # 扣除信用分
                if target.user_id:
                    author = User.query.get(target.user_id)
                    if author:
                        author.credit_score = max(0, author.credit_score - 10)

                        # 信用分为0则禁言
                        if author.credit_score == 0 and not author.is_muted:
                            author.is_muted = True
                            author.muted_until = datetime.now(timezone.utc) + timedelta(days=7)

                            # 禁言通知
                            notification = UserNotification(
                                user_id=author.id,
                                type='mute',
                                title='您已被禁言',
                                content='由于您的信用分已降为0,您已被禁言一周。请遵守社区规范。',
                                is_read=False,
                                related_id=None,
                                related_type='mute'
                            )
                            db.session.add(notification)

                        # 检查该内容被举报次数（已处理的举报）
                        processed_count = Report.query.filter_by(
                            target_type=report.target_type,
                            target_id=report.target_id,
                            status='processed'
                        ).count()

                        # 如果已被举报超过5次，才隐藏内容3天
                        if processed_count >= 5:
                            target.is_hidden = True
                            target.hidden_until = datetime.now(timezone.utc) + timedelta(days=3)

                        # 扣除信用分通知
                        notification = UserNotification(
                            user_id=author.id,
                            type='audit',
                            title='您发布的内容被举报',
                            content=f'您发布的{"物品" if report.target_type == "item" else "帖子"}因举报已被扣除信用分10分。请遵守社区规范。',
                            is_read=False,
                            related_id=target.id,
                            related_type=report.target_type
                        )
                        db.session.add(notification)

            # 标记为已处理
            report.status = 'processed'
            approved_count += 1

        except Exception as e:
            print(f'处理举报 {report.id} 时出错: {e}')
            continue

    db.session.commit()

    return jsonify({
        'message': f'成功通过 {approved_count} 条举报',
        'count': approved_count
    })

@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    """评论点赞/取消点赞"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '请先登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    comment = Comment.query.get_or_404(comment_id)

    # 检查是否已经点赞
    existing_like = CommentLike.query.filter_by(
        user_id=user_id,
        comment_id=comment_id
    ).first()

    if existing_like:
        # 取消点赞
        db.session.delete(existing_like)
        comment.like_count = max(0, comment.like_count - 1)
        liked = False
    else:
        # 点赞
        new_like = CommentLike(user_id=user_id, comment_id=comment_id)
        db.session.add(new_like)
        comment.like_count += 1
        liked = True

    db.session.commit()
    return jsonify({
        'like_count': comment.like_count,
        'liked': liked
    })

# 管理员API
@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401
    
    user = User.query.get_or_404(user_id)
    data = request.json
    if 'role' in data:
        user.role = data['role']
        db.session.commit()
    
    return jsonify(user.to_dict())

# 个人中心API
@app.route('/api/profile', methods=['GET'])
def get_profile():
    """获取个人中心信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    # 获取用户发布的信息
    my_items = LostItem.query.filter_by(user_id=user_id).order_by(LostItem.created_at.desc()).all()
    my_posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    
    # 获取浏览历史（最近20条）
    browse_history = BrowseHistory.query.filter_by(user_id=user_id).order_by(BrowseHistory.viewed_at.desc()).limit(20).all()
    
    # 获取点赞的帖子
    liked_posts = []
    for like in user.post_likes:
        if like.post:
            liked_posts.append(like.post)
    
    # 获取用户设置
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'user': user.to_dict(),
        'items': [item.to_dict() for item in my_items],
        'posts': [post.to_dict() for post in my_posts],
        'browse_history': [history.to_dict() for history in browse_history],
        'liked_posts': [post.to_dict() for post in liked_posts],
        'settings': settings.to_dict()
    })

@app.route('/api/profile/settings', methods=['GET'])
def get_settings():
    """获取用户设置"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    
    return jsonify(settings.to_dict())

@app.route('/api/profile/settings', methods=['PUT'])
def update_settings():
    """更新用户设置"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
    
    data = request.json
    if 'email_notification' in data:
        settings.email_notification = data['email_notification']
    if 'sms_notification' in data:
        settings.sms_notification = data['sms_notification']
    if 'show_location' in data:
        settings.show_location = data['show_location']
    if 'theme' in data:
        settings.theme = data['theme']
    
    db.session.commit()
    return jsonify(settings.to_dict())

@app.route('/api/profile/info', methods=['PUT'])
def update_profile_info():
    """更新个人信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    data = request.json
    if 'email' in data:
        # 检查邮箱是否已被使用
        existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
        if existing_user:
            return jsonify({'error': '邮箱已被其他用户使用'}), 400
        user.email = data['email']

    if 'phone' in data:
        # 检查手机号是否已被使用
        if data['phone']:
            existing_user = User.query.filter(User.phone == data['phone'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': '手机号已被其他用户使用'}), 400
        user.phone = data['phone']

    db.session.commit()
    return jsonify(user.to_dict())

@app.route('/api/profile/delete', methods=['DELETE'])
def delete_account():
    """注销账户"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    # 管理员不能删除自己的账户
    if user.role == 'admin':
        return jsonify({'error': '管理员账户不能注销'}), 403

    # 删除用户的所有数据
    # 删除浏览历史
    BrowseHistory.query.filter_by(user_id=user_id).delete()

    # 删除点赞记录
    PostLike.query.filter_by(user_id=user_id).delete()

    # 删除用户发布的帖子（包括评论）
    user_posts = Post.query.filter_by(user_id=user_id).all()
    for post in user_posts:
        # 删除帖子的所有评论
        Comment.query.filter_by(post_id=post.id).delete()
        db.session.delete(post)

    # 删除用户发布的物品
    LostItem.query.filter_by(user_id=user_id).delete()

    # 删除用户设置
    UserSettings.query.filter_by(user_id=user_id).delete()

    # 删除反馈
    Feedback.query.filter_by(user_id=user_id).delete()

    # 删除用户
    db.session.delete(user)

    # 记录删除原因
    data = request.json or {}
    reason = data.get('reason', '未提供原因')
    print(f'[注销] 用户 {user.username} (ID: {user_id}) 注销了账户，原因: {reason}')

    db.session.commit()
    return jsonify({'message': '账户已成功注销'})

@app.route('/api/profile/history', methods=['GET'])
def get_browse_history():
    """获取浏览历史"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    limit = int(request.args.get('limit', 20))
    history = BrowseHistory.query.filter_by(user_id=user_id).order_by(BrowseHistory.viewed_at.desc()).limit(limit).all()
    return jsonify([h.to_dict() for h in history])

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """提交用户反馈"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    data = request.json
    if not data.get('content'):
        return jsonify({'error': '反馈内容不能为空'}), 400

    feedback = Feedback(
        user_id=user_id,
        content=data['content']
    )

    db.session.add(feedback)
    db.session.commit()

    # 给管理员发送反馈通知
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notification = UserNotification(
            user_id=admin.id,
            type='feedback',
            title='新用户反馈',
            content=f'用户 {user.username} 提交了新的反馈: "{data["content"][:50]}..."',
            is_read=False,
            related_id=feedback.id,
            related_type='feedback'
        )
        db.session.add(notification)
    db.session.commit()

    print(f'[用户反馈] 用户 {user.username} 提交了反馈')

    return jsonify({
        'message': '反馈提交成功',
        'feedback': feedback.to_dict()
    })

@app.route('/api/profile/feedbacks', methods=['GET'])
def get_my_feedbacks():
    """获取我的反馈列表"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    feedbacks = Feedback.query.filter_by(user_id=user_id).order_by(Feedback.created_at.desc()).all()
    return jsonify([feedback.to_dict() for feedback in feedbacks])

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """获取当前用户的通知列表"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401

    # 获取未读数量
    unread_count = UserNotification.query.filter_by(user_id=user_id, is_read=False).count()

    # 获取所有通知，按时间倒序
    notifications = UserNotification.query.filter_by(user_id=user_id).order_by(UserNotification.created_at.desc()).limit(50).all()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    })

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """标记通知为已读"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    notification = UserNotification.query.get_or_404(notification_id)

    # 验证通知属于当前用户
    if notification.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403

    notification.is_read = True
    db.session.commit()

    return jsonify({'message': '标记成功'})

@app.route('/api/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """标记所有通知为已读"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
    except:
        return jsonify({'error': '无效的token'}), 401

    # 批量标记所有未读通知为已读
    UserNotification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()

    return jsonify({'message': '全部标记成功'})

@app.route('/api/profile/history', methods=['DELETE'])
def clear_browse_history():
    """清空浏览历史"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    BrowseHistory.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': '浏览历史已清空'})

@app.route('/api/profile/items/<int:item_id>/delete', methods=['DELETE'])
def delete_my_item(item_id):
    """删除我发布的信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    item = LostItem.query.get_or_404(item_id)
    if item.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403
    
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': '信息已删除'})

@app.route('/api/profile/posts/<int:post_id>/delete', methods=['DELETE'])
def delete_my_post(post_id):
    """删除我发布的帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'error': '无效的token'}), 401
    
    post = Post.query.get_or_404(post_id)
    if post.user_id != user_id:
        return jsonify({'error': '无权限操作'}), 403
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': '帖子已删除'})

@app.route('/api/track', methods=['POST'])
def track_view():
    """记录浏览历史，同时增加浏览数"""
    data = request.json
    item_type = data.get('item_type')  # 'found', 'lost', 'post'
    item_id = data.get('item_id')
    title = data.get('title')

    if not item_type or not item_id or not title:
        return jsonify({'error': '参数不完整'}), 400

    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'message': '未登录，不记录浏览历史'}), 200

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
    except:
        return jsonify({'message': '无效的token，不记录浏览历史'}), 200

    existing = BrowseHistory.query.filter_by(
        user_id=user_id,
        item_type=item_type,
        item_id=item_id
    ).first()

    if existing:
        # 更新浏览时间
        existing.viewed_at = datetime.now(timezone.utc)
    else:
        # 创建新的浏览记录
        history = BrowseHistory(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            title=title
        )
        db.session.add(history)

    # 增加物品浏览数
    if item_type in ['found', 'lost']:
        item = LostItem.query.get(item_id)
        if item:
            item.view_count += 1

    db.session.commit()
    return jsonify({'message': '浏览记录已更新'})

# ==================== 智能存储柜API ====================

@app.route('/api/lockers', methods=['GET'])
def get_lockers():
    """获取所有存储柜"""
    lockers = SmartLocker.query.order_by(SmartLocker.locker_number).all()
    return jsonify([locker.to_dict() for locker in lockers])

@app.route('/api/lockers', methods=['POST'])
def store_item():
    """存储物品到智能柜"""
    data = request.json
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    # 验证必填字段
    required_fields = ['locker_id', 'item_name', 'recipient_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    # 获取用户信息
    user_id = None
    if token and token.startswith('token_'):
        try:
            user_id = int(token.split('_')[1])
        except:
            return jsonify({'error': '无效的token'}), 401
    else:
        return jsonify({'error': '请先登录'}), 401

    # 检查存储柜是否可用
    locker = SmartLocker.query.get(data['locker_id'])
    if not locker:
        return jsonify({'error': '存储柜不存在'}), 404
    if locker.status != 'available':
        return jsonify({'error': '该存储柜已被占用'}), 400

    # 生成6位取件码
    import random
    pickup_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    # 创建存储物品记录
    item = LockerItem(
        locker_id=data['locker_id'],
        item_name=data['item_name'],
        description=data.get('description', ''),
        pickup_code=pickup_code,
        sender_id=user_id,
        recipient_phone=data['recipient_phone'],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # 7天后过期
    )

    # 更新存储柜状态
    locker.status = 'occupied'

    db.session.add(item)
    db.session.commit()

    print(f'[智能柜] 物品存入: {data["item_name"]}, 柜号: {locker.locker_number}, 取件码: {pickup_code}')

    # 发送取件码短信给接收人
    recipient_phone = data['recipient_phone']
    send_pickup_code_sms(recipient_phone, pickup_code, data['item_name'], locker.locker_number)

    # 发送系统通知给接收人（如果接收人是注册用户）
    print(f'[智能柜] 查找接收人，手机号: {recipient_phone}')
    recipient_user = User.query.filter_by(phone=recipient_phone).first()

    # 调试：打印所有用户的手机号
    all_users = User.query.all()
    print(f'[智能柜] 数据库中所有用户:')
    for u in all_users:
        print(f'  - ID: {u.id}, 用户名: {u.username}, 手机号: {u.phone}')

    if recipient_user:
        notification = UserNotification(
            user_id=recipient_user.id,
            type='system',
            title='智能存储柜取件通知',
            content=f'您有物品待取：{data["item_name"]}，柜号：{locker.locker_number}，取件码：{pickup_code}。请于7天内凭取件码取件。',
            is_read=False,
            related_id=item.id,
            related_type='locker_item'
        )
        db.session.add(notification)
        db.session.commit()
        print(f'[智能柜] 已发送取件通知给用户: {recipient_user.username} (ID: {recipient_user.id})')
    else:
        print(f'[智能柜] 未找到手机号为 {recipient_phone} 的用户，仅发送短信')

    return jsonify({
        'message': '物品存储成功',
        'item': item.to_dict()
    })

@app.route('/api/lockers/my-items', methods=['GET'])
def get_my_locker_items():
    """获取我存储的物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        items = LockerItem.query.filter_by(sender_id=user_id).order_by(LockerItem.stored_at.desc()).all()
        return jsonify([item.to_dict() for item in items])
    except:
        return jsonify({'error': '无效的token'}), 401

@app.route('/api/lockers/verify', methods=['POST'])
def verify_pickup_code():
    """验证取件码"""
    try:
        data = request.json
        pickup_code = data.get('pickup_code')

        if not pickup_code:
            return jsonify({'error': '请输入取件码'}), 400

        # 查找匹配的物品
        item = LockerItem.query.filter_by(pickup_code=pickup_code).first()

        if not item:
            return jsonify({'error': '取件码无效'}), 404

        if item.status != 'pending':
            return jsonify({'error': '该物品已被取走或已过期'}), 400

        # 检查是否过期
        if item.expires_at:
            # 统一转换为 UTC 时间进行比较
            current_time = datetime.now(timezone.utc)
            if item.expires_at.tzinfo is None:
                # 如果 expires_at 是 naive datetime，假设是 UTC
                expires_at_utc = item.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at_utc = item.expires_at

            if current_time > expires_at_utc:
                item.status = 'expired'
                db.session.commit()
                return jsonify({'error': '取件码已过期'}), 400

        return jsonify({
            'message': '取件码验证成功',
            'item': item.to_dict()
        })
    except Exception as e:
        print(f'[智能柜] 验证取件码错误: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/lockers/pickup', methods=['POST'])
def pickup_item():
    """取出物品"""
    try:
        data = request.json
        pickup_code = data.get('pickup_code')

        if not pickup_code:
            return jsonify({'error': '请输入取件码'}), 400

        # 查找匹配的物品
        item = LockerItem.query.filter_by(pickup_code=pickup_code).first()

        if not item:
            return jsonify({'error': '取件码无效'}), 404

        if item.status != 'pending':
            return jsonify({'error': '该物品已被取走或已过期'}), 400

        # 检查是否过期
        if item.expires_at:
            # 统一转换为 UTC 时间进行比较
            current_time = datetime.now(timezone.utc)
            if item.expires_at.tzinfo is None:
                # 如果 expires_at 是 naive datetime，假设是 UTC
                expires_at_utc = item.expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at_utc = item.expires_at

            if current_time > expires_at_utc:
                item.status = 'expired'
                db.session.commit()
                return jsonify({'error': '取件码已过期'}), 400

        # 更新物品状态
        item.status = 'claimed'
        item.picked_up_at = datetime.now(timezone.utc)

        # 释放存储柜
        if item.locker:
            item.locker.status = 'available'

        db.session.commit()

        print(f'[智能柜] 物品取出: {item.item_name}, 取件码: {pickup_code}')

        return jsonify({
            'message': '物品取出成功',
            'item': item.to_dict()
        })
    except Exception as e:
        print(f'[智能柜] 取出物品错误: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/api/lockers/<int:item_id>', methods=['DELETE'])
def delete_locker_item(item_id):
    """删除存储的物品（仅限创建者）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        item = LockerItem.query.get_or_404(item_id)

        if item.sender_id != user_id:
            return jsonify({'error': '无权限操作'}), 403

        # 释放存储柜
        if item.locker:
            item.locker.status = 'available'

        db.session.delete(item)
        db.session.commit()

        return jsonify({'message': '物品删除成功'})
    except:
        return jsonify({'error': '无效的token'}), 401

@app.route('/api/lockers/all', methods=['GET'])
def get_all_lockers():
    """获取所有存储柜（公开接口）"""
    lockers = SmartLocker.query.order_by(SmartLocker.locker_number).all()
    return jsonify([locker.to_dict() for locker in lockers])

@app.route('/api/lockers/manage', methods=['POST'])
def add_locker():
    """添加新的存储柜（管理员用）"""
    data = request.json
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    # 验证必填字段
    if not data.get('locker_number') or not data.get('location'):
        return jsonify({'error': '缺少必填字段'}), 400

    # 检查柜号是否已存在
    existing = SmartLocker.query.filter_by(locker_number=data['locker_number']).first()
    if existing:
        return jsonify({'error': '该柜号已存在'}), 400

    # 创建新存储柜
    locker = SmartLocker(
        locker_number=data['locker_number'],
        location=data['location']
    )

    db.session.add(locker)
    db.session.commit()

    return jsonify({
        'message': '存储柜添加成功',
        'locker': locker.to_dict()
    })

# 静态文件路由

# 静态文件路由
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return app.send_static_file(filename)


# ==================== 管理员 API ====================

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """获取管理员统计数据"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': '无权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    # 获取统计数据
    stats = {
        'users_count': User.query.count(),
        'items_count': LostItem.query.count(),
        'posts_count': Post.query.count(),
        'comments_count': Comment.query.count(),
        'locker_items_count': LockerItem.query.count(),
        'feedbacks_count': Feedback.query.count()
    }
    return jsonify(stats)

@app.route('/api/admin/items', methods=['GET'])
def get_all_items():
    """获取所有物品（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': '无权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    status = request.args.get('status')
    query = LostItem.query.order_by(LostItem.created_at.desc())

    if status:
        query = query.filter_by(status=status)

    items = query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/admin/posts', methods=['GET'])
def get_all_posts():
    """获取所有帖子（管理员）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        user_id = int(token.split('_')[1])
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': '无权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

# ==================== 管理员功能完善API ====================

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    user = User.query.get_or_404(user_id)

    # 不允许删除自己
    if user_id == current_user_id:
        return jsonify({'error': '不能删除自己'}), 400

    # 删除用户相关的所有数据
    # 删除用户的浏览历史
    BrowseHistory.query.filter_by(user_id=user_id).delete()
    # 删除用户的设置
    UserSettings.query.filter_by(user_id=user_id).delete()
    # 删除用户发布的物品
    LostItem.query.filter_by(user_id=user_id).delete()
    # 删除用户发布的帖子
    Post.query.filter_by(user_id=user_id).delete()
    # 删除用户的评论
    Comment.query.filter_by(user_id=user_id).delete()
    # 删除用户的存储柜物品
    LockerItem.query.filter_by(sender_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    print(f'[管理员] 删除用户: {user.username} (ID: {user_id})')

    return jsonify({'message': '用户删除成功'})

@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
def get_user_detail(user_id):
    """获取用户详情"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取用户统计信息
    items_count = LostItem.query.filter_by(user_id=user_id).count()
    posts_count = Post.query.filter_by(user_id=user_id).count()
    comments_count = Comment.query.filter_by(user_id=user_id).count()

    user_detail = user.to_dict()
    user_detail['stats'] = {
        'items_count': items_count,
        'posts_count': posts_count,
        'comments_count': comments_count
    }

    return jsonify(user_detail)

@app.route('/api/admin/items/<int:item_id>/audit', methods=['POST'])
def audit_item(item_id):
    """审核物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    item = LostItem.query.get_or_404(item_id)
    data = request.get_json()
    status = data.get('status', 'approved')  # approved 或 rejected

    if status not in ['approved', 'rejected']:
        return jsonify({'error': '无效的审核状态'}), 400

    item.audit_status = status
    db.session.commit()

    # 给用户发送审核通知
    notification = UserNotification(
        user_id=item.user_id,
        type='audit',
        title=f'您的{"失物招领" if item.type == "found" else "失物找寻"}信息已审核',
        content=f'您发布的"{item.title}"已通过{"审核" if status == "approved" else "审核未通过"}',
        is_read=False,
        related_id=item.id,
        related_type='item'
    )
    db.session.add(notification)
    db.session.commit()

    print(f'[管理员] 审核物品: {item.title} (ID: {item_id}), 状态: {status}')

    return jsonify({'message': f'物品审核{"通过" if status == "approved" else "拒绝"}成功', 'audit_status': status})

@app.route('/api/admin/posts/<int:post_id>/audit', methods=['POST'])
def audit_post(post_id):
    """审核帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    status = data.get('status', 'approved')  # approved 或 rejected

    if status not in ['approved', 'rejected']:
        return jsonify({'error': '无效的审核状态'}), 400

    post.audit_status = status
    db.session.commit()

    # 给用户发送审核通知
    notification = UserNotification(
        user_id=post.user_id,
        type='audit',
        title='您的帖子已审核',
        content=f'您发布的帖子"{post.title}"已通过{"审核" if status == "approved" else "审核未通过"}',
        is_read=False,
        related_id=post.id,
        related_type='post'
    )
    db.session.add(notification)
    db.session.commit()

    print(f'[管理员] 审核帖子: {post.title} (ID: {post_id}), 状态: {status}')

    return jsonify({'message': f'帖子审核{"通过" if status == "approved" else "拒绝"}成功', 'audit_status': status})

@app.route('/api/admin/items/approve-all', methods=['POST'])
def approve_all_items():
    """一键通过所有待审核物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    # 获取所有待审核的物品
    pending_items = LostItem.query.filter_by(audit_status='pending').all()

    if not pending_items:
        return jsonify({'message': '没有待审核的物品', 'count': 0})

    approved_count = 0

    for item in pending_items:
        try:
            item.audit_status = 'approved'
            approved_count += 1

            # 发送审核通过通知
            notification = UserNotification(
                user_id=item.user_id,
                type='audit',
                title=f'您的{"失物招领" if item.type == "found" else "失物找寻"}信息已审核',
                content=f'您发布的"{item.title}"已通过审核',
                is_read=False,
                related_id=item.id,
                related_type='item'
            )
            db.session.add(notification)
        except Exception as e:
            print(f'审核物品 {item.id} 时出错: {e}')
            continue

    db.session.commit()

    print(f'[管理员] 批量审核物品: 通过 {approved_count} 条')

    return jsonify({
        'message': f'成功通过 {approved_count} 条物品',
        'count': approved_count
    })

@app.route('/api/admin/posts/approve-all', methods=['POST'])
def approve_all_posts():
    """一键通过所有待审核帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    # 获取所有待审核的帖子
    pending_posts = Post.query.filter_by(audit_status='pending').all()

    if not pending_posts:
        return jsonify({'message': '没有待审核的帖子', 'count': 0})

    approved_count = 0

    for post in pending_posts:
        try:
            post.audit_status = 'approved'
            approved_count += 1

            # 发送审核通过通知
            notification = UserNotification(
                user_id=post.user_id,
                type='audit',
                title='您的帖子已审核',
                content=f'您发布的帖子"{post.title}"已通过审核',
                is_read=False,
                related_id=post.id,
                related_type='post'
            )
            db.session.add(notification)
        except Exception as e:
            print(f'审核帖子 {post.id} 时出错: {e}')
            continue

    db.session.commit()

    print(f'[管理员] 批量审核帖子: 通过 {approved_count} 条')

    return jsonify({
        'message': f'成功通过 {approved_count} 条帖子',
        'count': approved_count
    })

@app.route('/api/admin/items/<int:item_id>', methods=['DELETE'])
def delete_admin_item(item_id):
    """删除物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    item = LostItem.query.get_or_404(item_id)

    # 删除物品的浏览记录
    BrowseHistory.query.filter_by(item_id=item_id).delete()

    db.session.delete(item)
    db.session.commit()

    print(f'[管理员] 删除物品: {item.title} (ID: {item_id})')

    return jsonify({'message': '物品删除成功'})

@app.route('/api/admin/items/<int:item_id>/status', methods=['PUT'])
def update_item_status(item_id):
    """更新物品状态"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    item = LostItem.query.get_or_404(item_id)
    data = request.json

    if 'status' not in data:
        return jsonify({'error': '缺少status参数'}), 400

    valid_statuses = ['pending', 'claimed', 'returned', 'expired']
    if data['status'] not in valid_statuses:
        return jsonify({'error': '无效的状态值'}), 400

    item.status = data['status']
    db.session.commit()

    status_value = data['status']
    print(f'[管理员] 更新物品状态: {item.title} -> {status_value}')

    return jsonify({'message': '状态更新成功', 'item': item.to_dict()})

@app.route('/api/admin/items/<int:item_id>', methods=['GET'])
def get_item_detail(item_id):
    """获取物品详情"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    item = LostItem.query.get(item_id)
    if not item:
        return jsonify({'error': '物品不存在'}), 404
    item_dict = item.to_dict()

    # 添加发布者用户名
    if item.user_id:
        user = User.query.get(item.user_id)
        item_dict['username'] = user.username if user else '未知'
    else:
        item_dict['username'] = '未知'
    
    return jsonify(item_dict)

@app.route('/api/admin/posts/<int:post_id>', methods=['DELETE'])
def delete_admin_post(post_id):
    """删除帖子"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    post = Post.query.get_or_404(post_id)

    # 删除帖子的所有评论
    Comment.query.filter_by(post_id=post_id).delete()
    # 删除帖子的浏览记录
    BrowseHistory.query.filter_by(item_id=post_id, item_type='post').delete()

    db.session.delete(post)
    db.session.commit()

    print(f'[管理员] 删除帖子: {post.title} (ID: {post_id})')

    return jsonify({'message': '帖子删除成功'})

@app.route('/api/admin/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    return jsonify(post.to_dict())

@app.route('/api/admin/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """获取帖子的所有评论"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    return jsonify([comment.to_dict() for comment in comments])

@app.route('/api/admin/comments/<int:comment_id>', methods=['DELETE'])
def delete_admin_comment(comment_id):
    """删除评论"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()

    print(f'[管理员] 删除评论 (ID: {comment_id})')

    return jsonify({'message': '评论删除成功'})

@app.route('/api/admin/feedbacks', methods=['GET'])
def get_all_feedbacks():
    """获取所有用户反馈"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return jsonify([feedback.to_dict() for feedback in feedbacks])

@app.route('/api/admin/feedbacks/<int:feedback_id>/reply', methods=['POST'])
def reply_feedback(feedback_id):
    """回复反馈"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    feedback = Feedback.query.get_or_404(feedback_id)
    data = request.json

    if 'reply' not in data:
        return jsonify({'error': '缺少reply参数'}), 400

    feedback.reply = data['reply']
    feedback.replied_at = datetime.now(timezone.utc)
    feedback.status = 'replied'

    # 创建通知
    notification = UserNotification(
        user_id=feedback.user_id,
        type='feedback',
        title='您的反馈已收到回复',
        content=f'管理员回复了您的反馈：{data["reply"][:50]}...' if len(data['reply']) > 50 else data['reply'],
        is_read=False,
        related_id=feedback.id,
        related_type='feedback'
    )
    db.session.add(notification)

    db.session.commit()

    print(f'[管理员] 回复反馈 (ID: {feedback_id})')

    return jsonify({'message': '回复成功', 'feedback': feedback.to_dict()})

@app.route('/api/admin/lockers/items', methods=['GET'])
def get_all_locker_items():
    """获取所有存储柜物品"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    items = LockerItem.query.order_by(LockerItem.stored_at.desc()).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/admin/lockers/<int:locker_id>', methods=['DELETE'])
def delete_locker(locker_id):
    """删除存储柜"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    locker = SmartLocker.query.get_or_404(locker_id)

    if locker.status == 'occupied':
        return jsonify({'error': '存储柜中还有物品，无法删除'}), 400

    db.session.delete(locker)
    db.session.commit()

    print(f'[管理员] 删除存储柜: {locker.locker_number} (ID: {locker_id})')

    return jsonify({'message': '存储柜删除成功'})

@app.route('/api/admin/lockers/<int:locker_id>', methods=['PUT'])
def update_locker_status(locker_id):
    """更新存储柜状态"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    try:
        current_user_id = int(token.split('_')[1])
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': '需要管理员权限'}), 403
    except:
        return jsonify({'error': '无效的token'}), 401

    locker = SmartLocker.query.get_or_404(locker_id)
    data = request.json

    if 'status' not in data:
        return jsonify({'error': '缺少status参数'}), 400

    valid_statuses = ['available', 'occupied', 'maintenance']
    if data['status'] not in valid_statuses:
        return jsonify({'error': '无效的状态值'}), 400

    locker.status = data['status']
    db.session.commit()

    print(f'[管理员] 更新存储柜状态: {locker.locker_number} -> {data["status"]}')

    return jsonify({'message': '状态更新成功', 'locker': locker.to_dict()})

# ============== 好友和聊天系统 API ==============

@app.route('/api/user/search-by-phone', methods=['GET'])
@login_required
def search_user_by_phone():
    """通过手机号查找用户"""
    phone = request.args.get('phone')
    if not phone:
        return jsonify({'error': '请提供手机号'}), 400

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'error': '未找到该手机号对应的用户'}), 404

    # 获取当前用户
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 不能添加自己为好友
    if user.id == current_user_id:
        return jsonify({'error': '不能添加自己为好友'}), 400

    # 检查是否已经是好友或有待处理的请求
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == user.id)) |
        ((Friendship.user_id == user.id) & (Friendship.friend_id == current_user_id))
    ).first()

    if friendship:
        if friendship.status == 'accepted':
            return jsonify({
                'user': user.to_dict(),
                'relationship': 'friend',
                'message': '已经是好友'
            })
        elif friendship.status == 'pending':
            if friendship.user_id == current_user_id:
                return jsonify({
                    'user': user.to_dict(),
                    'relationship': 'pending_sent',
                    'message': '已发送好友申请，等待对方通过'
                })
            else:
                return jsonify({
                    'user': user.to_dict(),
                    'relationship': 'pending_received',
                    'message': '对方已发送好友申请，请处理'
                })

    return jsonify({
        'user': user.to_dict(),
        'relationship': 'none',
        'message': '可以添加为好友'
    })

@app.route('/api/friends/add', methods=['POST'])
@login_required
def add_friend():
    """发送好友申请"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])
    data = request.json

    if not data.get('friend_id'):
        return jsonify({'error': '请提供好友ID'}), 400

    friend_id = data['friend_id']

    # 不能添加自己为好友
    if friend_id == current_user_id:
        return jsonify({'error': '不能添加自己为好友'}), 400

    # 检查好友是否存在
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({'error': '好友不存在'}), 404

    # 检查是否已经是好友或有待处理的请求
    existing = Friendship.query.filter(
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user_id))
    ).first()

    if existing:
        if existing.status == 'accepted':
            return jsonify({'error': '已经是好友'}), 400
        elif existing.status == 'pending':
            if existing.user_id == current_user_id:
                return jsonify({'error': '已经发送过好友申请'}), 400
            else:
                return jsonify({'error': '对方已发送过好友申请，请先处理'}), 400

    # 创建好友申请
    friendship = Friendship(
        user_id=current_user_id,
        friend_id=friend_id,
        status='pending'
    )
    db.session.add(friendship)
    db.session.commit()

    # 给对方发送通知
    notification = UserNotification(
        user_id=friend_id,
        type='friend_request',
        title='新的好友申请',
        content=f'用户 {User.query.get(current_user_id).username} 想要添加你为好友',
        related_id=friendship.id,
        related_type='friendship'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'message': '好友申请已发送', 'friendship': friendship.to_dict()})

@app.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend():
    """接受好友申请"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])
    data = request.json

    if not data.get('friendship_id'):
        return jsonify({'error': '请提供好友关系ID'}), 400

    friendship = Friendship.query.get(data['friendship_id'])
    if not friendship:
        return jsonify({'error': '好友申请不存在'}), 404

    # 只能接受发给自己的好友申请
    if friendship.friend_id != current_user_id:
        return jsonify({'error': '无权操作'}), 403

    if friendship.status != 'pending':
        return jsonify({'error': '该申请已处理'}), 400

    # 更新好友关系状态
    friendship.status = 'accepted'
    db.session.commit()

    # 给申请人发送通知
    notification = UserNotification(
        user_id=friendship.user_id,
        type='friend_accepted',
        title='好友申请已通过',
        content=f'用户 {User.query.get(current_user_id).username} 已接受你的好友申请',
        related_id=friendship.id,
        related_type='friendship'
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'message': '好友申请已接受', 'friendship': friendship.to_dict()})

@app.route('/api/friends/reject', methods=['POST'])
@login_required
def reject_friend():
    """拒绝好友申请"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])
    data = request.json

    if not data.get('friendship_id'):
        return jsonify({'error': '请提供好友关系ID'}), 400

    friendship = Friendship.query.get(data['friendship_id'])
    if not friendship:
        return jsonify({'error': '好友申请不存在'}), 404

    # 只能拒绝发给自己的好友申请
    if friendship.friend_id != current_user_id:
        return jsonify({'error': '无权操作'}), 403

    if friendship.status != 'pending':
        return jsonify({'error': '该申请已处理'}), 400

    # 更新好友关系状态
    friendship.status = 'rejected'
    db.session.commit()

    return jsonify({'message': '好友申请已拒绝', 'friendship': friendship.to_dict()})

@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    """获取好友列表"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 获取已接受的好友关系
    friendships = Friendship.query.filter(
        Friendship.status == 'accepted'
    ).filter(
        ((Friendship.user_id == current_user_id) | (Friendship.friend_id == current_user_id))
    ).all()

    friends = []
    for f in friendships:
        friend_id = f.friend_id if f.user_id == current_user_id else f.user_id
        friend = User.query.get(friend_id)
        if friend:
            friends.append({
                'friendship_id': f.id,
                'user': friend.to_dict(),
                'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

    return jsonify(friends)

@app.route('/api/friends/pending', methods=['GET'])
@login_required
def get_pending_friend_requests():
    """获取待处理的好友申请"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 获取发给自己的待处理申请
    pending_requests = Friendship.query.filter(
        Friendship.friend_id == current_user_id,
        Friendship.status == 'pending'
    ).all()

    requests = []
    for f in pending_requests:
        user = User.query.get(f.user_id)
        if user:
            requests.append({
                'friendship_id': f.id,
                'user': user.to_dict(),
                'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

    return jsonify(requests)

@app.route('/api/friendships/<int:friendship_id>', methods=['GET'])
@login_required
def get_friendship(friendship_id):
    """获取单个好友关系信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    friendship = Friendship.query.get(friendship_id)
    if not friendship:
        return jsonify({'error': '好友关系不存在'}), 404

    # 验证当前用户是否参与此好友关系
    if friendship.user_id != current_user_id and friendship.friend_id != current_user_id:
        return jsonify({'error': '无权访问'}), 403

    return jsonify({
        'id': friendship.id,
        'user_id': friendship.user_id,
        'friend_id': friendship.friend_id,
        'status': friendship.status,
        'created_at': friendship.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/friends/<int:friend_id>', methods=['DELETE'])
@login_required
def delete_friend(friend_id):
    """删除好友"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 查找好友关系
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user_id))
    ).first()

    if not friendship:
        return jsonify({'error': '好友关系不存在'}), 404

    db.session.delete(friendship)
    db.session.commit()

    return jsonify({'message': '好友已删除'})

@app.route('/api/chat/messages/<int:user_id>', methods=['GET'])
@login_required
def get_chat_messages(user_id):
    """获取与指定用户的聊天记录"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 检查是否是好友
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user_id))
    ).first()

    if not friendship:
        return jsonify({'error': '不是好友关系'}), 403

    # 获取聊天记录
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user_id) & (ChatMessage.receiver_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == current_user_id))
    ).order_by(ChatMessage.created_at.asc()).all()

    # 标记收到的消息为已读
    unread_messages = ChatMessage.query.filter(
        ChatMessage.sender_id == user_id,
        ChatMessage.receiver_id == current_user_id,
        ChatMessage.is_read == False
    ).all()
    for msg in unread_messages:
        msg.is_read = True
    db.session.commit()

    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/chat/messages/send', methods=['POST'])
@login_required
def send_chat_message():
    """发送聊天消息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])
    data = request.json

    if not data.get('receiver_id') or not data.get('content'):
        return jsonify({'error': '请提供接收人ID和消息内容'}), 400

    receiver_id = data['receiver_id']
    content = data['content'].strip()

    if not content:
        return jsonify({'error': '消息内容不能为空'}), 400

    # 检查是否是好友
    friendship = Friendship.query.filter(
        Friendship.status == 'accepted',
        ((Friendship.user_id == current_user_id) & (Friendship.friend_id == receiver_id)) |
        ((Friendship.user_id == receiver_id) & (Friendship.friend_id == current_user_id))
    ).first()

    if not friendship:
        return jsonify({'error': '不是好友关系'}), 403

    # 创建消息
    message = ChatMessage(
        sender_id=current_user_id,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': '消息已发送', 'data': message.to_dict()})

@app.route('/api/chat/unread-count', methods=['GET'])
@login_required
def get_unread_chat_count():
    """获取未读消息数和最后一条消息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401

    current_user_id = int(token.split('_')[1])

    # 获取未读消息
    unread_count = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user_id,
        ChatMessage.is_read == False
    ).count()

    # 获取每个好友的未读消息数
    unread_messages = ChatMessage.query.filter(
        ChatMessage.receiver_id == current_user_id,
        ChatMessage.is_read == False
    ).all()

    sender_counts = {}
    for msg in unread_messages:
        if msg.sender_id not in sender_counts:
            sender_counts[msg.sender_id] = 0
        sender_counts[msg.sender_id] += 1

    # 获取每个好友的最后一条消息
    last_messages_raw = {}
    # 获取所有与好友的聊天消息（包括已读和未读）
    all_messages = ChatMessage.query.filter(
        (ChatMessage.sender_id == current_user_id) | (ChatMessage.receiver_id == current_user_id)
    ).order_by(ChatMessage.created_at).all()

    for msg in all_messages:
        other_user_id = msg.receiver_id if msg.sender_id == current_user_id else msg.sender_id
        # 如果该用户还没有最后一条消息，或者当前消息时间更新
        if other_user_id not in last_messages_raw or msg.created_at > last_messages_raw[other_user_id]['created_at']:
            last_messages_raw[other_user_id] = {
                'content': msg.content,
                'created_at': msg.created_at,
                'sender_id': msg.sender_id
            }

    # 将 datetime 对象转换为字符串格式用于 JSON 返回
    last_messages = {}
    for user_id, msg_data in last_messages_raw.items():
        last_messages[user_id] = {
            'content': msg_data['content'],
            'created_at': msg_data['created_at'].strftime('%Y-%m-%d %H:%M:%S') if msg_data['created_at'] else None,
            'sender_id': msg_data['sender_id']
        }

    return jsonify({
        'total': unread_count,
        'by_sender': sender_counts,
        'last_messages': last_messages
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
