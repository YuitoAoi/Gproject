import avatar1 from '@/assets/images/avatar/avatar1.webp'
import avatar2 from '@/assets/images/avatar/avatar2.webp'
import avatar3 from '@/assets/images/avatar/avatar3.webp'
import avatar4 from '@/assets/images/avatar/avatar4.webp'
import avatar5 from '@/assets/images/avatar/avatar5.webp'
import avatar6 from '@/assets/images/avatar/avatar6.webp'
import avatar7 from '@/assets/images/avatar/avatar7.webp'
import avatar8 from '@/assets/images/avatar/avatar8.webp'
import avatar9 from '@/assets/images/avatar/avatar9.webp'
import avatar10 from '@/assets/images/avatar/avatar10.webp'

export interface User {
  id: number
  username: string
  gender: 1 | 0
  mobile: string
  email: string
  dep: string
  status: string
  create_time: string
  avatar: string
}

// 用户列表
export const ACCOUNT_TABLE_DATA: User[] = [
  {
    id: 1,
    username: 'alexmorgan',
    gender: 1,
    mobile: '18670001591',
    email: 'alexmorgan@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-09-09 10:01:10',
    avatar: avatar1
  },
  {
    id: 2,
    username: 'sophiabaker',
    gender: 1,
    mobile: '17766664444',
    email: 'sophiabaker@company.com',
    dep: '电商部',
    status: '1',
    create_time: '2020-10-10 13:01:12',
    avatar: avatar2
  },
  {
    id: 3,
    username: 'liampark',
    gender: 1,
    mobile: '18670001597',
    email: 'liampark@company.com',
    dep: '人事部',
    status: '1',
    create_time: '2020-11-14 12:01:45',
    avatar: avatar3
  },
  {
    id: 4,
    username: 'oliviagrant',
    gender: 0,
    mobile: '18670001596',
    email: 'oliviagrant@company.com',
    dep: '产品部',
    status: '1',
    create_time: '2020-11-14 09:01:20',
    avatar: avatar4
  },
  {
    id: 5,
    username: 'emmawilson',
    gender: 0,
    mobile: '18670001595',
    email: 'emmawilson@company.com',
    dep: '财务部',
    status: '1',
    create_time: '2020-11-13 11:01:05',
    avatar: avatar5
  },
  {
    id: 6,
    username: 'noahevan',
    gender: 1,
    mobile: '18670001594',
    email: 'noahevan@company.com',
    dep: '运营部',
    status: '1',
    create_time: '2020-10-11 13:10:26',
    avatar: avatar6
  },
  {
    id: 7,
    username: 'avamartin',
    gender: 1,
    mobile: '18123820191',
    email: 'avamartin@company.com',
    dep: '客服部',
    status: '2',
    create_time: '2020-05-14 12:05:10',
    avatar: avatar7
  },
  {
    id: 8,
    username: 'jacoblee',
    gender: 1,
    mobile: '18670001592',
    email: 'jacoblee@company.com',
    dep: '总经办',
    status: '3',
    create_time: '2020-11-12 07:22:25',
    avatar: avatar8
  },
  {
    id: 9,
    username: 'miaclark',
    gender: 0,
    mobile: '18670001581',
    email: 'miaclark@company.com',
    dep: '研发部',
    status: '4',
    create_time: '2020-06-12 05:04:20',
    avatar: avatar9
  },
  {
    id: 10,
    username: 'ethanharris',
    gender: 1,
    mobile: '13755554444',
    email: 'ethanharris@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-12 16:01:10',
    avatar: avatar10
  },
  {
    id: 11,
    username: 'isabellamoore',
    gender: 1,
    mobile: '13766660000',
    email: 'isabellamoore@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-14 12:01:20',
    avatar: avatar6
  },
  {
    id: 12,
    username: 'masonwhite',
    gender: 1,
    mobile: '18670001502',
    email: 'masonwhite@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-14 12:01:20',
    avatar: avatar7
  },
  {
    id: 13,
    username: 'charlottehall',
    gender: 1,
    mobile: '13006644977',
    email: 'charlottehall@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-14 12:01:20',
    avatar: avatar8
  },
  {
    id: 14,
    username: 'benjaminscott',
    gender: 0,
    mobile: '13599998888',
    email: 'benjaminscott@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-14 12:01:20',
    avatar: avatar9
  },
  {
    id: 15,
    username: 'ameliaking',
    gender: 1,
    mobile: '13799998888',
    email: 'ameliaking@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-11-14 12:01:20',
    avatar: avatar10
  }
]

