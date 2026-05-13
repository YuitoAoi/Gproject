/**
 * 系统全局配置
 */

const appConfig = {
  // 系统信息
  systemInfo: {
    name: 'LLaMA-Factory Workstation'
  },
  // 系统主题样式
  systemThemeStyles: {
    light: { className: '' },
    dark: { className: 'dark' }
  },
  // 菜单主题列表
  themeList: [
    {
      theme: 'design',
      background: '#FFFFFF',
      systemNameColor: 'var(--lfp-gray-800)',
      iconColor: '#6B6B6B',
      textColor: '#29343D'
    },
    {
      theme: 'dark',
      background: '#191A23',
      systemNameColor: '#D9DADB',
      iconColor: '#BABBBD',
      textColor: '#BABBBD'
    }
  ],
  // 暗黑模式菜单样式
  darkMenuStyles: [
    {
      theme: 'dark',
      background: 'var(--default-box-color)',
      systemNameColor: '#DDDDDD',
      iconColor: '#BABBBD',
      textColor: 'rgba(#FFFFFF, 0.7)'
    }
  ],
  // 系统主色
  systemMainColor: [
    '#5D87FF',
    '#B48DF3',
    '#1D84FF',
    '#60C041',
    '#38C0FC',
    '#F9901F',
    '#FF80C8'
  ] as const
}

export default Object.freeze(appConfig)
