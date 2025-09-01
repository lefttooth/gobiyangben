import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests
from flask_cors import CORS

# 配置
UPLOAD_FOLDER = 'uploads'
GEOSERVER_URL = 'http://localhost:8001/geoserver'
GEOSERVER_USER = 'admin'
GEOSERVER_PASSWORD = 'geoserver'
GEOSERVER_WORKSPACE = 'gobi'  # 可根据实际情况修改

app = Flask(__name__, static_folder='dist', static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CORS(app)

# 提供前端静态文件
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# 允许的扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'tif', 'tiff', 'zip'}

@app.route('/upload', methods=['POST'])
def upload_file():
    print('收到上传请求')
    files = request.files.getlist('file')
    print(f'接收到文件数: {len(files)}')
    if not files:
        print('未检测到文件')
        return jsonify(success=False, message='未检测到文件')

    filenames = []
    for file in files:
        print(f'处理文件: {file.filename}')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
        else:
            print(f'文件类型不支持: {file.filename}')
            return jsonify(success=False, message='文件类型不支持')

    print(f'所有保存的文件: {filenames}')
    exts = set([f.rsplit('.', 1)[1].lower() for f in filenames])
    print(f'文件扩展名集合: {exts}')
    if 'tif' in exts or 'tiff' in exts:
        print('检测到栅格数据')
        tif_file = [f for f in filenames if f.endswith(('tif', 'tiff'))][0]
        layer_name = os.path.splitext(tif_file)[0]
        coverage_name = None
        print(f'准备发布tif: {tif_file}, 图层名: {layer_name}')
        try:
            publish_success, coverage_name = publish_geoserver_raster(layer_name, tif_file)
            print(f'发布结果: {publish_success}, coverage_name: {coverage_name}')
        except Exception as e:
            print(f'后端异常: {e}')
            return jsonify(success=False, message=f'后端异常: {e}')
        if publish_success and coverage_name:
            layer_full_name = f'{GEOSERVER_WORKSPACE}:{coverage_name}'
            wms_url = f'{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms'
            bbox = None
            try:
                info_url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coverages/{coverage_name}.json'
                r_info = requests.get(info_url, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD))
                if r_info.status_code == 200:
                    info = r_info.json()
                    cov = info.get('coverage', {})
                    bbox = cov.get('latLonBoundingBox') or cov.get('nativeBoundingBox')
            except Exception as e:
                print(f'获取coverage范围异常: {e}')
            print(f'返回给前端: layerType=raster, layerName={layer_full_name}, wmsUrl={wms_url}, bbox={bbox}')
            return jsonify(success=True, layerType='raster', layerName=layer_full_name, wmsUrl=wms_url, bbox=bbox)
        else:
            print('GeoServer发布栅格失败')
            return jsonify(success=False, message='GeoServer发布栅格失败')
    elif 'zip' in exts:
        print('检测到shp zip数据')
        zip_file = [f for f in filenames if f.endswith('zip')][0]
        layer_name = os.path.splitext(zip_file)[0]
        print(f'准备发布shp zip: {layer_name}, 文件: {zip_file}')
        try:
            publish_success = publish_geoserver_vector(layer_name, zip_file)
            print(f'发布结果: {publish_success}')
        except Exception as e:
            print(f'后端异常: {e}')
            return jsonify(success=False, message=f'后端异常: {e}')
        if publish_success:
            # 获取矢量图层bbox
            bbox = None
            try:
                # 遍历datastore下所有featuretypes，找到第一个有效bbox
                ft_list_url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{layer_name}/featuretypes.json'
                r_list = requests.get(ft_list_url, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD))
                print(f'featuretypes列表请求状态: {r_list.status_code}')
                if r_list.status_code == 200:
                    ft_list = r_list.json().get('featureTypes', {}).get('featureType', [])
                    print(f'featureType列表: {ft_list}')
                    for ft_item in ft_list:
                        ft_name = ft_item.get('name')
                        ft_url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/datastores/{layer_name}/featuretypes/{ft_name}.json'
                        r_ft = requests.get(ft_url, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD))
                        print(f'featureType {ft_name} 请求状态: {r_ft.status_code}')
                        if r_ft.status_code == 200:
                            ft_info = r_ft.json().get('featureType', {})
                            bbox = ft_info.get('latLonBoundingBox') or ft_info.get('nativeBoundingBox')
                            print(f'featureType {ft_name} bbox原始值: {bbox}')
                            if isinstance(bbox, dict) and all(k in bbox for k in ['minx','maxx','miny','maxy']):
                                break
                            else:
                                print(f'featureType {ft_name} 无效bbox, 完整内容: {ft_info}')
                        else:
                            print(f'featureType {ft_name} 请求失败，状态码: {r_ft.status_code}')
            except Exception as e:
                print(f'获取shp bbox异常: {e}')
            print(f'返回给前端: layerType=vector, layerName={GEOSERVER_WORKSPACE}:{layer_name}, wmsUrl={GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms, bbox={bbox}')
            return jsonify(success=True, layerType='vector', layerName=f'{GEOSERVER_WORKSPACE}:{layer_name}', wmsUrl=f'{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms', bbox=bbox)
        else:
            print('GeoServer发布矢量失败')
            return jsonify(success=False, message='GeoServer发布矢量失败')
    else:
        print('文件类型不支持或数量不完整')
        return jsonify(success=False, message='请上传tif或zip格式的shp数据')

def publish_geoserver_raster(layer_name, tif_file):
    # 创建数据存储
    url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{layer_name}/file.geotiff'
    headers = {'Content-type': 'image/tiff'}
    try:
        with open(os.path.join(UPLOAD_FOLDER, tif_file), 'rb') as f:
            r = requests.put(url, data=f, headers=headers, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD), params={'configure': 'none'})
        print(f'GeoServer响应码: {r.status_code}')
        print(f'GeoServer响应内容: {r.text}')
        if r.status_code not in [201, 202]:
            return False, None
        # 自动发布coverage（图层）
        coverage_url = f'{GEOSERVER_URL}/rest/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{layer_name}/coverages'
        coverage_xml = f'''<coverage>
  <name>{layer_name}</name>
  <nativeName>{layer_name}</nativeName>
  <title>{layer_name}</title>
  <enabled>true</enabled>
</coverage>'''
        r2 = requests.post(coverage_url, data=coverage_xml.encode('utf-8'), headers={'Content-Type': 'text/xml'}, auth=(GEOSERVER_USER, GEOSERVER_PASSWORD))
        print(f'Coverage发布响应码: {r2.status_code}')
        print(f'Coverage发布响应内容: {r2.text}')
        # coverage_name为GeoServer返回内容（通常为coverage名）
        if r2.status_code in [201, 202]:
            # 兼容GeoServer返回的coverage_name可能带有XML标签或纯文本
            import re
            text = r2.text.strip()
            m = re.search(r'<name>(.*?)</name>', text)
            if m:
                coverage_name = m.group(1)
            else:
                coverage_name = text
            return True, coverage_name
        else:
            return False, None
    except Exception as e:
        print(f'发布栅格异常: {e}')
        return False, None

def publish_geoserver_vector(layer_name, filenames):
    # 直接上传zip包
    try:
        zip_path = os.path.join(UPLOAD_FOLDER, filenames) if isinstance(filenames, str) else filenames[0]
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