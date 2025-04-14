from app import app, db
import models

with app.app_context():
    db.create_all()
    print("数据库初始化完成！")