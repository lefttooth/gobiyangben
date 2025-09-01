<!-- eslint-disable -->
<template>
  <div class="uploader-container">
    <el-card class="uploader-card">
      <template #header>
        <div class="card-header">
          <span>上传地理数据</span>
        </div>
      </template>
      
      <el-alert
        title="请上传地理数据以显示图层"
        type="info"
        description="当前地图仅显示卫星底图，请上传 TIF 或 Shapefile(ZIP) 数据以添加新图层"
        show-icon
        :closable="false"
        style="margin-bottom: 15px;"
      />
      
      <el-upload
        class="upload-area"
        action="/api/upload"
        :multiple="true"
        :limit="5"
        :on-exceed="handleExceed"
        :before-upload="beforeUpload"
        :on-success="handleSuccess"
        :on-error="handleError"
        :on-progress="handleProgress"
        :file-list="fileList"
        :show-file-list="true"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .tif/.tiff 栅格数据或 .zip 格式的 Shapefile 矢量数据
          </div>
        </template>
      </el-upload>
      
      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :status="uploadStatus" />
        <div class="upload-status">{{ uploadStatusText }}</div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'FileUploader',
  components: {
    UploadFilled
  },
  data() {
    return {
      fileList: [],
      uploading: false,
      uploadProgress: 0,
      uploadStatus: '',
      uploadStatusText: ''
    }
  },
  methods: {
    handleExceed() {
      ElMessage.warning('最多只能上传5个文件')
    },
    
    beforeUpload(file) {
      // 检查文件类型
      const validTypes = ['.tif', '.tiff', '.zip']
      const isValidType = validTypes.some(type => file.name.toLowerCase().endsWith(type))
      
      if (!isValidType) {
        ElMessage.error('只支持 .tif/.tiff 或 .zip 格式的文件')
        return false
      }
      
      // 检查文件大小（限制为500MB）
      const isLessThan500M = file.size / 1024 / 1024 < 500
      if (!isLessThan500M) {
        ElMessage.error('文件大小不能超过500MB')
        return false
      }
      
      this.uploading = true
      this.uploadProgress = 0
      this.uploadStatus = ''
      this.uploadStatusText = '正在上传...'
      
      return true
    },
    
    handleProgress(event) {
      this.uploadProgress = Math.round(event.percent)
    },
    
    handleSuccess(response) {
      this.uploading = false
      this.fileList = []
      
      if (response.success) {
        this.uploadStatus = 'success'
        this.uploadStatusText = '上传成功'
        
        // 通知父组件添加新图层
        this.$emit('layer-added', {
          layerName: response.layerName,
          layerType: response.layerType,
          wmsUrl: response.wmsUrl,
          bbox: response.bbox
        })
        
        ElMessage.success('文件上传成功')
      } else {
        this.uploadStatus = 'exception'
        this.uploadStatusText = '上传失败: ' + (response.message || '未知错误')
        ElMessage.error(this.uploadStatusText)
      }
    },
    
    handleError() {
      this.uploading = false
      this.uploadStatus = 'exception'
      this.uploadStatusText = '上传失败: 服务器错误'
      ElMessage.error('上传失败，服务器无响应')
    }
  }
}
</script>

<style scoped>
.uploader-container {
  margin-bottom: 15px;
}

.uploader-card {
  margin-bottom: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.upload-progress {
  margin-top: 15px;
}

.upload-status {
  margin-top: 5px;
  text-align: center;
  color: #606266;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>