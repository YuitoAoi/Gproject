import type { FastEnterConfig } from '@/types/config'

const fastEnterConfig: FastEnterConfig = {
  minWidth: 1200,
  applications: [
    {
      name: '新建训练任务',
      description: '直达模型微调配置页',
      icon: 'ri:brain-line',
      iconColor: '#377dff',
      enabled: true,
      order: 1,
      routeName: ''
    },
    {
      name: '上传/接入数据集',
      description: '直达数据解析与清洗页',
      icon: 'ri:upload-cloud-2-line',
      iconColor: '#13DEB9',
      enabled: true,
      order: 2,
      routeName: ''
    },
    {
      name: '模型对话沙箱',
      description: '直达最新就绪模型的推理测试页',
      icon: 'ri:chat-3-line',
      iconColor: '#ffb100',
      enabled: true,
      order: 3,
      routeName: ''
    },
    {
      name: '算力与存储',
      description: '查看当前算力资源与存储使用情况',
      icon: 'ri:server-line',
      iconColor: '#7A7FFF',
      enabled: true,
      order: 4,
      routeName: ''
    },
    {
      name: '任务调度中心',
      description: '查看和管理所有异步任务',
      icon: 'ri:timer-flash-line',
      iconColor: '#ff6b6b',
      enabled: true,
      order: 5,
      routeName: ''
    }
  ],
  quickLinks: [
    {
      name: '概览',
      enabled: true,
      order: 1,
      routeName: 'Overview'
    },
    {
      name: '数据管理',
      enabled: true,
      order: 2,
      routeName: 'DataManagement'
    },
    {
      name: '模型训练',
      enabled: true,
      order: 3,
      routeName: 'ModelTraining'
    },
    {
      name: '任务监控',
      enabled: true,
      order: 4,
      routeName: 'TaskMonitoring'
    },
    {
      name: '模型推理',
      enabled: true,
      order: 5,
      routeName: 'ModelInference'
    }
  ]
}

export default Object.freeze(fastEnterConfig)
