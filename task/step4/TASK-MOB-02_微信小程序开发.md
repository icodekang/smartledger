# 任务编号：TASK-MOB-02
# 任务名称：微信小程序开发
# 优先级：P1
# 预估工期：3天
# 负责人：前端

================================================================================
                              任务描述
================================================================================

开发微信小程序，提供更便捷的移动端体验，支持扫码、拍照、消息推送等原生能力。

================================================================================
                              需求详情
================================================================================

## 1. 技术选型

- **框架**: Taro 3 (React/Vue)
- **UI库**: Taro UI
- **状态管理**: Redux/Mobx
- **构建工具**: Webpack

## 2. 目录结构

```
weapp/
├── src/
│   ├── app.config.ts       # 全局配置
│   ├── app.tsx             # 入口
│   ├── pages/              # 页面
│   │   ├── index/          # 首页
│   │   ├── bills/          # 票据
│   │   ├── scan/           # 扫码
│   │   ├── reports/        # 报表
│   │   └── profile/        # 我的
│   ├── components/         # 组件
│   ├── utils/              # 工具
│   └── services/           # API服务
├── config/
└── package.json
```

## 3. 核心功能

### 3.1 扫码上传
```typescript
// pages/scan/index.tsx
import Taro, { useCamera } from '@tarojs/taro'

export default function ScanPage() {
  const handleScan = async () => {
    // 调用扫码
    const { result } = await Taro.scanCode({
      scanType: ['qrCode', 'barCode']
    })
    
    // 解析发票二维码
    if (result.startsWith('http')) {
      // 电子发票URL
      const invoiceInfo = await parseInvoiceQR(result)
      // 自动填充
      navigateTo('/pages/bills/create', { invoiceInfo })
    }
  }
  
  const handleTakePhoto = async () => {
    // 拍照上传
    const { tempFilePaths } = await Taro.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera']
    })
    
    // 上传识别
    const uploadRes = await uploadFile({
      url: `${API_BASE}/invoices/upload`,
      filePath: tempFilePaths[0],
      name: 'file'
    })
    
    Taro.showToast({ title: '上传成功' })
  }
  
  return (
    <View className='scan-page'>
      <Button onClick={handleScan}>扫码识别</Button>
      <Button onClick={handleTakePhoto}>拍照上传</Button>
    </View>
  )
}
```

### 3.2 票据管理
```typescript
// pages/bills/index.tsx
import { useEffect, useState } from 'react'
import { View, ScrollView } from '@tarojs/components'
import { AtList, AtListItem, AtSwipeAction } from 'taro-ui'

export default function BillsPage() {
  const [bills, setBills] = useState([])
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    loadBills()
  }, [])
  
  const loadBills = async () => {
    setLoading(true)
    const res = await getBillsList()
    setBills(res.data)
    setLoading(false)
  }
  
  const handleDelete = async (id) => {
    await Taro.showModal({
      title: '确认删除',
      content: '删除后不可恢复'
    })
    
    await deleteBill(id)
    loadBills()
  }
  
  return (
    <ScrollView
      scrollY
      onScrollToLower={loadMore}
      style={{ height: '100vh' }}
    >
      <AtList>
        {bills.map(bill => (
          <AtSwipeAction
            key={bill.id}
            options={[
              { text: '删除', style: { backgroundColor: '#FF4949' } }
            ]}
            onClick={() => handleDelete(bill.id)}
          >
            <AtListItem
              title={bill.seller_name}
              note={`${bill.invoice_date} · ${bill.invoice_no}`}
              extra={`¥${bill.total_amount}`}
              arrow
              onClick={() => navigateTo(`/pages/bills/detail?id=${bill.id}`)}
            />
          </AtSwipeAction>
        ))}
      </AtList>
      
      <AtFab onClick={() => navigateTo('/pages/scan/index')} >
        上传
      </AtFab>
    </ScrollView>
  )
}
```

### 3.3 订阅消息推送
```typescript
// 请求订阅权限
const requestSubscribe = async () => {
  const res = await Taro.requestSubscribeMessage({
    tmplIds: [
      'TEMPLATE_ID_1', // 审核提醒
      'TEMPLATE_ID_2', // 结账提醒
    ]
  })
  
  if (res['TEMPLATE_ID_1'] === 'accept') {
    // 保存订阅状态到后端
    await subscribeNotification(['audit_reminder'])
  }
}

// 推送消息（后端调用微信API）
// 当有待审核凭证时，后端调用微信订阅消息接口推送
```

## 4. 小程序配置

```typescript
// app.config.ts
export default defineAppConfig({
  pages: [
    'pages/index/index',
    'pages/bills/index',
    'pages/bills/detail',
    'pages/scan/index',
    'pages/reports/index',
    'pages/profile/index',
  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBarBackgroundColor: '#fff',
    navigationBarTitleText: 'SmartLedger',
    navigationBarTextStyle: 'black'
  },
  tabBar: {
    list: [
      { pagePath: 'pages/index/index', text: '首页', iconPath: 'assets/home.png' },
      { pagePath: 'pages/bills/index', text: '票据', iconPath: 'assets/bill.png' },
      { pagePath: 'pages/reports/index', text: '报表', iconPath: 'assets/chart.png' },
      { pagePath: 'pages/profile/index', text: '我的', iconPath: 'assets/user.png' },
    ]
  },
  // 权限配置
  permission: {
    'scope.camera': {
      desc: '用于拍照上传票据'
    }
  }
})
```

## 5. 原生能力使用

```typescript
// 获取微信登录code
const wxLogin = async () => {
  const { code } = await Taro.login()
  
  // 后端换取openid
  const res = await request({
    url: '/api/v1/auth/wechat-login',
    method: 'POST',
    data: { code }
  })
  
  // 保存token
  Taro.setStorageSync('token', res.token)
}

// 获取用户信息（需用户授权）
const getUserProfile = async () => {
  const { userInfo } = await Taro.getUserProfile({
    desc: '用于完善用户资料'
  })
  
  await updateUserInfo({
    nickname: userInfo.nickName,
    avatar: userInfo.avatarUrl
  })
}

// 文件预览
const previewFile = (url: string) => {
  Taro.downloadFile({
    url,
    success: (res) => {
      Taro.openDocument({
        filePath: res.tempFilePath
      })
    }
  })
}
```

================================================================================
                              验收标准
================================================================================

1. [ ] 微信登录正常
2. [ ] 扫码识别发票二维码
3. [ ] 拍照上传正常
4. [ ] 订阅消息推送到达
5. [ ] 核心功能可用
6. [ ] 通过小程序审核

================================================================================
                              开发提示
================================================================================

1. 需要申请微信小程序账号
2. 服务端域名需配置到白名单
3. 注意用户隐私保护
4. 图片上传大小限制
5. 做好错误处理和重试
