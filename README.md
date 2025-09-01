# GeoServer Vue 地图应用

这是一个基于Vue 3和OpenLayers的GeoServer地图应用，支持上传和管理地理空间数据。

## 功能特点

- 基于Vue 3和Element Plus构建的现代化UI
- 使用OpenLayers显示地图和图层
- 支持上传TIF栅格数据和Shapefile矢量数据(ZIP格式)
- 图层管理功能：显示/隐藏、调整透明度、调整顺序、删除
- 自动缩放到新添加图层的范围

## 项目设置

### 安装依赖

```bash
npm install
```

### 开发模式运行

```bash
npm run serve
```

### 构建生产版本

```bash
npm run build
```

## 后端服务

后端使用Flask提供API服务，需要先启动后端：

```bash
python server.py
```

## 系统要求

- Node.js 14+
- Python 3.6+
- GeoServer实例（默认配置为localhost:8001）

## 配置

可以在以下文件中修改配置：

- `server.py`: 后端服务器配置，包括GeoServer连接信息
- `vue.config.js`: 前端开发服务器配置
- `src/App.vue`: 默认图层配置