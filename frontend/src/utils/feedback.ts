import { ElMessage, ElMessageBox } from 'element-plus'

export function showSuccess(message: string) {
  ElMessage.success({ message, duration: 2000 })
}

export function showError(message: string) {
  ElMessage.error({ message, duration: 5000, showClose: true })
}

export function showWarning(message: string) {
  ElMessage.warning({ message, duration: 3000 })
}

export function showInfo(message: string) {
  ElMessage.info({ message, duration: 2000 })
}

export async function confirmDelete(itemName: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(
      `确定删除 "${itemName}" 吗？删除后不可恢复。`,
      '确认删除',
      { 
        type: 'warning', 
        confirmButtonClass: 'el-button--danger',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    return true
  } catch {
    return false
  }
}

export async function confirmAction(
  title: string, 
  message: string, 
  type: 'warning' | 'info' | 'success' = 'warning'
): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, { type })
    return true
  } catch {
    return false
  }
}
