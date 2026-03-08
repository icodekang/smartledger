<template>
  <el-dialog
    v-model="visible"
    :title="isCreate ? '新建客户' : '客户详情'"
    width="900px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading">
      <el-tabs v-model="activeTab">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="客户编码">
                  <el-input v-model="form.code" disabled placeholder="自动生成" />
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <el-form-item label="客户名称" prop="name">
                  <el-input v-model="form.name" placeholder="请输入客户名称" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="客户简称">
                  <el-input v-model="form.short_name" placeholder="请输入客户简称" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="企业类型">
                  <el-select v-model="form.company_type" placeholder="请选择" style="width: 100%">
                    <el-option label="有限责任公司" value="有限责任公司" />
                    <el-option label="股份有限公司" value="股份有限公司" />
                    <el-option label="个体户" value="个体户" />
                    <el-option label="合伙企业" value="合伙企业" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="企业规模">
                  <el-select v-model="form.scale" placeholder="请选择" style="width: 100%">
                    <el-option label="小型" value="小型" />
                    <el-option label="中型" value="中型" />
                    <el-option label="大型" value="大型" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="所属行业">
                  <el-select v-model="form.industry" placeholder="请选择" style="width: 100%">
                    <el-option label="科技" value="科技" />
                    <el-option label="制造" value="制造" />
                    <el-option label="贸易" value="贸易" />
                    <el-option label="服务" value="服务" />
                    <el-option label="其他" value="其他" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="统一社会信用代码">
                  <el-input v-model="form.tax_no" placeholder="请输入税号" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="纳税人类型">
                  <el-select v-model="form.tax_type" placeholder="请选择" style="width: 100%">
                    <el-option label="一般纳税人" value="一般纳税人" />
                    <el-option label="小规模纳税人" value="小规模纳税人" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="联系电话">
                  <el-input v-model="form.phone" placeholder="请输入联系电话" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="联系邮箱">
                  <el-input v-model="form.email" placeholder="请输入邮箱" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="传真">
                  <el-input v-model="form.fax" placeholder="请输入传真" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="服务开始日期">
                  <el-date-picker v-model="form.service_start_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="服务结束日期">
                  <el-date-picker v-model="form.service_end_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 联系人 -->
        <el-tab-pane label="联系人" name="contacts">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="showContactDialog = true">+ 添加联系人</el-button>
          </div>
          <el-table :data="contacts" border size="small">
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="title" label="职位" width="100" />
            <el-table-column prop="department" label="部门" width="100" />
            <el-table-column prop="phone" label="手机" width="120" />
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="is_primary" label="主要联系人" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_primary" type="success">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeContact($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 地址 -->
        <el-tab-pane label="地址" name="addresses">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="showAddressDialog = true">+ 添加地址</el-button>
          </div>
          <el-table :data="addresses" border size="small">
            <el-table-column prop="address_type" label="地址类型" width="120" />
            <el-table-column prop="province" label="省" width="100" />
            <el-table-column prop="city" label="市" width="100" />
            <el-table-column prop="district" label="区" width="100" />
            <el-table-column prop="detail" label="详细地址" />
            <el-table-column prop="is_primary" label="主要地址" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_primary" type="success">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeAddress($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 开票信息 -->
        <el-tab-pane label="开票信息" name="invoice">
          <div class="tab-actions">
            <el-button type="primary" size="small" @click="showInvoiceDialog = true">+ 添加开票信息</el-button>
          </div>
          <el-table :data="invoiceInfos" border size="small">
            <el-table-column prop="title" label="发票抬头" />
            <el-table-column prop="tax_no" label="税号" />
            <el-table-column prop="bank_name" label="开户银行" />
            <el-table-column prop="bank_account" label="银行账号" />
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success">是</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="removeInvoiceInfo($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>

    <!-- 添加联系人对话框 -->
    <el-dialog v-model="showContactDialog" title="添加联系人" width="500px" append-to-body>
      <el-form :model="contactForm" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="contactForm.name" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="contactForm.title" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="contactForm.department" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="contactForm.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="contactForm.email" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="contactForm.is_primary">设为主要联系人</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showContactDialog = false">取消</el-button>
        <el-button type="primary" @click="addContact">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加地址对话框 -->
    <el-dialog v-model="showAddressDialog" title="添加地址" width="500px" append-to-body>
      <el-form :model="addressForm" label-width="100px">
        <el-form-item label="地址类型" required>
          <el-select v-model="addressForm.address_type" style="width: 100%">
            <el-option label="注册地址" value="注册地址" />
            <el-option label="办公地址" value="办公地址" />
            <el-option label="仓库地址" value="仓库地址" />
          </el-select>
        </el-form-item>
        <el-form-item label="省">
          <el-input v-model="addressForm.province" />
        </el-form-item>
        <el-form-item label="市">
          <el-input v-model="addressForm.city" />
        </el-form-item>
        <el-form-item label="区">
          <el-input v-model="addressForm.district" />
        </el-form-item>
        <el-form-item label="详细地址">
          <el-input v-model="addressForm.detail" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="addressForm.is_primary">设为主要地址</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddressDialog = false">取消</el-button>
        <el-button type="primary" @click="addAddress">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加开票信息对话框 -->
    <el-dialog v-model="showInvoiceDialog" title="添加开票信息" width="500px" append-to-body>
      <el-form :model="invoiceForm" label-width="100px">
        <el-form-item label="发票抬头" required>
          <el-input v-model="invoiceForm.title" />
        </el-form-item>
        <el-form-item label="税号" required>
          <el-input v-model="invoiceForm.tax_no" />
        </el-form-item>
        <el-form-item label="开户银行">
          <el-input v-model="invoiceForm.bank_name" />
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="invoiceForm.bank_account" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="invoiceForm.is_default">设为默认</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInvoiceDialog = false">取消</el-button>
        <el-button type="primary" @click="addInvoiceInfo">确定</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { customerApi, type Customer, type CustomerContact, type CustomerAddress, type CustomerInvoiceInfo } from '../../../api/customer'

const props = defineProps<{
  modelValue: boolean
  customerId?: string
  isCreate: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const saving = ref(false)
const activeTab = ref('basic')
const formRef = ref()

const form = ref<Partial<Customer>>({
  name: '',
  short_name: '',
  company_type: '',
  industry: '',
  scale: '',
  tax_no: '',
  tax_type: '一般纳税人',
  phone: '',
  email: '',
  fax: '',
  website: '',
  service_start_date: '',
  service_end_date: '',
  remark: ''
})

const rules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}

const contacts = ref<CustomerContact[]>([])
const addresses = ref<CustomerAddress[]>([])
const invoiceInfos = ref<CustomerInvoiceInfo[]>([])

// 子对话框显示
const showContactDialog = ref(false)
const showAddressDialog = ref(false)
const showInvoiceDialog = ref(false)

// 表单
const contactForm = ref<CustomerContact>({
  name: '',
  title: '',
  department: '',
  phone: '',
  email: '',
  is_primary: false
})

const addressForm = ref<CustomerAddress>({
  address_type: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_primary: false
})

const invoiceForm = ref<CustomerInvoiceInfo>({
  title: '',
  tax_no: '',
  bank_name: '',
  bank_account: '',
  is_default: true
})

const fetchDetail = async () => {
  if (!props.customerId) return
  loading.value = true
  try {
    const res = await customerApi.getDetail(props.customerId)
    const data = res.data
    
    form.value = {
      code: data.code,
      name: data.name,
      short_name: data.short_name,
      company_type: data.company_type,
      industry: data.industry,
      scale: data.scale,
      tax_no: data.tax_no,
      tax_type: data.tax_type,
      phone: data.phone,
      email: data.email,
      fax: data.fax,
      website: data.website,
      service_start_date: data.service_start_date,
      service_end_date: data.service_end_date,
      remark: data.remark
    }
    
    contacts.value = data.contacts || []
    addresses.value = data.addresses || []
    invoiceInfos.value = data.invoice_infos || []
  } catch (error) {
    console.error('获取详情失败:', error)
  } finally {
    loading.value = false
  }
}

// 添加联系人
const addContact = () => {
  if (!contactForm.value.name) {
    ElMessage.warning('请输入姓名')
    return
  }
  contacts.value.push({ ...contactForm.value })
  contactForm.value = { name: '', title: '', department: '', phone: '', email: '', is_primary: false }
  showContactDialog.value = false
}

const removeContact = (index: number) => {
  contacts.value.splice(index, 1)
}

// 添加地址
const addAddress = () => {
  if (!addressForm.value.address_type) {
    ElMessage.warning('请选择地址类型')
    return
  }
  addresses.value.push({ ...addressForm.value })
  addressForm.value = { address_type: '', province: '', city: '', district: '', detail: '', is_primary: false }
  showAddressDialog.value = false
}

const removeAddress = (index: number) => {
  addresses.value.splice(index, 1)
}

// 添加开票信息
const addInvoiceInfo = () => {
  if (!invoiceForm.value.title || !invoiceForm.value.tax_no) {
    ElMessage.warning('请填写完整信息')
    return
  }
  invoiceInfos.value.push({ ...invoiceForm.value })
  invoiceForm.value = { title: '', tax_no: '', bank_name: '', bank_account: '', is_default: true }
  showInvoiceDialog.value = false
}

const removeInvoiceInfo = (index: number) => {
  invoiceInfos.value.splice(index, 1)
}

// 保存
const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  saving.value = true
  try {
    let customerId = props.customerId
    
    if (props.isCreate) {
      const res = await customerApi.create(form.value)
      customerId = res.data.id
    } else {
      await customerApi.update(props.customerId!, form.value)
    }
    
    // 保存联系人
    for (const contact of contacts.value) {
      if (!contact.id) {
        await customerApi.addContact(customerId!, contact)
      }
    }
    
    ElMessage.success(props.isCreate ? '创建成功' : '保存成功')
    emit('success')
    handleClose()
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  visible.value = false
}

watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.isCreate) {
      form.value = {
        name: '',
        short_name: '',
        company_type: '',
        industry: '',
        scale: '',
        tax_no: '',
        tax_type: '一般纳税人',
        phone: '',
        email: '',
        fax: '',
        website: '',
        service_start_date: '',
        service_end_date: '',
        remark: ''
      }
      contacts.value = []
      addresses.value = []
      invoiceInfos.value = []
    } else {
      fetchDetail()
    }
  }
})
</script>

<style scoped>
.tab-actions {
  margin-bottom: 16px;
}
</style>
