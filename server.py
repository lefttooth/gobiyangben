import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import requests

# 配置
UPLOAD_FOLDER = 'uploads'
GEOSERVER_URL = 'http://localhost:8001/geoserver'
GEOSERVER_USER = 'admin'
GEOSERVER_PASSWORD = 'geoserver'
GEOSERVER_WORKSPACE = 'gobi'  # 可根据实际情况修改

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 允许的扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'tif', 'tiff', 'shp', 'shx', 'dbf', 'prj', 'cpg'}

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if not files:
        return jsonify(success=False, message='未检测到文件')

    filenames = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
        else:
            return jsonify(success=False, message='文件类型不支持')

    # 判断是tif还是shp
    exts = set([f.rsplit('.', 1)[1].lower() for f in filenames])
    if 'tif' in exts or 'tiff' in exts:
        # 栅格数据
        tif_file = [f for f in filenames if f.endswith(('tif', 'tiff'))][0]
        layer_name = os.path.splitext(tif_file)[0]
        # 发布到GeoServer
        publish_success = publish_geoserver_raster(layer_name, tif_file)
        if publish_success:
            return jsonify(success=True, layerType='raster', layerName=f'{GEOSERVER_WORKSPACE}:{layer_name}', wmsUrl=f'{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms')
        else:
            return jsonify(success=False, message='GeoServer发布栅格失败')
    elif {'shp', 'shx', 'dbf'}.issubset(exts):
        # 矢量数据
        shp_file = [f for f in filenames if f.endswith('shp')][0]
        layer_name = os.path.splitext(shp_file)[0]
        # 发布到GeoServer
        publish_success = publish_geoserver_vector(layer_name, filenames)
        if publish_success:
            return jsonify(success=True, layerType='vector', layerName=f'{GEOSERVER_WORKSPACE}:{layer_name}', wmsUrl=f'{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms')
        else:
            return jsonify(success=False, message='GeoServer发布矢量失败')
    else:
        return jsonify(success=False, message='请上传完整的tif或shp文件（shp+shx+dbf）')

def publish_geoserver_raster(layer_name, tif_file):
    # 创建数据存储
    url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{layer_name}/file.geotiff'
    headers = {'Content-type': 'image/tiff'}
    try:
        with open(os.path.join(UPLOAD_FOLDER, tif_file), 'rb') as f:
            r = requests.put(url, data=f, headers=headers, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD), params={'configure': 'all'})
        print(f'GeoServer响应码: {r.status_code}')
        print(f'GeoServer响应内容: {r.text}')
        return r.status_code in [201, 202]
    except Exception as e:
        print(f'发布栅格异常: {e}')
        return False

def publish_geoserver_vector(layer_name, filenames):
    # 打包shp相关文件为zip
    import zipfile
    zip_path = os.path.join(UPLOAD_FOLDER, layer_name + '.zip')
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for ext in ['shp', 'shx', 'dbf', 'prj', 'cpg']:
                fname = layer_name + '.' + ext
                fpath = os.path.join(UPLOAD_FOLDER, fname)
                if os.path.exists(fpath):
                    zipf.write(fpath, fname)
        # 上传zip到GeoServer
        url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{layer_name}/file.shp'
        headers = {'Content-type': 'application/zip'}
        with open(zip_path, 'rb') as f:
            r = requests.put(url, data=f, headers=headers, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD), params={'configure': 'all'})
        print(f'GeoServer响应码: {r.status_code}')
        print(f'GeoServer响应内容: {r.text}')
        return r.status_code in [201, 202]
    except Exception as e:
        print(f'发布矢量异常: {e}')
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
