<!-- eslint-disable -->
<template>
  <div class="app-container">
    <el-container>
      <el-aside width="350px">
        <div class="sidebar-container">
          <h2 class="app-title">地理数据可视化</h2>
          
          <!-- 上传组件 -->
          <div class="sidebar-section">
            <h3 class="section-title">数据上传</h3>
            <file-uploader @layer-added="handleLayerAdded" />
          </div>
          
          <!-- 图层管理组件 -->
          <div class="sidebar-section">
            <h3 class="section-title">图层管理</h3>
            <layer-manager 
              :layers="layers" 
              @toggle-layer="toggleLayer"
              @remove-layer="removeLayer"
              @layer-opacity-change="changeLayerOpacity"
              @layer-order-change="changeLayerOrder"
            />
          </div>
        </div>
      </el-aside>
      
      <el-main>
        <map-viewer 
          ref="mapViewer" 
          :layers="layers"
        />
        <div v-if="!hasNonBaseLayers" class="map-empty-overlay">
          <el-empty 
            description="暂无图层数据" 
            :image-size="100"
          >
            <template #description>
              <p>请通过左侧上传功能添加地理数据</p>
            </template>
          </el-empty>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import MapViewer from './components/MapViewer.vue'
import FileUploader from './components/FileUploader.vue'
import LayerManager from './components/LayerManager.vue'

export default {
  name: 'App',
  components: {
    MapViewer,
    FileUploader,
    LayerManager
  },
  computed: {
    hasNonBaseLayers() {
      return this.layers.some(layer => !layer.baseLayer)
    }
  },
  data() {
    return {
      layers: [
        {
          id: 'satellite',
          name: '卫星底图',
          type: 'xyz',
          visible: true,
          opacity: 1,
          baseLayer: true,
          source: {
            url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            maxZoom: 19
          }
        }
      ]
    }
  },
  methods: {
    handleLayerAdded(layerInfo) {
      // 生成唯一ID
      const layerId = `layer-${Date.now()}`
      
      // 创建新图层对象
      const newLayer = {
        id: layerId,
        name: layerInfo.layerName.split(':')[1] || layerInfo.layerName,
        type: 'wms',
        visible: true,
        opacity: 1,
        baseLayer: false,
        source: {
          url: layerInfo.wmsUrl,
          params: {
            'LAYERS': layerInfo.layerName,
            'TILED': true
          }
        },
        bbox: layerInfo.bbox
      }
      
      // 添加到图层列表
      this.layers.push(newLayer)
      
      // 通知地图组件缩放到新图层范围
      if (layerInfo.bbox) {
        this.$nextTick(() => {
          this.$refs.mapViewer.zoomToExtent(layerInfo.bbox)
        })
      }
      
      // 显示成功消息
      this.$message({
        message: '图层添加成功',
        type: 'success'
      })
    },
    
    toggleLayer(layerId, visible) {
      const layer = this.layers.find(l => l.id === layerId)
      if (layer) {
        layer.visible = visible
      }
    },
    
    removeLayer(layerId) {
      const index = this.layers.findIndex(l => l.id === layerId)
      if (index !== -1 && !this.layers[index].baseLayer) {
        this.layers.splice(index, 1)
      }
    },
    
    changeLayerOpacity(layerId, opacity) {
      const layer = this.layers.find(l => l.id === layerId)
      if (layer) {
        layer.opacity = opacity
      }
    },
    
    changeLayerOrder(fromIndex, toIndex) {
      // 保护基础图层始终在底部
      const nonBaseLayers = this.layers.filter(l => !l.baseLayer)
      const baseLayers = this.layers.filter(l => l.baseLayer)
      
      if (fromIndex >= 0 && fromIndex < nonBaseLayers.length && 
          toIndex >= 0 && toIndex < nonBaseLayers.length) {
        // 调整非基础图层的顺序
        const movedItem = nonBaseLayers.splice(fromIndex, 1)[0]
        nonBaseLayers.splice(toIndex, 0, movedItem)
        
        // 重组图层数组
        this.layers = [...baseLayers, ...nonBaseLayers]
      }
    }
  }
}
</script>

<style>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-container {
  height: 100%;
}

.app-title {
  margin: 0 0 15px 0;
  padding: 15px 0;
  text-align: center;
  border-bottom: 1px solid #e6e6e6;
}

.el-aside {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  padding: 0;
  overflow-y: auto;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
}

.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-section {
  padding: 10px 15px;
  margin-bottom: 10px;
}

.section-title {
  font-size: 16px;
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px dashed #dcdfe6;
  color: #409EFF;
}

.el-main {
  padding: 0;
  position: relative;
}

.map-empty-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.5);
  pointer-events: none;
}
</style>