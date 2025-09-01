<!-- eslint-disable -->
<template>
  <div class="layer-manager">
    <h3>图层管理</h3>
    
    <el-empty v-if="displayLayers.length === 0" description="暂无图层" />
    
    <div ref="layerListRef" class="layer-list">
      <div 
        v-for="element in displayLayers" 
        :key="element.id" 
        class="layer-item"
        :class="{ 'is-base-layer': element.baseLayer }"
      >
        <div class="layer-header">
          <el-icon class="drag-handle" v-if="!element.baseLayer"><d-arrow-left /></el-icon>
          <el-switch
            v-model="element.visible"
            @change="(val) => toggleLayer(element.id, val)"
            size="small"
            inline-prompt
            :active-icon="Check"
            :inactive-icon="Close"
          />
          <span class="layer-name" :title="element.name">{{ element.name }}</span>
          <el-button
            v-if="!element.baseLayer"
            @click="removeLayer(element.id)"
            type="danger"
            size="small"
            circle
            plain
          >
            <el-icon><delete /></el-icon>
          </el-button>
        </div>
        
        <div class="layer-controls">
          <span class="opacity-label">透明度:</span>
          <el-slider
            v-model="element.opacity"
            :min="0"
            :max="1"
            :step="0.01"
            @change="(val) => changeLayerOpacity(element.id, val)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { Check, Close, Delete, DArrowLeft } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'

export default {
  name: 'LayerManager',
  props: {
    layers: {
      type: Array,
      required: true
    }
  },
  setup(props, { emit }) {
    const layerListRef = ref(null)
    
    // 计算属性：用于显示的图层（反向显示，使顶部图层显示在列表顶部）
    const displayLayers = computed(() => {
      // 分离基础图层和普通图层
      const baseLayers = props.layers.filter(l => l.baseLayer)
      const nonBaseLayers = props.layers.filter(l => !l.baseLayer)
      
      // 普通图层反转顺序（使顶部图层显示在列表顶部）
      return [...nonBaseLayers.slice().reverse(), ...baseLayers]
    })
    
    // 初始化拖拽排序
    onMounted(() => {
      if (layerListRef.value) {
        Sortable.create(layerListRef.value, {
          animation: 200,
          handle: '.drag-handle',
          ghostClass: 'ghost',
          filter: '.is-base-layer', // 过滤基础图层，不允许拖动
          onEnd: (evt) => {
            // 只处理非基础图层的拖拽
            const nonBaseLayers = props.layers.filter(l => !l.baseLayer)
            if (nonBaseLayers.length < 2) return
            
            // 计算实际的图层索引（考虑到显示顺序是反向的）
            const fromIndex = nonBaseLayers.length - 1 - evt.oldIndex
            const toIndex = nonBaseLayers.length - 1 - evt.newIndex
            
            // 通知父组件更新图层顺序
            emit('layer-order-change', fromIndex, toIndex)
          }
        })
      }
    })
    
    // 切换图层可见性
    const toggleLayer = (layerId, visible) => {
      emit('toggle-layer', layerId, visible)
    }
    
    // 移除图层
    const removeLayer = (layerId) => {
      emit('remove-layer', layerId)
    }
    
    // 修改图层透明度
    const changeLayerOpacity = (layerId, opacity) => {
      emit('layer-opacity-change', layerId, opacity)
    }
    
    return {
      layerListRef,
      displayLayers,
      toggleLayer,
      removeLayer,
      changeLayerOpacity,
      Check,
      Close,
      Delete,
      DArrowLeft
    }
  }
}
</script>

<style scoped>
.layer-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.layer-list {
  display: flex;
  flex-direction: column;
}

.layer-item {
  background-color: #fff;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.layer-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.drag-handle {
  cursor: move;
  margin-right: 8px;
  color: #909399;
}

.layer-name {
  flex: 1;
  margin: 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layer-controls {
  display: flex;
  align-items: center;
}

.opacity-label {
  min-width: 60px;
  font-size: 12px;
  color: #606266;
}

.el-slider {
  flex: 1;
  margin-left: 10px;
}

.ghost {
  opacity: 0.5;
  background: #c8ebfb;
}

.is-base-layer .drag-handle {
  display: none;
}
</style>