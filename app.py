from flask import Flask, jsonify, render_template, request, redirect, url_for, session, Response
from datetime import datetime
from extensions import db
from models import User, Project, Storyboard, StoryboardImage, Character
import cv2
import numpy as np
import os
from flask import send_file
import io
import base64
import json
from typing import Optional
from dotenv import load_dotenv
import requests
import uuid
from werkzeug.utils import secure_filename
import time

from cozepy import COZE_CN_BASE_URL, Coze, DeviceOAuthApp, Stream, TokenAuth, WorkflowEvent, WorkflowEventType
# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 配置 SQLite 数据库（数据库文件名为 database.db）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'conframe-2024-dev'  # 修改为一个随机字符串

db.init_app(app)

@app.route('/process_mask/<int:project_id>/<int:storyboard_id>')  # 添加这行路由装饰器
def process_mask(project_id, storyboard_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    storyboard = Storyboard.query.get_or_404(storyboard_id)
    
    # 读取原始蒙版图片
    mask_path = os.path.join(app.static_folder, storyboard.images[0].peoplemask_url)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    # 创建BGRA图像
    h, w = mask.shape
    output = np.zeros((h, w, 4), dtype=np.uint8)
    
    # 设置颜色为黑色，alpha通道使用反转灰度
    output[:, :, 0:3] = (0, 0, 0)  # BGR黑色
    output[:, :, 3] = 255 - mask  # 反转灰度作为alpha通道
    
    # 将图片转换为字节流
    is_success, buffer = cv2.imencode(".png", output)
    if not is_success:
        return "图片处理失败", 500
        
    byte_io = io.BytesIO(buffer.tobytes())
    
    return send_file(
        byte_io,
        mimetype='image/png',
        as_attachment=False
    )


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # 检查用户是否已存在
        user = User.query.filter_by(email=email).first()
        if not user:
            # 创建新用户
            user = User(username=username, email=email)
            db.session.add(user)
            db.session.commit()
        
        # 将用户信息存储在session中
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return render_template('index.html', 
                         projects=projects,
                         username=session.get('username'),
                         email=session.get('email'))

@app.route('/create_project', methods=['POST'])
def create_project():
    project_name = request.form.get('project_name')
    project_description = request.form.get('project_description')
    
    # TODO: 在这里添加项目创建的逻辑
    # 例如保存到数据库等
    
    return redirect(url_for('index'))

@app.route('/storyboard/<int:project_id>', methods=['GET'])
def storyboard_edit(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    storyboards = Storyboard.query.filter_by(project_id=project_id).order_by(Storyboard.id).all()
    
    return render_template('storyboard-edit.html', 
                         project=project,
                         storyboards=storyboards,
                         username=session.get('username'),
                         email=session.get('email'))

@app.route('/storyboard/<int:project_id>/panorama/<int:storyboard_id>', methods=['GET'])
def panorama(project_id, storyboard_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    storyboard = Storyboard.query.get_or_404(storyboard_id)
    
    # 验证该分镜是否属于当前项目
    if storyboard.project_id != project_id:
        return redirect(url_for('storyboard_edit', project_id=project_id))
    
    background_url = url_for('static', filename=storyboard.images[0].background_url)
    peoplemask_url = url_for('process_mask', project_id=project_id, storyboard_id=storyboard_id)

    return render_template('panorama.html', 
                         project=project, 
                         storyboard=storyboard,
                         username=session.get('username'),
                         email=session.get('email'),
                         background_url=background_url,
                         peoplemask_url=peoplemask_url)

@app.route('/rename_project/<int:project_id>', methods=['POST'])
def rename_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    if project.user_id != session['user_id']:
        return redirect(url_for('index'))
    
    data = request.get_json()
    new_name = data.get('name')
    if new_name:
        project.name = new_name
        db.session.commit()
        return '', 200
    return '', 400

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    if project.user_id != session['user_id']:
        return redirect(url_for('index'))
    
    db.session.delete(project)
    db.session.commit()
    return '', 200




@app.route('/save_screenshot', methods=['POST'])
def save_screenshot():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.json
    base64_data = data.get('base64_data')
    project_id = data.get('project_id')
    storyboard_id = data.get('storyboard_id')

    try:
        # 解析并保存图片
        image_data = base64.b64decode(base64_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'bgpano_{storyboard_id}_{timestamp}.png'

        save_dir = os.path.join(app.static_folder, 'img', 'bgpano')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)

        with open(file_path, 'wb') as f:
            f.write(image_data)

        relative_path = os.path.join('img', 'bgpano', filename)

        # 更新数据库
        storyboard = Storyboard.query.get_or_404(storyboard_id)

        # 找到或创建 storyboard 对应的图像记录
        image_record = StoryboardImage.query.filter_by(storyboard_id=storyboard_id).first()
        if image_record:
            image_record.bgpano_url = relative_path
        else:
            new_image = StoryboardImage(
                storyboard_id=storyboard_id,
                bgpano_url=relative_path
            )
            db.session.add(new_image)

        db.session.commit()

        return jsonify({
            'success': True,
            'project_id': project_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def get_coze_api_base() -> str:
    # The default access is api.coze.cn, but if you need to access api.coze.com,
    # please use base_url to configure the api endpoint to access
    coze_api_base = os.getenv("COZE_API_BASE")
    if coze_api_base:
        return coze_api_base

    return COZE_CN_BASE_URL  # default


def get_coze_api_token(workspace_id: Optional[str] = None) -> str:
    # Get an access_token through personal access token or oauth.
    coze_api_token = os.getenv("COZE_API_TOKEN")
    if coze_api_token:
        return coze_api_token

    coze_api_base = get_coze_api_base()

    device_oauth_app = DeviceOAuthApp(client_id="57294420732781205987760324720643.app.coze", base_url=coze_api_base)
    device_code = device_oauth_app.get_device_code(workspace_id)
    print(f"Please Open: {device_code.verification_url} to get the access token")
    return device_oauth_app.get_access_token(device_code=device_code.device_code, poll=True).access_token


@app.route('/stream_test')
def stream_test():
    return render_template('stream_test.html')

@app.route('/stream')
def stream():
    def generate():
        try:
            coze = Coze(auth=TokenAuth(token=get_coze_api_token()), base_url=get_coze_api_base())
            workflow_id = os.getenv("COZE_WORKFLOW_ID") or "workflow id"
            parameters = {"BOT_USER_INPUT": "奥特曼大战奶龙"}
            
            stream = coze.workflows.runs.stream(
                workflow_id=workflow_id,
                parameters=parameters,
            )
            
            for event in stream:
                if event.event == WorkflowEventType.MESSAGE:
                    # 只序列化消息的文本内容
                    message_content = event.message.content if hasattr(event.message, 'content') else str(event.message)
                    yield f"data: {json.dumps({'type': 'message', 'content': message_content})}\n\n"
                elif event.event == WorkflowEventType.ERROR:
                    error_content = str(event.error)
                    yield f"data: {json.dumps({'type': 'error', 'content': error_content})}\n\n"
                elif event.event == WorkflowEventType.INTERRUPT:
                    resume_stream = coze.workflows.runs.resume(
                        workflow_id=workflow_id,
                        event_id=event.interrupt.interrupt_data.event_id,
                        resume_data="hey",
                        interrupt_type=event.interrupt.interrupt_data.type,
                    )
                    for resume_event in resume_stream:
                        if resume_event.event == WorkflowEventType.MESSAGE:
                            # 同样只序列化恢复消息的文本内容
                            resume_content = resume_event.message.content if hasattr(resume_event.message, 'content') else str(resume_event.message)
                            yield f"data: {json.dumps({'type': 'message', 'content': resume_content})}\n\n"
        except Exception as e:
            error_message = f"发生错误: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_message})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/process_image', methods=['POST'])
def process_image():
    file = request.files['image']
        
    # 保存上传的图片
    filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
    upload_path = os.path.join(app.static_folder, 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    try:
        # 准备ComfyUI API调用数据
        workflow = {
        "1": {
            "inputs": {
            "image": "testproject2.png"
            },
            "class_type": "LoadImage",
            "_meta": {
            "title": "加载图像"
            }
        },
        "3": {
            "inputs": {
            "detail_method": "VITMatte",
            "detail_erode": 4,
            "detail_dilate": 2,
            "black_point": 0.01,
            "white_point": 0.99,
            "process_detail": False,
            "device": "cuda",
            "max_megapixels": 2,
            "image": [
                "1",
                0
            ],
            "birefnet_model": [
                "4",
                0
            ]
            },
            "class_type": "LayerMask: BiRefNetUltraV2",
            "_meta": {
            "title": "LayerMask: BiRefNet Ultra V2(Advance)"
            }
        },
        "4": {
            "inputs": {
            "model": "BiRefNet-general-epoch_244.pth"
            },
            "class_type": "LayerMask: LoadBiRefNetModel",
            "_meta": {
            "title": "LayerMask: Load BiRefNet Model(Advance)"
            }
        },
        "7": {
            "inputs": {
            "mask": [
                "11",
                0
            ]
            },
            "class_type": "MaskToImage",
            "_meta": {
            "title": "遮罩转换为图像"
            }
        },
        "11": {
            "inputs": {
            "mask": [
                "3",
                1
            ]
            },
            "class_type": "InvertMask",
            "_meta": {
            "title": "反转遮罩"
            }
        },
        "13": {
            "inputs": {
            "filename_prefix": "result",
            "images": [
                "7",
                0
            ]
            },
            "class_type": "SaveImage",
            "_meta": {
            "title": "保存图像"
            }
        }
        }
        
        # 调用ComfyUI API
        comfyui_url = 'http://127.0.0.1:8188'  # 根据实际ComfyUI服务地址修改
        
        # 上传图片到ComfyUI
        with open(file_path, 'rb') as f:
            files = {
                'image': (filename, f, 'image/png')
            }
            response = requests.post(f'{comfyui_url}/upload/image', files=files)

        
        # 执行工作流
        response = requests.post(f'{comfyui_url}/prompt', json={
            'prompt': workflow
        })

            
        prompt_id = response.json()['prompt_id']
        
        # 等待处理完成
        while True:
            response = requests.get(f'{comfyui_url}/history/{prompt_id}')
            if response.status_code == 200:
                history = response.json()
                if prompt_id in history:
                    if 'outputs' in history[prompt_id]:
                        # 获取输出图片
                        output_images = history[prompt_id]['outputs']
                        if output_images and '12' in output_images:
                            image_data = output_images['12']['images'][0]
                            
                            # 保存处理后的图片
                            output_filename = f'output_{filename}'
                            output_path = os.path.join(upload_path, output_filename)
                            
                            # 从base64解码并保存图片
                            image_data = base64.b64decode(image_data.split(',')[1])
                            with open(output_path, 'wb') as f:
                                f.write(image_data)
                                
                            return jsonify({
                                'success': True,
                                'image_url': url_for('static', filename=f'uploads/{output_filename}')
                            })
                    elif 'error' in history[prompt_id]:
                        raise Exception(history[prompt_id]['error'])
            
            time.sleep(1)  # 等待1秒后再次检查
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/upload')
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)