export interface Role {
  roleName: string
  roleCode: string
  des: string
  date: string
  enable: boolean
}

// 角色列表
export const ROLE_LIST_DATA: Role[] = [
  {
    roleName: '超级管理员',
    roleCode: 'R_SUPER',
    des: '拥有系统全部权限',
    date: '2025-05-15 12:30:45',
    enable: true
  },
  {
    roleName: '管理员',
    roleCode: 'R_ADMIN',
    des: '拥有系统管理权限',
    date: '2025-05-15 12:30:45',
    enable: true
  },
  {
    roleName: '普通用户',
    roleCode: 'R_USER',
    des: '拥有系统普通权限',
    date: '2025-05-15 12:30:45',
    enable: true
  },
  {
    roleName: '财务管理员',
    roleCode: 'R_FINANCE',
    des: '管理财务相关权限',
    date: '2025-05-16 09:15:30',
    enable: true
  },
  {
    roleName: '数据分析师',
    roleCode: 'R_ANALYST',
    des: '拥有数据分析权限',
    date: '2025-05-16 11:45:00',
    enable: false
  },
  {
    roleName: '客服专员',
    roleCode: 'R_SUPPORT',
    des: '处理客户支持请求',
    date: '2025-05-17 14:30:22',
    enable: true
  },
  {
    roleName: '营销经理',
    roleCode: 'R_MARKETING',
    des: '管理营销活动权限',
    date: '2025-05-17 15:10:50',
    enable: true
  },
  {
    roleName: '访客用户',
    roleCode: 'R_GUEST',
    des: '仅限浏览权限',
    date: '2025-05-18 08:25:40',
    enable: false
  },
  {
    roleName: '系统维护员',
    roleCode: 'R_MAINTAINER',
    des: '负责系统维护和更新',
    date: '2025-05-18 09:50:12',
    enable: true
  },
  {
    roleName: '项目经理',
    roleCode: 'R_PM',
    des: '管理项目相关权限',
    date: '2025-05-19 13:40:35',
    enable: true
  }
]

export interface DatasetItem {
  id: number
  name: string
  description: string
  format: string
  size: number
  records: number
  status: string
  tags: { label: string; color: string }[]
  lineage: { sourceName: string; rules: string[] } | null
  source: string
  creator: string
  storagePath: string
  samples: string[]
  logs: { time: string; action: string; detail: string }[]
  uploadTime: string
  updateTime: string
}

