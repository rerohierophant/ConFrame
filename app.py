from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name')
    project_description = request.form.get('project_description')
    
    # TODO: 在这里添加项目创建的逻辑
    # 例如保存到数据库等
    
    return redirect(url_for('index'))

@app.route('/storyboard', methods=['GET', 'POST'])
def storyboard():
    return render_template('storyboard-edit.html')



if __name__ == '__main__':
    app.run(debug=True)
