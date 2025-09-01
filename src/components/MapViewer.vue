<!-- eslint-disable -->
<template>
  <div class="map-container" ref="mapContainer"></div>
</template>

<script>
import 'ol/ol.css'
import { Map, View } from 'ol'
import { Tile as TileLayer } from 'ol/layer'
import { XYZ, TileWMS } from 'ol/source'
import { defaults as defaultControls, Zoom, ScaleLine } from 'ol/control'
import { defaults as defaultInteractions } from 'ol/interaction'
// import { fromLonLat } from 'ol/proj'

export default {
  name: 'MapViewer',
  props: {
    layers: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      map: null,
      olLayers: {}
    }
  },
  mounted() {
    this.initMap()
  },
  methods: {
    initMap() {
      // 创建地图实例
      this.map = new Map({
        target: this.$refs.mapContainer,
        controls: defaultControls().extend([
          new Zoom({
            delta: 1,
            zoomInTipLabel: '放大',
            zoomOutTipLabel: '缩小'
          }),
          new ScaleLine({
            units: 'metric'
          })
        ]),
        interactions: defaultInteractions({
          doubleClickZoom: false // 禁用双击缩放
        }),
        view: new View({
          projection: 'EPSG:4326',
          center: [0, 0],
          zoom: 2
        })
      })
      
      // 初始化图层
      this.updateLayers()
    },
    
    updateLayers() {
      // 清除现有图层
      if (this.map) {
        this.map.getLayers().clear()
        this.olLayers = {}
        
        if (this.layers && this.layers.length > 0) {
          // 按顺序添加图层（基础图层在底部）
          const baseLayers = this.layers.filter(l => l.baseLayer)
          const nonBaseLayers = this.layers.filter(l => !l.baseLayer)
          
          // 先添加基础图层
          baseLayers.forEach(layer => {
            this.addLayerToMap(layer)
          })
          
          // 再添加其他图层
          nonBaseLayers.forEach(layer => {
            this.addLayerToMap(layer)
          })
        } else {
          // 如果没有图层，添加一个空白底图
          console.log('没有可用图层')
        }
      }
    },
    
    addLayerToMap(layerConfig) {
      let olLayer
      
      if (layerConfig.type === 'xyz') {
        olLayer = new TileLayer({
          source: new XYZ({
            url: layerConfig.source.url,
            maxZoom: layerConfig.source.maxZoom || 19,
            crossOrigin: 'anonymous'
          }),
          visible: layerConfig.visible,
          opacity: layerConfig.opacity
        })
      } else if (layerConfig.type === 'wms') {
        olLayer = new TileLayer({
          source: new TileWMS({
            url: layerConfig.source.url,
            params: layerConfig.source.params,
            serverType: 'geoserver',
            crossOrigin: 'anonymous'
          }),
          visible: layerConfig.visible,
          opacity: layerConfig.opacity
        })
      }
      
      if (olLayer) {
        this.olLayers[layerConfig.id] = olLayer
        this.map.addLayer(olLayer)
      }
    },
    
    zoomToExtent(bbox) {
      if (this.map && bbox) {
        // 检查 bbox 是否为对象格式（带有 minx, miny, maxx, maxy 属性）
        let extent;
        if (typeof bbox === 'object' && 'minx' in bbox && 'miny' in bbox && 'maxx' in bbox && 'maxy' in bbox) {
          extent = [bbox.minx, bbox.miny, bbox.maxx, bbox.maxy];
        } 
        // 检查 bbox 是否为数组格式 [minx, miny, maxx, maxy]
        else if (Array.isArray(bbox) && bbox.length === 4) {
          extent = bbox;
        }
        
        if (extent) {
          this.map.getView().fit(extent, {
            padding: [50, 50, 50, 50],
            duration: 1000
          });
        }
      }
    }
  },
  watch: {
    layers: {
      deep: true,
      handler(newLayers) {
        // 当图层配置发生变化时更新地图
        if (this.map) {
          // 更新现有图层的可见性和透明度
          newLayers.forEach(layerConfig => {
            const olLayer = this.olLayers[layerConfig.id]
            if (olLayer) {
              olLayer.setVisible(layerConfig.visible)
              olLayer.setOpacity(layerConfig.opacity)
            } else {
              // 如果是新图层，添加到地图
              this.addLayerToMap(layerConfig)
            }
          })
          
          // 移除已删除的图层
          Object.keys(this.olLayers).forEach(layerId => {
            if (!newLayers.some(l => l.id === layerId)) {
              this.map.removeLayer(this.olLayers[layerId])
              delete this.olLayers[layerId]
            }
          })
        }
      }
    }
  }
}
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
}
</style>

<style>
/* 自定义地图控件样式 */
.ol-zoom {
  top: 10px;
  left: auto;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  padding: 2px;
}

.ol-zoom button {
  background-color: #fff;
  color: #333;
  width: 30px;
  height: 30px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 2px;
  margin: 1px;
}

.ol-zoom button:hover {
  background-color: #f0f0f0;
}

.ol-scale-line {
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  padding: 2px 5px;
  bottom: 10px;
  left: 10px;
}
</style>