/** 数据集列表 mock 数据 */
export const DATASET_TABLE_DATA: DatasetItem[] = [
  {
    id: 1,
    name: 'Alpaca-Cleaned-zh',
    description: '清洗后的中文 Alpaca 指令微调数据集，涵盖问答、翻译、摘要等场景',
    format: 'JSON',
    size: 245.6,
    records: 52000,
    status: 'ready',
    tags: [
      { label: '高质量', color: '#67C23A' },
      { label: '指令微调', color: '#409EFF' }
    ],
    lineage: { sourceName: '原始Alpaca数据集', rules: ['去重', '脱敏', '格式标准化'] },
    source: '本地上传',
    creator: 'Admin',
    storagePath: '/data/datasets/alpaca-cleaned-zh/',
    samples: [
      '{"instruction": "将下列句子翻译成英文", "input": "今天天气真好", "output": "The weather is really nice today."}',
      '{"instruction": "总结以下段落", "input": "人工智能技术近年来发展迅速...", "output": "人工智能技术发展迅猛，已在多领域应用。"}',
      '{"instruction": "生成一个Python函数", "input": "计算斐波那契数列", "output": "def fibonacci(n):\\n    if n <= 1: return n\\n    return fibonacci(n-1) + fibonacci(n-2)"}'
    ],
    logs: [
      { time: '2026-04-25 09:15', action: '数据清洗完成', detail: '清洗规则：去重、脱敏，共处理52000条记录' },
      { time: '2026-04-22 16:30', action: '质量检测通过', detail: '数据完整性 99.8%，格式一致性 100%' },
      { time: '2026-04-20 14:30', action: '数据集上传', detail: '由 Admin 上传，原始大小 312.4 MB' }
    ],
    uploadTime: '2026-04-20 14:30:00',
    updateTime: '2026-04-25 09:15:00'
  },
  {
    id: 2,
    name: 'ShareGPT-Vicuna-zh',
    description: 'ShareGPT 中文对话数据集，包含多轮对话数据',
    format: 'JSON',
    size: 512.3,
    records: 98000,
    status: 'ready',
    tags: [
      { label: '对话', color: '#E6A23C' },
      { label: '多轮', color: '#409EFF' }
    ],
    lineage: null,
    source: '远程导入',
    creator: 'Admin',
    storagePath: '/data/datasets/sharegpt-vicuna-zh/',
    samples: [
      '{"conversations": [{"from": "human", "value": "你好"}, {"from": "gpt", "value": "你好！有什么可以帮你的？"}]}',
      '{"conversations": [{"from": "human", "value": "解释一下机器学习"}, {"from": "gpt", "value": "机器学习是AI的一个分支..."}]}'
    ],
    logs: [
      { time: '2026-04-18 10:00', action: '远程导入完成', detail: '从 HuggingFace 导入，共 98000 条记录' }
    ],
    uploadTime: '2026-04-18 10:00:00',
    updateTime: '2026-04-22 16:45:00'
  },
  {
    id: 3,
    name: '法律文书2025Q4',
    description: '法律文书语料库 2025Q4，用于垂直领域微调',
    format: 'CSV',
    size: 1024.8,
    records: 156000,
    status: 'processing',
    tags: [
      { label: '垂直领域', color: '#F56C6C' },
      { label: '文本分类', color: '#909399' }
    ],
    lineage: { sourceName: '中国裁判文书网原始数据', rules: ['结构化解析', '敏感信息脱敏', '分段标注'] },
    source: '本地上传',
    creator: 'ZhangWei',
    storagePath: '/data/datasets/legal-2025q4/',
    samples: [
      '案号,案由,审理法院,判决结果,全文\n(2025)京01民初123号,合同纠纷,北京市第一中级人民法院,支持原告诉讼请求,"原告与被告于2024年签订..."',
      '案号,案由,审理法院,判决结果,全文\n(2025)沪02民终456号,侵权纠纷,上海市第二中级人民法院,驳回上诉维持原判,"上诉人因不服一审判决..."'
    ],
    logs: [
      { time: '2026-04-26 11:30', action: '数据清洗中', detail: '正在进行敏感信息脱敏处理' },
      { time: '2026-04-24 08:20', action: '数据集上传', detail: '由 ZhangWei 上传，原始大小 1.8 GB' }
    ],
    uploadTime: '2026-04-24 08:20:00',
    updateTime: '2026-04-26 11:30:00'
  },
  {
    id: 4,
    name: '医疗问答对',
    description: '医疗问答对数据集，包含诊断、用药、检查等专业问答',
    format: 'JSON',
    size: 189.2,
    records: 35000,
    status: 'ready',
    tags: [
      { label: '高质量', color: '#67C23A' },
      { label: '垂直领域', color: '#F56C6C' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'LiMing',
    storagePath: '/data/datasets/medical-qa/',
    samples: [
      '{"question": "患者出现发热、咳嗽症状，应如何诊断？", "answer": "需进行血常规、胸部X光检查，结合流行病学史综合判断..."}',
      '{"question": "二甲双胍的常见副作用有哪些？", "answer": "常见副作用包括胃肠道反应如恶心、腹泻，少数可出现乳酸酸中毒..."}'
    ],
    logs: [
      { time: '2026-04-16 14:20', action: '质量检测通过', detail: '医学专业审核通过，准确率 97.3%' },
      { time: '2026-04-15 16:50', action: '数据集上传', detail: '由 LiMing 上传' }
    ],
    uploadTime: '2026-04-15 16:50:00',
    updateTime: '2026-04-16 14:20:00'
  },
  {
    id: 5,
    name: '代码指令10K',
    description: '代码指令数据集，覆盖 Python、Java、TypeScript 等语言',
    format: 'JSON',
    size: 78.5,
    records: 10000,
    status: 'ready',
    tags: [
      { label: '代码', color: '#409EFF' },
      { label: '指令微调', color: '#409EFF' }
    ],
    lineage: null,
    source: '远程导入',
    creator: 'Admin',
    storagePath: '/data/datasets/code-instruct-10k/',
    samples: [
      '{"instruction": "编写一个Python函数计算最大公约数", "output": "def gcd(a, b):\\n    while b:\\n        a, b = b, a % b\\n    return a"}',
      '{"instruction": "用TypeScript定义一个用户接口", "output": "interface User {\\n  id: number;\\n  name: string;\\n  email: string;\\n}"}'
    ],
    logs: [
      { time: '2026-04-22 09:30', action: '远程导入完成', detail: '从 GitHub 仓库导入' }
    ],
    uploadTime: '2026-04-22 09:30:00',
    updateTime: '2026-04-23 10:05:00'
  },
  {
    id: 6,
    name: '金融研报2026H1',
    description: '金融报告数据集 2026H1，用于金融领域模型训练',
    format: 'CSV',
    size: 890.4,
    records: 72000,
    status: 'error',
    tags: [
      { label: '垂直领域', color: '#F56C6C' },
      { label: '金融', color: '#E6A23C' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'WangFang',
    storagePath: '/data/datasets/finance-reports-2026h1/',
    samples: [
      '报告标题,机构,日期,行业,评级,摘要\n2026年AI产业投资展望,中信证券,2026-01-15,科技,增持,"人工智能产业在2026年将继续保持高速增长..."'
    ],
    logs: [
      { time: '2026-04-23 13:20', action: '上传失败', detail: '文件编码异常：检测到混合编码 GBK/UTF-8，建议重新导出' },
      { time: '2026-04-23 13:15', action: '数据集上传', detail: '由 WangFang 上传' }
    ],
    uploadTime: '2026-04-23 13:15:00',
    updateTime: '2026-04-23 13:20:00'
  },
  {
    id: 7,
    name: '多轮对话v3',
    description: '多轮对话数据集 v3 版本，增强上下文理解能力',
    format: 'JSON',
    size: 356.7,
    records: 68000,
    status: 'ready',
    tags: [
      { label: '对话', color: '#E6A23C' },
      { label: '高质量', color: '#67C23A' }
    ],
    lineage: { sourceName: '多轮对话v2', rules: ['去除低质量样本', '上下文增强', '新增大语言模型生成数据'] },
    source: '远程导入',
    creator: 'Admin',
    storagePath: '/data/datasets/multi-turn-dialog-v3/',
    samples: [
      '{"messages": [{"role": "user", "content": "推荐一本好书"}, {"role": "assistant", "content": "你喜歡什么类型的？"}, {"role": "user", "content": "科幻"}, {"role": "assistant", "content": "推荐《三体》，中国科幻的里程碑之作"}]}'
    ],
    logs: [
      { time: '2026-04-20 08:30', action: '版本升级完成', detail: '从 v2 升级至 v3，新增 12000 条数据' },
      { time: '2026-04-19 11:45', action: '数据集导入', detail: '远程导入完成' }
    ],
    uploadTime: '2026-04-19 11:45:00',
    updateTime: '2026-04-20 08:30:00'
  },
  {
    id: 8,
    name: '电商评论情感分析',
    description: '电商评论情感分析数据集，正负向标注',
    format: 'CSV',
    size: 156.1,
    records: 45000,
    status: 'ready',
    tags: [
      { label: '情感分析', color: '#67C23A' },
      { label: '电商', color: '#E6A23C' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'ChenJie',
    storagePath: '/data/datasets/ecommerce-reviews/',
    samples: [
      '评论内容,情感标签,评分\n"物流很快，商品质量也很好",正面,5\n"收到货发现有瑕疵，很失望",负面,2'
    ],
    logs: [
      { time: '2026-04-21 18:20', action: '标注完成', detail: '自动标注 + 人工复核，准确率 95.1%' },
      { time: '2026-04-21 15:00', action: '数据集上传', detail: '由 ChenJie 上传' }
    ],
    uploadTime: '2026-04-21 15:00:00',
    updateTime: '2026-04-21 18:20:00'
  },
  {
    id: 9,
    name: '中文百科2026Q1',
    description: '中文维基百科语料，用于预训练和知识增强',
    format: 'TXT',
    size: 2048.0,
    records: 320000,
    status: 'processing',
    tags: [
      { label: '预训练', color: '#F56C6C' },
      { label: '大规模', color: '#909399' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'Admin',
    storagePath: '/data/datasets/wiki-zh-2026q1/',
    samples: [
      '人工智能（英语：Artificial Intelligence，缩写为AI）亦称智械、机器智能，指由人制造出来的机器所表现出来的智能...',
      '深度学习是机器学习的分支，是一种以人工神经网络为架构，对数据进行表征学习的算法...'
    ],
    logs: [
      { time: '2026-04-26 10:32', action: '分块上传中', detail: '已上传 65%，速度 12.5 MB/s' },
      { time: '2026-04-26 10:30', action: '开始上传', detail: '文件大小 2GB，启动分块上传' }
    ],
    uploadTime: '2026-04-26 10:30:00',
    updateTime: '2026-04-26 10:32:00'
  },
  {
    id: 10,
    name: '指令微调混合集',
    description: '混合指令微调数据集，整合多个开源数据集',
    format: 'JSON',
    size: 456.9,
    records: 88000,
    status: 'ready',
    tags: [
      { label: '指令微调', color: '#409EFF' },
      { label: '高质量', color: '#67C23A' }
    ],
    lineage: {
      sourceName: 'Alpaca + Dolly + Self-Instruct',
      rules: ['格式统一化', '质量过滤（阈值0.7）', '去重合并']
    },
    source: '远程导入',
    creator: 'Admin',
    storagePath: '/data/datasets/instruction-tuning-mix/',
    samples: [
      '{"instruction": "解释什么是过拟合", "output": "过拟合是指模型在训练数据上表现很好，但在新数据上表现差..."}',
      '{"instruction": "写一首关于春天的诗", "output": "春风拂面柳如烟，细雨沾衣杏花天..."}',
      '{"instruction": "将十进制数255转换为二进制", "output": "255的二进制表示为11111111"}'
    ],
    logs: [
      { time: '2026-04-18 12:10', action: '合并完成', detail: '整合 3 个数据源，去重后 88000 条' },
      { time: '2026-04-17 07:00', action: '数据集导入', detail: '远程导入完成' }
    ],
    uploadTime: '2026-04-17 07:00:00',
    updateTime: '2026-04-18 12:10:00'
  },
  {
    id: 11,
    name: '科学论文摘要2025',
    description: '科学论文摘要数据集，学术领域微调',
    format: 'JSON',
    size: 167.3,
    records: 28000,
    status: 'ready',
    tags: [
      { label: '学术', color: '#409EFF' },
      { label: '文本生成', color: '#67C23A' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'ZhaoQiang',
    storagePath: '/data/datasets/science-papers-2025/',
    samples: [
      '{"title": "基于Transformer的文本分类方法研究", "abstract": "本文提出了一种改进的Transformer架构用于文本分类任务...", "keywords": ["Transformer", "文本分类", "深度学习"]}'
    ],
    logs: [
      { time: '2026-04-15 16:30', action: '元数据提取完成', detail: '自动识别论文标题、摘要、关键词字段' },
      { time: '2026-04-14 09:00', action: '数据集上传', detail: '由 ZhaoQiang 上传' }
    ],
    uploadTime: '2026-04-14 09:00:00',
    updateTime: '2026-04-15 16:30:00'
  },
  {
    id: 12,
    name: '客服对话日志',
    description: '客服对话日志，用于意图识别和情感分类',
    format: 'CSV',
    size: 321.5,
    records: 95000,
    status: 'disabled',
    tags: [
      { label: '对话', color: '#E6A23C' },
      { label: '情感分析', color: '#67C23A' },
      { label: '禁用', color: '#F56C6C' }
    ],
    lineage: null,
    source: '本地上传',
    creator: 'SunLi',
    storagePath: '/data/datasets/customer-service-logs/',
    samples: [
      '会话ID,用户消息,客服回复,意图,情感\nCS001,"我的订单什么时候到？","您的订单预计明日下午到达",物流查询,中性',
      '会话ID,用户消息,客服回复,意图,情感\nCS002,"产品质量太差了，我要投诉！","非常抱歉给您带来不便...",投诉,负面'
    ],
    logs: [
      { time: '2026-04-26 09:45', action: '数据集禁用', detail: '因隐私合规审查，暂时禁用该数据集' },
      { time: '2026-04-25 14:10', action: '数据集上传', detail: '由 SunLi 上传' }
    ],
    uploadTime: '2026-04-25 14:10:00',
    updateTime: '2026-04-26 09:45:00'
  }
]

/** 上传任务队列 mock 数据 */
export const UPLOAD_TASK_QUEUE: DatasetItem[] = []

/** 清洗预览样本 mock 数据 */
export const CLEANING_SAMPLES = [
  {
    id: 1,
    raw: {
      instruction: '<p>你好，我的单号是12345678，电话是13800000000</p>',
      input: '',
      output: '退款已处理。'
    },
    processed: {
      instruction: '你好，我的单号是12345678，电话是[MASK_PHONE]',
      input: '',
      output: '退款已处理。'
    },
    diffFields: ['instruction'],
    discarded: false,
    discardReason: ''
  },
  {
    id: 2,
    raw: {
      instruction: '<div>请帮我查询订单状态</div>',
      input: '订单号 ORD-20260401-8899',
      output: '您的订单当前状态为：运输中，预计2026年4月30日送达。'
    },
    processed: {
      instruction: '请帮我查询订单状态',
      input: '订单号 ORD-20260401-8899',
      output: '您的订单当前状态为：运输中，预计2026年4月30日送达。'
    },
    diffFields: ['instruction'],
    discarded: false,
    discardReason: ''
  },
  {
    id: 3,
    raw: {
      instruction: '联系邮箱：admin@example.com，电话：13912345678',
      input: '',
      output: '请通过邮箱或电话联系我们。'
    },
    processed: {
      instruction: '联系邮箱：[MASK_EMAIL]，电话：[MASK_PHONE]',
      input: '',
      output: '请通过邮箱或电话联系我们。'
    },
    diffFields: ['instruction'],
    discarded: false,
    discardReason: ''
  },
  {
    id: 4,
    raw: {
      instruction: 'hi',
      input: '',
      output: 'hello'
    },
    processed: {
      instruction: '',
      input: '',
      output: ''
    },
    diffFields: [],
    discarded: true,
    discardReason: '基础过滤-文本长度<10'
  },
  {
    id: 5,
    raw: {
      instruction: '身份证号：320102199001011234，请验证身份信息',
      input: '姓名：张三',
      output: '身份验证通过，系统显示您的基本信息正确。'
    },
    processed: {
      instruction: '身份证号：[MASK_IDCARD]，请验证身份信息',
      input: '姓名：张三',
      output: '身份验证通过，系统显示您的基本信息正确。'
    },
    diffFields: ['instruction'],
    discarded: false,
    discardReason: ''
  }
]

/** 默认清洗配置 */
export const DEFAULT_CLEANING_CONFIG = {
  fieldMapping: { instruction: '', input: '', output: '' },
  filters: { dropEmpty: true, dropShortText: true, minLength: 10 },
  formatters: { stripHtml: true, unifyPunctuation: false },
  piiMaskers: { phone: true, idCard: false, email: true, bankCard: false },
  deduplication: { enabled: true, threshold: 0.85 }
}

/** 模拟处理日志 */
export const MOCK_PROCESSING_LOGS = [
  { time: '14:20:00', level: 'INFO' as const, message: 'Task ID: cln_9fa82b started.' },
  { time: '14:20:01', level: 'INFO' as const, message: 'Loading dataset from storage...' },
  { time: '14:20:03', level: 'INFO' as const, message: 'Dataset loaded: 52,000 records from Alpaca-Cleaned-zh' },
  { time: '14:20:05', level: 'WARN' as const, message: 'Chunk 1: Dropped 452 empty rows.' },
  { time: '14:20:08', level: 'INFO' as const, message: 'Applying HTML tag removal...' },
  { time: '14:20:12', level: 'INFO' as const, message: 'PII Masker: Masked 1,204 phone numbers.' },
  { time: '14:20:15', level: 'INFO' as const, message: 'PII Masker: Masked 487 email addresses.' },
  { time: '14:20:18', level: 'WARN' as const, message: 'Chunk 2: Dropped 89 short texts (length < 10).' },
  { time: '14:21:03', level: 'INFO' as const, message: 'Chunk 3: Dropped 156 empty rows.' },
  { time: '14:21:30', level: 'INFO' as const, message: 'MinHash Dedup: Scanning chunk 1/5...' },
  { time: '14:21:45', level: 'INFO' as const, message: 'MinHash Dedup: Chunk 1 complete, 12,340 duplicates found.' },
  { time: '14:22:15', level: 'INFO' as const, message: 'Chunk 4 processing...' },
  { time: '14:22:40', level: 'INFO' as const, message: 'MinHash Dedup: All chunks complete. Total duplicates: 8,521.' },
  { time: '14:23:00', level: 'INFO' as const, message: 'Writing output dataset...' },
  { time: '14:23:30', level: 'INFO' as const, message: 'Cleaning pipeline completed. Output: 43,034 valid records.' }
]
