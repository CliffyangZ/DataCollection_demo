<template>
  <div class="data-collection-view">
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="text-h5">
            數據收集控制面板
          </v-card-title>
          <v-card-text>
            <v-form @submit.prevent="startDataCollection">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.symbol"
                    label="交易對"
                    placeholder="例如: BTC-USDT"
                    :rules="[v => !!v || '請輸入交易對']"
                    required
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.interval"
                    :items="intervalOptions"
                    label="K線間隔"
                    required
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.startTime"
                    label="開始時間"
                    type="date"
                    :rules="[v => !!v || '請選擇開始時間']"
                    required
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.endTime"
                    label="結束時間"
                    type="date"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.batchSize"
                    label="批次大小"
                    type="number"
                    :rules="[v => v > 0 || '批次大小必須大於0']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.exchange"
                    :items="exchangeOptions"
                    item-title="label"
                    item-value="value"
                    label="交易所"
                    @update:model-value="onExchangeChange"
                    required
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formData.configPath"
                    :items="[
                      {
                        filename: 'BingX_api_config2_local.json',
                        path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/BingX_api_config2_local.json',
                        exchange: 'BingX'
                      },
                      {
                        filename: 'Binance_api_config.json',
                        path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/Binance_api_config.json',
                        exchange: 'Binance'
                      },
                      {
                        filename: 'OKX_api_config.json',
                        path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/OKX_api_config.json',
                        exchange: 'OKX'
                      },
                      {
                        filename: 'ByBit_api_config.json',
                        path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/ByBit_api_config.json',
                        exchange: 'ByBit'
                      }
                    ].filter(config => config.exchange === formData.exchange)"
                    item-title="filename"
                    item-value="path"
                    label="配置文件"
                    :rules="[v => !!v || '請選擇配置文件']"
                    required
                  >
                    <template v-slot:append-outer>
                      <v-btn icon="mdi-plus" size="small" color="primary" @click="openConfigDialog"></v-btn>
                    </template>
                  </v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.sleepTime"
                    label="休眠時間(秒)"
                    type="number"
                    :rules="[v => v >= 0 || '休眠時間不能為負數']"
                  ></v-text-field>
                </v-col>
              </v-row>
              <v-btn 
                color="primary" 
                type="submit" 
                :disabled="store.isCollecting"
                :loading="store.isCollecting"
              >
                開始收集
              </v-btn>
              <v-btn 
                color="error" 
                class="ml-4" 
                @click="stopCollection" 
                :disabled="!store.isCollecting"
              >
                停止收集
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="text-h5">收集進度</v-card-title>
          <v-card-text>
            <div v-if="store.isCollecting || store.collectedKlines > 0">
              <v-progress-linear
                :model-value="store.progressPercentage"
                height="25"
                color="primary"
                striped
              >
                <template v-slot:default="{ value }">
                  <strong>{{ Math.ceil(value) }}%</strong>
                </template>
              </v-progress-linear>
              
              <v-list class="mt-4">
                <v-list-item>
                  <v-list-item-title>交易對: {{ store.symbol }}</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>K線間隔: {{ store.interval }}</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>已收集: {{ store.collectedKlines }} / {{ store.totalKlines }} 條</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>批次數: {{ store.batchCount }}</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>收集速率: {{ store.collectionRate }} 條/秒</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>預計剩餘時間: {{ store.estimatedTimeRemaining }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </div>
            <div v-else class="text-center pa-4">
              <v-icon size="64" color="grey">mdi-database-clock</v-icon>
              <div class="text-h6 mt-2">尚未開始收集數據</div>
              <div class="text-subtitle-1">請填寫上方表單並開始收集</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="text-h5">當前批次詳情</v-card-title>
          <v-card-text>
            <div v-if="store.isCollecting && store.currentBatch.startTime">
              <v-list>
                <v-list-item>
                  <v-list-item-title>開始時間: {{ formatDateTime(store.currentBatch.startTime) }}</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>結束時間: {{ formatDateTime(store.currentBatch.endTime) }}</v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>本批次數量: {{ store.currentBatch.count }} 條</v-list-item-title>
                </v-list-item>
              </v-list>
              
              <div class="text-center mt-4">
                <v-progress-circular
                  :size="100"
                  :width="10"
                  :model-value="store.progressPercentage"
                  color="primary"
                >
                  {{ Math.ceil(store.progressPercentage) }}%
                </v-progress-circular>
              </div>
            </div>
            <div v-else class="text-center pa-4">
              <v-icon size="64" color="grey">mdi-timer-sand</v-icon>
              <div class="text-h6 mt-2">尚無批次數據</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            收集歷史
            <v-spacer></v-spacer>
            <v-btn icon @click="refreshChart">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div v-if="store.collectionHistory.length > 0">
              <CollectionHistoryChart :history-data="store.collectionHistory" :key="chartKey" />
            </div>
            <div v-else class="text-center pa-4">
              <v-icon size="64" color="grey">mdi-chart-timeline</v-icon>
              <div class="text-h6 mt-2">尚無收集歷史數據</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      timeout="5000"
    >
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="showSnackbar = false"
        >
          關閉
        </v-btn>
      </template>
    </v-snackbar>
    
    <!-- 交易所API配置對話框 -->
    <v-dialog v-model="configDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5">
          {{ editingConfig ? '編輯交易所配置' : '新增交易所配置' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveConfig" ref="configForm">
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="configFormData.exchange_name"
                  :items="exchangeOptions"
                  item-title="label"
                  item-value="value"
                  label="交易所"
                  :rules="[v => !!v || '請選擇交易所']"
                  required
                ></v-select>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="configFormData.config_name"
                  label="配置名稱"
                  :rules="[v => !!v || '請輸入配置名稱']"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="configFormData.api_url"
                  label="API URL"
                  placeholder="例如: https://open-api.bingx.com"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="configFormData.api_key"
                  label="API Key"
                  :rules="[v => !!v || '請輸入API Key']"
                  required
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="configFormData.secret_key"
                  label="Secret Key"
                  :type="showSecret ? 'text' : 'password'"
                  :append-icon="showSecret ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append="showSecret = !showSecret"
                  :rules="[v => !!v || '請輸入Secret Key']"
                  required
                ></v-text-field>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="configDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveConfig">儲存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useDataCollectionStore } from '../stores/dataCollectionStore'
import CollectionHistoryChart from '../components/CollectionHistoryChart.vue'
import axios from 'axios'

export default {
  name: 'DataCollectionView',
  
  components: {
    CollectionHistoryChart
  },
  
  setup() {
    const store = useDataCollectionStore()
    const showSnackbar = ref(false)
    const snackbarText = ref('')
    const snackbarColor = ref('info')
    const chartKey = ref(0)
    const configDialog = ref(false)
    const showSecret = ref(false)
    const editingConfig = ref(false)
    const exchangeOptions = ref([])
    const configOptions = ref([])
    
    // 過濾後的配置選項（基於選中的交易所）
    const filteredConfigOptions = computed(() => {
      if (!formData.exchange) return []
      
      const filtered = configOptions.value.filter(config => {
        console.log(`過濾: 配置=${config.filename}, 交易所=${config.exchange}, 選中=${formData.exchange}`)
        return config.exchange === formData.exchange
      })
      
      console.log(`過濾結果: 找到 ${filtered.length} 個匹配的配置`)
      return filtered
    })
    
    // 無需使用計算屬性，直接在模板中過濾
    
    const formData = reactive({
      symbol: 'BTC-USDT',
      interval: '1h',
      startTime: '',
      endTime: '',
      batchSize: 1000,
      sleepTime: 1,
      exchange: '',
      configPath: ''
    })
    
    const configFormData = reactive({
      exchange_name: '',
      config_name: '',
      api_key: '',
      secret_key: '',
      api_url: ''
    })
    
    const intervalOptions = [
      { title: '1分鐘', value: '1m' },
      { title: '5分鐘', value: '5m' },
      { title: '15分鐘', value: '15m' },
      { title: '30分鐘', value: '30m' },
      { title: '1小時', value: '1h' },
      { title: '4小時', value: '4h' },
      { title: '1天', value: '1d' }
    ]
    
    // 獲取支持的交易所列表
    const fetchExchanges = async () => {
      try {
        console.log('開始獲取交易所列表...')
        const response = await axios.get('http://localhost:5001/api/exchanges')
        console.log('原始交易所API回應:', response)
        
        // 手動創建交易所列表，以防API回傳空數組或錯誤
        if (!response.data || response.data.length === 0) {
          console.log('從 API 獲取的交易所列表為空，使用手動創建的列表')
          exchangeOptions.value = [
            { label: 'BingX', value: 'BingX' },
            { label: 'Binance', value: 'Binance' },
            { label: 'OKX', value: 'OKX' },
            { label: 'ByBit', value: 'ByBit' }
          ]
        } else {
          exchangeOptions.value = response.data
        }
        
        console.log('交易所選項:', exchangeOptions.value)
      } catch (error) {
        console.error('獲取交易所列表失敗:', error)
        showNotification('獲取交易所列表失敗', 'error')
        
        // 如果發生錯誤，使用預設交易所列表
        exchangeOptions.value = [
          { label: 'BingX', value: 'BingX' },
          { label: 'Binance', value: 'Binance' },
          { label: 'OKX', value: 'OKX' },
          { label: 'ByBit', value: 'ByBit' }
        ]
        console.log('使用預設交易所列表:', exchangeOptions.value)
      }
    }
    
    // 獲取配置文件列表
    const fetchConfigs = async () => {
      try {
        console.log('開始獲取配置文件列表...')
        // 使用絕對URL來避免CORS問題
        const response = await axios.get('http://localhost:5001/api/exchanges/configs')
        console.log('原始 API 回應:', response)
        
        // 檢查響應格式並提取配置文件列表
        let configFiles = [];
        
        if (response.data && response.data.configFiles && Array.isArray(response.data.configFiles)) {
          // 新的API格式 - configFiles是一個屬性
          configFiles = response.data.configFiles;
          console.log('從API獲取配置文件列表 (新格式)')
        } else if (Array.isArray(response.data)) {
          // 舊的API格式 - 直接返回陣列
          configFiles = response.data;
          console.log('從API獲取配置文件列表 (舊格式)')
        }
        
        // 檢查是否有配置文件
        if (!configFiles || configFiles.length === 0) {
          console.log('從 API 獲取的配置文件列表為空，使用手動創建的列表')
          configOptions.value = [
            {
              filename: 'BingX_api_config2_local.json',
              path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/BingX_api_config2_local.json',
              exchange: 'BingX'
            },
            {
              filename: 'Binance_api_config.json',
              path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/Binance_api_config.json',
              exchange: 'Binance'
            },
            {
              filename: 'OKX_api_config.json',
              path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/OKX_api_config.json',
              exchange: 'OKX'
            },
            {
              filename: 'ByBit_api_config.json',
              path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/ByBit_api_config.json',
              exchange: 'ByBit'
            }
          ]
        } else {
          configOptions.value = configFiles
        }
        
        console.log('All configs:', configOptions.value)
        
        // 確保所有配置都有正確的exchange屬性
        configOptions.value.forEach(config => {
          if (!config.exchange) {
            // 如果沒有exchange屬性，嘗試從文件名提取
            const filename = config.filename || ''
            if (filename.includes('BingX')) {
              config.exchange = 'BingX'
            } else if (filename.includes('Binance')) {
              config.exchange = 'Binance'
            } else if (filename.includes('OKX')) {
              config.exchange = 'OKX'
            } else if (filename.includes('ByBit')) {
              config.exchange = 'ByBit'
            }
            console.log(`修正配置文件 ${filename} 的交易所為: ${config.exchange}`)
          }
        })
        
        // 過濾當前選中交易所的配置文件
        const filteredConfigs = configOptions.value.filter(config => {
          console.log(`比較: 配置文件交易所="${config.exchange}", 選中交易所="${formData.exchange}"`)
          return config.exchange === formData.exchange
        })
        console.log('Filtered configs for', formData.exchange, ':', filteredConfigs)
        
        // 如果有匹配的配置，選擇第一個
        if (filteredConfigs.length > 0) {
          formData.configPath = filteredConfigs[0].path
          console.log(`選擇了配置文件: ${filteredConfigs[0].filename}`)
        } else {
          formData.configPath = ''
          console.log(`沒有找到匹配的配置文件給 ${formData.exchange}`)
        }
      } catch (error) {
        console.error('獲取配置文件列表失敗:', error)
        showNotification('獲取配置文件列表失敗', 'error')
      }
    }
    
    // 獲取指定交易所的配置選項
    const getConfigOptionsForExchange = (exchange) => {
      console.log(`獲取 ${exchange} 的配置選項`)
      
      // 預設配置選項，用於備用
      const defaultConfigs = [
        {
          filename: 'BingX_api_config2_local.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/BingX_api_config2_local.json',
          exchange: 'BingX'
        },
        {
          filename: 'Binance_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/Binance_api_config.json',
          exchange: 'Binance'
        },
        {
          filename: 'OKX_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/OKX_api_config.json',
          exchange: 'OKX'
        },
        {
          filename: 'ByBit_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/ByBit_api_config.json',
          exchange: 'ByBit'
        }
      ]
      
      // 先嘗試使用過濾後的配置選項
      if (filteredConfigOptions.value && filteredConfigOptions.value.length > 0) {
        console.log(`使用過濾後的配置選項，找到 ${filteredConfigOptions.value.length} 個選項`)
        return filteredConfigOptions.value
      }
      
      // 如果過濾後的選項為空，則使用預設選項並過濾
      const filtered = defaultConfigs.filter(config => config.exchange === exchange)
      console.log(`使用預設配置選項，找到 ${filtered.length} 個選項給 ${exchange}`)
      return filtered
    }
    
    // 當交易所選擇變更時，更新相關配置
    const onExchangeChange = () => {
      console.log('Exchange changed to:', formData.exchange)
      
      if (!formData.exchange) {
        console.error('交易所為空，無法選擇配置文件')
        formData.configPath = ''
        return
      }
      
      // 預設配置選項，用於備用
      const defaultConfigs = [
        {
          filename: 'BingX_api_config2_local.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/BingX_api_config2_local.json',
          exchange: 'BingX'
        },
        {
          filename: 'Binance_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/Binance_api_config.json',
          exchange: 'Binance'
        },
        {
          filename: 'OKX_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/OKX_api_config.json',
          exchange: 'OKX'
        },
        {
          filename: 'ByBit_api_config.json',
          path: '/Users/cliffyang/Documents/Program/Crypto_Trading_Bot/TradingModel_V3/backend/api_config/ByBit_api_config.json',
          exchange: 'ByBit'
        }
      ]
      
      // 先嘗試使用過濾後的配置選項
      let configs = []
      if (filteredConfigOptions.value && filteredConfigOptions.value.length > 0) {
        configs = filteredConfigOptions.value.filter(config => config.exchange === formData.exchange)
        console.log(`使用過濾後的配置選項，找到 ${configs.length} 個選項`)
      }
      
      // 如果過濾後的選項為空，則使用預設選項並過濾
      if (configs.length === 0) {
        configs = defaultConfigs.filter(config => config.exchange === formData.exchange)
        console.log(`使用預設配置選項，找到 ${configs.length} 個選項給 ${formData.exchange}`)
      }
      
      // 如果有匹配的配置，選擇第一個
      if (configs.length > 0) {
        formData.configPath = configs[0].path
        console.log(`自動選擇了配置文件: ${configs[0].filename}`)
        console.log(`設置的完整配置路徑: ${formData.configPath}`)
      } else {
        formData.configPath = ''
        console.error(`沒有找到 ${formData.exchange} 的配置文件`)
      }
    }
    
    // 打開配置對話框
    const openConfigDialog = () => {
      editingConfig.value = false
      configFormData.exchange_name = formData.exchange
      configFormData.config_name = ''
      configFormData.api_key = ''
      configFormData.secret_key = ''
      configFormData.api_url = ''
      configDialog.value = true
    }
    
    // 保存配置
    const saveConfig = async () => {
      try {
        const response = await axios.post('http://localhost:5001/api/exchanges/config', configFormData)
        if (response.data.success) {
          showNotification('配置保存成功', 'success')
          configDialog.value = false
          // 重新獲取配置列表
          await fetchConfigs()
          // 選擇新創建的配置
          formData.configPath = response.data.config_path
        } else {
          showNotification(`配置保存失敗: ${response.data.message}`, 'error')
        }
      } catch (error) {
        console.error('保存配置失敗:', error)
        showNotification(`保存配置失敗: ${error.message}`, 'error')
      }
    }
    
    // 模擬數據收集進度更新
    let progressInterval = null
    
    const startDataCollection = async () => {
      try {
        // 確保至少有所需的資訊
        const validationErrors = [];
        
        if (!formData.symbol) validationErrors.push('請選擇交易對')
        if (!formData.startTime) validationErrors.push('請選擇開始日期')
        if (!formData.exchange) validationErrors.push('請選擇交易所')
        if (!formData.configPath) validationErrors.push('請選擇配置文件')
        
        if (validationErrors.length > 0) {
          showNotification(validationErrors.join('\n'), 'error')
          return
        }
        
        console.log('開始數據收集處理，驗證通過')
        
        // 計算預估的K線數量
        const estimatedKlines = calculateEstimatedKlines()
        
        // 更新狀態
        store.startCollection({
          symbol: formData.symbol,
          interval: formData.interval,
          startTime: formData.startTime,
          endTime: formData.endTime || new Date().toISOString().split('T')[0],
          estimatedKlines
        })
        
        // 設置預設值
        const batchSize = parseInt(formData.batchSize) || 1000
        const sleepTime = parseInt(formData.sleepTime) || 1
        
        // 檢查配置路徑是否存在並且有效
        console.log(`目前的配置路徑: ${formData.configPath}`)
        
        // 整理請求數據 - 完全符合成功 curl 請求的格式
        const requestData = {
          symbol: formData.symbol,
          interval: formData.interval,
          startTime: formData.startTime,
          endTime: formData.endTime || new Date().toISOString().split('T')[0],
          batchSize: batchSize,
          configPath: formData.configPath,
          sleepTime: sleepTime,
          exchange: formData.exchange
          // 移除不必要的 estimatedKlines 參數，它可能會導致後端問題
        }
        
        console.log('發送數據收集請求 (詳細):')
        Object.keys(requestData).forEach(key => {
          console.log(`  ${key}: ${requestData[key]}`)
        })
        
        // 使用絕對路徑以避免 CORS 或代理問題
        const apiUrl = 'http://localhost:5001/api/data-collection/start'
        console.log('調用API端點:', apiUrl)
        
        // 使用axios發送請求 (不需手動JSON.stringify，讓axios自己處理)
        const response = await axios.post(apiUrl, requestData, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        if (response.data.success) {
          showNotification('數據收集已開始', 'success')
          
          // 啟動輪詢獲取進度
          startPollingStatus()
        } else {
          store.isCollecting = false
          showNotification(`數據收集啟動失敗: ${response.data.message}`, 'error')
        }
      } catch (error) {
        console.error('啟動數據收集失敗:', error)
        store.isCollecting = false
        showNotification(`啟動數據收集失敗: ${error.message}`, 'error')
      }
    }
    
    // 輪詢數據收集狀態
    let statusPollingInterval = null
    
    const startPollingStatus = () => {
      // 每3秒獲取一次狀態
      statusPollingInterval = setInterval(async () => {
        try {
          // 使用絕對路徑以避免 CORS 或代理問題
          const response = await axios.get('http://localhost:5001/api/data-collection/status')
          const status = response.data
          
          if (!status.isCollecting) {
            // 如果收集已停止
            stopCollection()
            store.completeCollection()
            showNotification('數據收集已完成', 'success')
            return
          }
          
          // 更新進度
          store.updateProgress({
            progress: status.progressPercentage || 0,
            totalCollected: status.collectedKlines || 0,
            batchCount: status.batchCount || 0,
            batchSize: status.currentBatchSize || 0,
            currentBatchStart: status.currentBatch?.startTime,
            currentBatchEnd: status.currentBatch?.endTime
          })
        } catch (error) {
          console.error('獲取數據收集狀態失敗:', error)
        }
      }, 3000)
    }
    
    const stopCollection = async () => {
      // 清除輪詢間隔
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
        statusPollingInterval = null
      }
      
      if (store.isCollecting) {
        try {
          // 調用後端API停止數據收集
          await axios.post('http://localhost:5001/api/data-collection/stop')
          store.isCollecting = false
          showNotification('數據收集已停止', 'info')
        } catch (error) {
          console.error('停止數據收集失敗:', error)
          showNotification(`停止數據收集失敗: ${error.message}`, 'error')
        }
      }
    }
    
    const calculateEstimatedKlines = () => {
      // 計算預估的K線數量
      const startDate = new Date(formData.startTime)
      const endDate = formData.endTime ? new Date(formData.endTime) : new Date()
      
      const intervalMs = {
        '1m': 60 * 1000,
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '30m': 30 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '4h': 4 * 60 * 60 * 1000,
        '1d': 24 * 60 * 60 * 1000
      }
      
      const diffMs = endDate - startDate
      return Math.ceil(diffMs / intervalMs[formData.interval])
    }
    
    const showNotification = (text, color = 'info') => {
      snackbarText.value = text
      snackbarColor.value = color
      showSnackbar.value = true
    }
    
    const formatDateTime = (dateTimeStr) => {
      if (!dateTimeStr) return ''
      const date = new Date(dateTimeStr)
      return date.toLocaleString('zh-TW')
    }
    
    const refreshChart = () => {
      chartKey.value++
    }
    
    onMounted(async () => {
      console.log('Component mounted')
      
      // 獲取交易所列表
      await fetchExchanges()
      console.log('Exchange options loaded:', exchangeOptions.value)
      
      // 確保交易所選項有效
      if (exchangeOptions.value.length > 0) {
        // 設置默認交易所
        formData.exchange = exchangeOptions.value[0].value
        console.log('Default exchange set to:', formData.exchange)
      }
      
      // 獲取配置文件
      await fetchConfigs()
      
      // 檢查是否有正在進行的收集任務
      try {
        const response = await axios.get('/api/data-collection/status')
        const status = response.data
        
        if (status.isCollecting) {
          // 如果有正在進行的收集任務，更新狀態並啟動輪詢
          store.startCollection({
            symbol: status.symbol,
            interval: status.interval,
            startTime: status.startTime,
            endTime: status.endTime,
            estimatedKlines: status.totalKlines || 1000
          })
          
          // 更新表單數據
          formData.symbol = status.symbol
          formData.interval = status.interval
          formData.startTime = status.startTime
          formData.endTime = status.endTime
          
          // 啟動輪詢
          startPollingStatus()
        }
      } catch (error) {
        console.error('獲取數據收集狀態失敗:', error)
      }
    })
    
    onUnmounted(() => {
      if (progressInterval) {
        clearInterval(progressInterval)
      }
    })
    
    return {
      store,
      formData,
      configFormData,
      intervalOptions,
      exchangeOptions,
      configOptions,
      filteredConfigOptions,
      showSnackbar,
      snackbarText,
      snackbarColor,
      chartKey,
      configDialog,
      showSecret,
      editingConfig,
      startDataCollection,
      stopCollection,
      formatDateTime,
      refreshChart,
      fetchExchanges,
      fetchConfigs,
      onExchangeChange,
      openConfigDialog,
      saveConfig
    }
  }
}
</script>

<style scoped>
.data-collection-view {
  padding: 16px;
}
</style>