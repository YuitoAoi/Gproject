/**
 * API 接口类型定义模块
 *
 * 提供所有后端接口的类型定义
 *
 * ## 主要功能
 *
 * - 通用类型（分页参数、响应结构等）
 * - 认证类型（登录、用户信息等）
 * - 系统管理类型（用户、角色等）
 * - 全局命名空间声明
 *
 * ## 使用场景
 *
 * - API 请求参数类型约束
 * - API 响应数据类型定义
 * - 接口文档类型同步
 *
 * ## 注意事项
 *
 * - 在 .vue 文件使用需要在 eslint.config.mjs 中配置 globals: { Api: 'readonly' }
 * - 使用全局命名空间，无需导入即可使用
 *
 * ## 使用方式
 *
 * ```typescript
 * const params: Api.Auth.LoginParams = { userName: 'admin', password: '123456' }
 * const response: Api.Auth.UserInfo = await fetchUserInfo()
 * ```
 *
 * @module types/api/api
 * @author Art Design Pro Team
 */

declare namespace Api {
  /** 通用类型 */
  namespace Common {
    /** 分页参数 */
    interface PaginationParams {
      /** 当前页码 */
      current: number
      /** 每页条数 */
      size: number
      /** 总条数 */
      total: number
    }

    /** 通用搜索参数 */
    type CommonSearchParams = Pick<PaginationParams, 'current' | 'size'>

    /** 分页响应基础结构 */
    interface PaginatedResponse<T = any> {
      records: T[]
      current: number
      size: number
      total: number
    }

    /** 启用状态 */
    type EnableStatus = '1' | '2'
  }

  /** 认证类型 */
  namespace Auth {
    /** 登录参数 */
    interface LoginParams {
      email: string
      password: string
    }

    /** 登录响应 */
    interface LoginResponse {
      user_id: number
      access_token: string
      refresh_token: string
      expires_in: number
      success: boolean
      error?: string
    }

    /** 注册参数 */
    interface RegisterParams {
      name: string
      email: string
      password: string
    }

    /** 注册响应 */
    interface RegisterResponse {
      user_id: number
      name: string
      email: string
      success: boolean
      error?: string
    }

    /** 用户信息（后端响应） */
    interface UserInfo {
      id: number
      name: string
      email: string
      is_admin: boolean
      is_active: boolean
      created_at: string
      last_login: string
      error?: string
    }

    /** 前端 Store 用户信息 */
    interface FrontendUserInfo {
      userId: number
      userName: string
      email: string
      roles: string[]
      buttons: string[]
      avatar: string
    }
  }

  /** 数据管理类型 */
  namespace DataManage {
    /** 数据集列表 */
    type DatasetList = Api.Common.PaginatedResponse<DatasetListItem>

    /** 数据集标签 */
    interface DatasetTag {
      label: string
      color: string
    }

    /** 数据血缘节点 */
    interface DataLineage {
      sourceName: string
      rules: string[]
    }

    /** 数据集列表项 */
    interface DatasetListItem {
      id: number
      name: string
      description: string
      format: string
      size: number
      records: number
      status: string
      tags: DatasetTag[]
      lineage: DataLineage | null
      source: string
      creator: string
      storagePath: string
      samples: string[]
      logs: DatasetLog[]
      uploadTime: string
      updateTime: string
    }

    /** 操作日志 */
    interface DatasetLog {
      time: string
      action: string
      detail: string
    }

    /** 上传任务 */
    interface UploadTask {
      id: number
      fileName: string
      progress: number
      status: string
      speed: string
      remaining: string
    }

    /** 数据集搜索参数 */
    type DatasetSearchParams = Partial<
      Pick<DatasetListItem, 'id' | 'name' | 'format' | 'status' | 'creator'> &
        Api.Common.CommonSearchParams & {
          tag?: string
          dateRange?: [string, string]
        }
    >

    namespace DataProcessing {
      /** 字段映射配置 */
      interface FieldMapping {
        instruction: string
        input: string
        output: string
      }

      /** 过滤配置 */
      interface FilterConfig {
        dropEmpty: boolean
        dropShortText: boolean
        minLength: number
      }

      /** 格式化配置 */
      interface FormatterConfig {
        stripHtml: boolean
        unifyPunctuation: boolean
      }

      /** 隐私脱敏配置 */
      interface PiiMaskerConfig {
        phone: boolean
        idCard: boolean
        email: boolean
        bankCard: boolean
      }

      /** 去重配置 */
      interface DedupConfig {
        enabled: boolean
        threshold: number
      }

      /** 清洗完整配置 */
      interface CleaningConfig {
        fieldMapping: FieldMapping
        filters: FilterConfig
        formatters: FormatterConfig
        piiMaskers: PiiMaskerConfig
        deduplication: DedupConfig
      }

      /** 图生成任务配置（对接后端 DatasetProcessRequest） */
      interface ProcessConfig {
        api_key: string
        synthesizer_url: string
        synthesizer_model: string
        mode:
          | 'atomic'
          | 'multi_hop'
          | 'aggregated'
          | 'CoT'
          | 'multi_choice'
          | 'multi_answer'
          | 'fill_in_blank'
          | 'true_false'
        data_format: 'Alpaca' | 'Sharegpt' | 'ChatML'
        content_field?: string
        tokenizer?: string
        chunk_size?: number
        chunk_overlap?: number
        quiz_samples?: number
        partition_method?: 'dfs' | 'bfs' | 'leiden' | 'ece'
        rpm?: number
        tpm?: number
      }

      /** 清洗预览样本 */
      interface CleaningSample {
        id: number
        raw: Record<string, string>
        processed: Record<string, string>
        diffFields: string[]
        discarded: boolean
        discardReason: string
      }

      /** 处理任务状态 */
      type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

      /** 处理任务 */
      interface ProcessingTask {
        taskId: string
        datasetName: string
        status: TaskStatus
        progress: number
        eta: string
        rawCount: number
        filteredCount: number
        dedupedCount: number
        finalCount: number
      }

      /** 处理日志条目 */
      interface ProcessingLog {
        time: string
        level: 'INFO' | 'WARN' | 'ERROR'
        message: string
      }

      /** WebSocket 推送的阶段进度消息 */
      interface StageProgress {
        stage: string
        progress: number
        message: string
        status: string
      }
    }
  }

  /** 系统管理类型 */
  namespace SystemManage {
    /** 用户列表 */
    type UserList = Api.Common.PaginatedResponse<UserListItem>

    /** 用户列表项 */
    interface UserListItem {
      id: number
      avatar: string
      status: string
      userName: string
      userGender: string
      nickName: string
      userPhone: string
      userEmail: string
      userRoles: string[]
      createBy: string
      createTime: string
      updateBy: string
      updateTime: string
    }

    /** 用户搜索参数 */
    type UserSearchParams = Partial<
      Pick<UserListItem, 'id' | 'userName' | 'userGender' | 'userPhone' | 'userEmail' | 'status'> &
        Api.Common.CommonSearchParams
    >

    /** 角色列表 */
    type RoleList = Api.Common.PaginatedResponse<RoleListItem>

    /** 角色列表项 */
    interface RoleListItem {
      roleId: number
      roleName: string
      roleCode: string
      description: string
      enabled: boolean
      createTime: string
    }

    /** 角色搜索参数 */
    type RoleSearchParams = Partial<
      Pick<RoleListItem, 'roleId' | 'roleName' | 'roleCode' | 'description' | 'enabled'> &
        Api.Common.CommonSearchParams
    >
  }
}
