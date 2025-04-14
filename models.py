from extensions import db
from datetime import datetime

# 用户（用户id，用户名，邮箱） 
# 项目（项目id，项目名，创建时间，修改时间，分镜类型，用户输入，分镜脚本，封面图url，用户id） 
# 分镜（分镜id，分镜名，分镜描述，角色描述，景别，拍摄角度，备注，项目id） 
# 分镜图（分镜图id，分镜图url，背景图url，分镜id）
# 角色（角色id，角色名，人物图url，项目id）

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    projects = db.relationship('Project', backref='user', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))
    storyboard_type = db.Column(db.String(50))
    user_input = db.Column(db.Text)
    script = db.Column(db.Text)
    cover_image_url = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    storyboards = db.relationship('Storyboard', backref='project', lazy=True)
    characters = db.relationship('Character', backref='project', lazy=True)

class Storyboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    role_description = db.Column(db.Text)
    view = db.Column(db.String(50))  # 景别
    angle = db.Column(db.String(50))  # 拍摄角度
    note = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    images = db.relationship('StoryboardImage', backref='storyboard', lazy=True)

class StoryboardImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200))
    background_url = db.Column(db.String(200))
    peoplemask_url = db.Column(db.String(200))
    bgpano_url = db.Column(db.String(200))
    storyboard_id = db.Column(db.Integer, db.ForeignKey('storyboard.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(200))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
