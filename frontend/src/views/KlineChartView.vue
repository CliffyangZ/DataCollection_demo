<template>
  <div class="kline-chart-view">
    <!-- 工具列表 -->
    <div class="chart-toolbar">
      <div class="tool-button" :class="{ active: activeTool === 'crosshair' }" @click="setTool('crosshair')" title="十字準心">
        <v-icon>mdi-crosshairs</v-icon>
      </div>
      <div class="tool-button" :class="{ active: activeTool === 'trendline' }" @click="setTool('trendline')" title="趨勢線">
        <v-icon>mdi-chart-line</v-icon>
      </div>
      <div class="tool-button" :class="{ active: activeTool === 'eraser' }" @click="setTool('eraser')" title="橡皮擦">
        <v-icon>mdi-eraser</v-icon>
      </div>
    </div>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center justify-space-between">
            <div>
              <span class="text-h6">K線圖表</span>
              <span class="text-subtitle-1 ml-2">
                {{ selectedSymbol }}
              </span>
            </div>
            <div class="d-flex align-center">
              <v-select
                v-model="selectedSymbol"
                :items="symbols"
                label="交易對"
                density="compact"
                hide-details
                class="symbol-select mr-2"
                @update:model-value="loadKlineData"
              ></v-select>
              
              <v-select
                v-model="selectedInterval"
                :items="intervals"
                label="時間間隔"
                density="compact"
                hide-details
                class="interval-select mr-2"
                @update:model-value="loadKlineData"
              ></v-select>
              
              <v-btn
                icon
                variant="text"
                @click="loadKlineData"
                :loading="isLoading"
              >
                <v-icon>mdi-refresh</v-icon>
              </v-btn>
            </div>
          </v-card-title>
          
          <v-divider></v-divider>
          
          <v-card-text>
            <!-- 價格統計卡片 -->
            <div class="d-flex justify-space-between mb-4">
              <!-- 當前價格 -->
              <div class="stats-card price-card">
                <div class="text-overline">當前價格</div>
                <div class="text-h5">{{ currentPrice }}</div>
              </div>
              
              <!-- 價格變化 -->
              <div class="stats-card price-card">
                <div class="text-overline">價格變化</div>
                <div class="text-h5" :class="priceChangeColor">
                  {{ hoveredCandle ? (hoveredCandle.percentChange >= 0 ? '+' : '') + hoveredCandle.percentChange + '%' : priceChange24h }}
                </div>
              </div>
              
              <!-- OHLC 顯示 -->
              <div class="stats-card ohlc-card">
                <div class="d-flex justify-space-between">
                  <div>
                    <div class="text-caption">開盤</div>
                    <div class="text-subtitle-1" :class="getOhlcColor('open')">
                      {{ hoveredCandle ? hoveredCandle.open : currentPrice }}
                    </div>
                  </div>
                  <div>
                    <div class="text-caption">最高</div>
                    <div class="text-subtitle-1 text-success">
                      {{ hoveredCandle ? hoveredCandle.high : high24h }}
                    </div>
                  </div>
                  <div>
                    <div class="text-caption">最低</div>
                    <div class="text-subtitle-1 text-error">
                      {{ hoveredCandle ? hoveredCandle.low : low24h }}
                    </div>
                  </div>
                  <div>
                    <div class="text-caption">收盤</div>
                    <div class="text-subtitle-1" :class="getOhlcColor('close')">
                      {{ hoveredCandle ? hoveredCandle.close : currentPrice }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="chart-wrapper">
              <!-- 圖表容器 -->
              <div class="chart-container-wrapper">
                <div ref="chartContainer" class="chart-container"></div>
                <div ref="drawingLayer" class="drawing-layer"></div>
              </div>
            </div>
            
            <div class="d-flex justify-space-between mt-4">
              <div><strong>數據點數:</strong> {{ dataPointsCount }}</div>
              <div><strong>時間範圍:</strong> {{ dataTimeRange }}</div>
              <div><strong>最後更新:</strong> {{ lastUpdated }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts'
import klineDataService from '@/services/klineDataService'

export default {
  name: 'KlineChartView',
  setup() {
    // 響應式狀態
    const chartContainer = ref(null)
    const drawingLayer = ref(null)
    const chart = ref(null)
    const candlestickSeries = ref(null)
    const volumeSeries = ref(null)
    
    // 繪圖工具狀態
    const activeTool = ref('crosshair') // 默認選中十字準心工具
    const isDrawing = ref(false)
    const startPoint = ref({ x: 0, y: 0 })
    const endPoint = ref({ x: 0, y: 0 })
    const drawnLines = ref([]) // 存儲已繪製的線條
    
    // 滑鼠懸停在K線上的數據
    const hoveredCandle = ref(null)
    
    // OHLC 數據顯示
    const ohlcData = ref({
      open: '0.00',
      high: '0.00',
      low: '0.00',
      close: '0.00',
      percentChange: '0.00'
    })
    
    // 交易對和時間間隔選擇
    const selectedSymbol = ref('BTC-USDT')
    const selectedInterval = ref('1h')
    const symbols = ref(['BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'SOL-USDT'])
    const intervals = ref(['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'])
    
    // 狀態和統計數據
    const isLoading = ref(false)
    const currentPrice = ref('0.00')
    const priceChange24h = ref('0.00 (0.00%)')
    const high24h = ref('0.00')
    const low24h = ref('0.00')
    const volume24h = ref('0.00')
    const dataPointsCount = ref(0)
    const dataTimeRange = ref('無數據')
    const lastUpdated = ref('-')
    
    // 通知相關
    const showSnackbar = ref(false)
    const snackbarText = ref('')
    const snackbarColor = ref('info')
    
    // 計算屬性
    const priceChangeColor = computed(() => {
      const change = priceChange24h.value;
      if (!change) return '';
      return change.includes('-') ? 'text-error' : 'text-success';
    })
    
    // 獲取OHLC顯示顏色
    const getOhlcColor = (type) => {
      if (!hoveredCandle.value) return '';
      
      if (type === 'open' || type === 'close') {
        const open = parseFloat(hoveredCandle.value.open);
        const close = parseFloat(hoveredCandle.value.close);
        
        if (type === 'open') {
          return open < close ? 'text-success' : (open > close ? 'text-error' : '');
        } else {
          return close > open ? 'text-success' : (close < open ? 'text-error' : '');
        }
      }
      
      return '';
    }
    
    // 初始化圖表
    const initChart = () => {
      try {
        console.log('Initializing chart, container exists:', !!chartContainer.value);
        if (chartContainer.value) {
          console.log('Chart container dimensions:', chartContainer.value.clientWidth, 'x', chartContainer.value.clientHeight);
          
          // 創建圖表，設置多窗格支持
          chart.value = createChart(chartContainer.value, {
            width: chartContainer.value.clientWidth || 800,
            height: 500,
            layout: {
              background: { color: '#1E1E1E' },
              textColor: '#D9D9D9',
            },
            grid: {
              vertLines: { color: '#2B2B43' },
              horzLines: { color: '#2B2B43' },
            },
            crosshair: {
              mode: 0,
            },
            timeScale: {
              timeVisible: true,
              secondsVisible: false,
              borderColor: '#2B2B43',
            }
          })
          
          console.log('Chart created successfully');
          
          // 添加K線圖 - 使用新的 API
          candlestickSeries.value = chart.value.addSeries(CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          })
          
          // 創建單獨的窗格用於成交量圖
          const volumePane = chart.value.addPane({
            height: 150  // 成交量窗格的高度
          });
          
          // 添加成交量圖 - 使用新的 API，放在單獨的窗格中
          volumeSeries.value = volumePane.addSeries(HistogramSeries, {
            color: '#26a69a',
            priceFormat: {
              type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          
          console.log('Series added successfully');
          
          // 訂閱十字準心移動事件，更新懸停在K線上的數據
          chart.value.subscribeCrosshairMove(param => {
            try {
              if (param && param.time && candlestickSeries.value && param.seriesData) {
                // 取得十字準心位置的K線數據
                const currentData = param.seriesData.get(candlestickSeries.value);
                
                if (currentData) {
                  // 取得所有K線數據以計算漲跌百分比
                  const allData = candlestickSeries.value.data();
                  const dataIndex = allData.findIndex(d => d.time === param.time);
                  const prevData = dataIndex > 0 ? allData[dataIndex - 1] : null;
                  
                  // 計算與前一根K線的漲跌百分比
                  let percentChange = '0.00';
                  if (prevData) {
                    const change = ((currentData.close - prevData.close) / prevData.close) * 100;
                    percentChange = change.toFixed(2);
                  }
                  
                  // 更新懸停在K線上的數據
                  hoveredCandle.value = {
                    open: currentData.open.toFixed(2),
                    high: currentData.high.toFixed(2),
                    low: currentData.low.toFixed(2),
                    close: currentData.close.toFixed(2),
                    percentChange: percentChange,
                    time: param.time
                  };
                } else {
                  hoveredCandle.value = null;
                }
              } else {
                // 如果滑鼠移出圖表區域，清除懸停數據
                hoveredCandle.value = null;
              }
            } catch (error) {
              console.error('十字準心數據更新錯誤:', error);
              hoveredCandle.value = null;
            }
          });
          
          // 響應式調整
          const handleResize = () => {
            if (chart.value && chartContainer.value) {
              chart.value.applyOptions({
                width: chartContainer.value.clientWidth || 800,
              })
            }
          }
          
          window.addEventListener('resize', handleResize);
          
          // Force a resize after a short delay to ensure proper rendering
          setTimeout(handleResize, 100);
        } else {
          console.error('Chart container element not found');
          showNotification('圖表容器初始化失敗', 'error');
        }
      } catch (error) {
        console.error('Error initializing chart:', error);
        showNotification('圖表初始化失敗: ' + error.message, 'error');
      }
    }
    
    // 加載K線數據
    const loadKlineData = async () => {
      try {
        isLoading.value = true
        showNotification('正在加載數據...', 'info')
        
        // 確保圖表已初始化
        if (!chart.value) {
          console.log('圖表未初始化，重新初始化圖表')
          initChart()
        }
        
        // 確保圖表系列已初始化
        if (!candlestickSeries.value || !volumeSeries.value) {
          console.log('圖表系列未初始化，初始化系列')
          // 添加K線圖 - 使用新的 API
          candlestickSeries.value = chart.value.addSeries(CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          })
          
          // 創建單獨的窗格用於成交量圖
          const volumePane = chart.value.addPane({
            height: 150  // 成交量窗格的高度
          });
          
          // 添加成交量圖 - 使用新的 API，放在單獨的窗格中
          volumeSeries.value = volumePane.addSeries(HistogramSeries, {
            color: '#26a69a',
            priceFormat: {
              type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          console.log('系列初始化完成')
        }
        
        // 從API獲取K線數據 - 傳遞null作為limit參數以獲取所有可用數據
        console.log(`請求數據: ${selectedSymbol.value}, ${selectedInterval.value}, 無數據限制`)
        const response = await klineDataService.getKlineData(selectedSymbol.value, selectedInterval.value, null, null, null)
        
        console.log('收到回應:', response)
        
        if (response.data && response.data.data && response.data.data.length > 0) {
          const data = response.data.data
          console.log(`收到 ${data.length} 條數據記錄`)
          
          // 更新統計信息
          updateStats(data)
          
          // 確保系列存在再設置數據
          if (candlestickSeries.value && volumeSeries.value) {
            // 清除現有數據
            candlestickSeries.value.setData([])
            volumeSeries.value.setData([])
            
            // 設置新數據
            candlestickSeries.value.setData(data)
            
            // 設置成交量數據
            const volumeData = data.map(item => ({
              time: item.time,
              value: item.volume,
              color: item.close >= item.open ? 'rgba(0, 150, 136, 0.8)' : 'rgba(255, 82, 82, 0.8)'
            }))
            
            volumeSeries.value.setData(volumeData)
            
            // 加載市場統計數據
            await loadMarketStats()
            
            // 顯示成功通知
            showNotification(`成功加載 ${data.length} 條數據記錄`, 'success')
          } else {
            console.error('圖表系列仍然未初始化')
            showNotification('圖表初始化失敗，請重試', 'error')
          }
        } else {
          console.warn('無法獲取實際數據')
          showNotification('無法獲取實際數據，請檢查後端數據庫', 'warning')
        }
      } catch (error) {
        console.error('加載K線數據失敗:', error)
        showNotification('加載數據失敗，請檢查後端API連接', 'error')
      } finally {
        isLoading.value = false
      }
    }
    
    // 加載模擬數據
    // 移除了模擬數據相關功能，僅使用實際數據
    
    // 更新統計信息
    const updateStats = (data) => {
      if (data && data.length > 0) {
        // 更新數據點數量
        dataPointsCount.value = data.length
        
        // 更新時間範圍
        const startDate = new Date(data[0].time * 1000)
        const endDate = new Date(data[data.length - 1].time * 1000)
        dataTimeRange.value = `${formatDate(startDate)} - ${formatDate(endDate)}`
        
        // 更新最後更新時間
        lastUpdated.value = formatDate(new Date())
        
        // 更新當前價格
        currentPrice.value = data[data.length - 1].close.toFixed(2)
      }
    }
    
    // 加載市場統計數據
    const loadMarketStats = async () => {
      try {
        const response = await klineDataService.getMarketStats(selectedSymbol.value)
        
        if (response.data && response.data.data) {
          const stats = response.data.data
          
          // 更新24小時變化
          const change = stats.priceChange24h || 0
          const changePercent = stats.priceChangePercent24h || 0
          priceChange24h.value = `${change.toFixed(2)} (${changePercent.toFixed(2)}%)`
          
          // 更新24小時最高/最低
          high24h.value = stats.high24h ? stats.high24h.toFixed(2) : '0.00'
          low24h.value = stats.low24h ? stats.low24h.toFixed(2) : '0.00'
          
          // 更新24小時成交量
          volume24h.value = stats.volume24h ? formatVolume(stats.volume24h) : '0.00'
        }
      } catch (error) {
        console.error('加載市場統計數據失敗:', error)
      }
    }
    
    // 格式化日期
    const formatDate = (date) => {
      return date.toLocaleString()
    }
    
    // 格式化成交量
    const formatVolume = (volume) => {
      if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(2) + 'B'
      } else if (volume >= 1000000) {
        return (volume / 1000000).toFixed(2) + 'M'
      } else if (volume >= 1000) {
        return (volume / 1000).toFixed(2) + 'K'
      } else {
        return volume.toFixed(2)
      }
    }
    
    // 顯示通知
    const showNotification = (text, color = 'info') => {
      snackbarText.value = text
      snackbarColor.value = color
      showSnackbar.value = true
    }
    
    // 工具選擇和繪圖功能
    const setTool = (tool) => {
      activeTool.value = tool
      
      // 切換十字準心
      if (chart.value) {
        if (tool === 'crosshair') {
          chart.value.applyOptions({
            crosshair: {
              mode: 1, // 0: 無, 1: 十字準心, 2: 水平線, 3: 垂直線
              vertLine: {
                visible: true,
                labelVisible: true,
              },
              horzLine: {
                visible: true,
                labelVisible: true,
              },
            },
          })
          
          // 十字準心模式下，繪圖層不應該攜擋滑鼠事件
          if (drawingLayer.value) {
            drawingLayer.value.style.pointerEvents = 'none'
          }
        } else {
          // 其他工具時隱藏十字準心
          chart.value.applyOptions({
            crosshair: {
              mode: 0,
              vertLine: {
                visible: false,
                labelVisible: false,
              },
              horzLine: {
                visible: false,
                labelVisible: false,
              },
            },
          })
          
          // 其他工具模式下，繪圖層需要接收滑鼠事件
          if (drawingLayer.value) {
            drawingLayer.value.style.pointerEvents = 'auto'
          }
        }
      }
      
      // 如果選擇橡皮擦工具，設置鼠標樣式
      if (tool === 'eraser' && drawingLayer.value) {
        drawingLayer.value.style.cursor = 'url("/eraser-cursor.png"), auto'
      } else if (drawingLayer.value) {
        drawingLayer.value.style.cursor = 'crosshair'
      }
    }
    
    // 初始化繪圖層事件
    const initDrawingLayer = () => {
      if (!drawingLayer.value) return
      
      // 根據選擇的工具設置初始狀態
      if (activeTool.value === 'crosshair') {
        drawingLayer.value.style.pointerEvents = 'none'
      } else {
        drawingLayer.value.style.pointerEvents = 'auto'
      }
      
      // 滑鼠按下事件 - 開始繪圖
      drawingLayer.value.addEventListener('mousedown', (e) => {
        // 如果是十字準心模式，不處理滑鼠事件
        if (activeTool.value === 'crosshair') return
        
        if (activeTool.value === 'trendline') {
          isDrawing.value = true
          const rect = drawingLayer.value.getBoundingClientRect()
          startPoint.value = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
          }
          endPoint.value = { ...startPoint.value }
        } else if (activeTool.value === 'eraser') {
          // 橡皮擦功能 - 檢查是否點擊了已繪製的線條
          const rect = drawingLayer.value.getBoundingClientRect()
          const clickPoint = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
          }
          
          // 檢查是否點擊了線條
          const lineIndex = findLineNearPoint(clickPoint)
          if (lineIndex !== -1) {
            // 刪除該線條
            drawnLines.value.splice(lineIndex, 1)
            redrawLines()
          }
        }
      })
      
      // 滑鼠移動事件 - 繪製預覽
      drawingLayer.value.addEventListener('mousemove', (e) => {
        if (isDrawing.value && activeTool.value === 'trendline') {
          const rect = drawingLayer.value.getBoundingClientRect()
          endPoint.value = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
          }
          redrawLines()
        }
      })
      
      // 滑鼠放開事件 - 完成繪圖
      drawingLayer.value.addEventListener('mouseup', () => {
        if (isDrawing.value && activeTool.value === 'trendline') {
          // 保存繪製的線條
          drawnLines.value.push({
            start: { ...startPoint.value },
            end: { ...endPoint.value }
          })
          isDrawing.value = false
        }
      })
      
      // 滑鼠離開事件 - 取消繪圖
      drawingLayer.value.addEventListener('mouseleave', () => {
        if (isDrawing.value) {
          isDrawing.value = false
          redrawLines()
        }
      })
    }
    
    // 重新繪製所有線條
    const redrawLines = () => {
      if (!drawingLayer.value) return
      
      const canvas = document.createElement('canvas')
      canvas.width = drawingLayer.value.clientWidth
      canvas.height = drawingLayer.value.clientHeight
      const ctx = canvas.getContext('2d')
      
      // 清除畫布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // 繪製已保存的線條
      ctx.strokeStyle = '#2196F3' // 藍色
      ctx.lineWidth = 2
      
      drawnLines.value.forEach(line => {
        ctx.beginPath()
        ctx.moveTo(line.start.x, line.start.y)
        ctx.lineTo(line.end.x, line.end.y)
        ctx.stroke()
      })
      
      // 如果正在繪製，顯示當前線條
      if (isDrawing.value) {
        ctx.strokeStyle = '#FF5722' // 橙色
        ctx.beginPath()
        ctx.moveTo(startPoint.value.x, startPoint.value.y)
        ctx.lineTo(endPoint.value.x, endPoint.value.y)
        ctx.stroke()
      }
      
      // 更新繪圖層
      drawingLayer.value.innerHTML = ''
      drawingLayer.value.appendChild(canvas)
    }
    
    // 檢查點擊位置是否接近線條
    const findLineNearPoint = (point) => {
      const threshold = 10 // 點擊容差範圍
      
      for (let i = 0; i < drawnLines.value.length; i++) {
        const line = drawnLines.value[i]
        const distance = distanceToLine(point, line.start, line.end)
        if (distance < threshold) {
          return i
        }
      }
      
      return -1
    }
    
    // 計算點到線的距離
    const distanceToLine = (point, lineStart, lineEnd) => {
      const A = point.x - lineStart.x
      const B = point.y - lineStart.y
      const C = lineEnd.x - lineStart.x
      const D = lineEnd.y - lineStart.y
      
      const dot = A * C + B * D
      const lenSq = C * C + D * D
      let param = -1
      
      if (lenSq !== 0) param = dot / lenSq
      
      let xx, yy
      
      if (param < 0) {
        xx = lineStart.x
        yy = lineStart.y
      } else if (param > 1) {
        xx = lineEnd.x
        yy = lineEnd.y
      } else {
        xx = lineStart.x + param * C
        yy = lineStart.y + param * D
      }
      
      const dx = point.x - xx
      const dy = point.y - yy
      
      return Math.sqrt(dx * dx + dy * dy)
    }
    
    // 生命週期掛鉤
    onMounted(() => {
      // 初始化圖表
      initChart()
      
      // 初始化繪圖層
      initDrawingLayer()
      
      // 加載K線數據
      loadKlineData()
    })
    
    return {
      // 圖表相關
      chartContainer,
      drawingLayer,
      activeTool,
      setTool,
      ohlcData,
      
      // 交易對和時間間隔選擇
      selectedSymbol,
      selectedInterval,
      symbols,
      intervals,
      
      // 狀態和統計數據
      isLoading,
      currentPrice,
      priceChange24h,
      high24h,
      low24h,
      volume24h,
      dataPointsCount,
      dataTimeRange,
      lastUpdated,
      
      // 十字準心和OHLC數據
      hoveredCandle,
      getOhlcColor,
      
      // 通知相關
      showSnackbar,
      snackbarText,
      snackbarColor,
      
      // 計算屬性
      priceChangeColor,
      
      // 方法
      loadKlineData,
    }
  }
}
</script>

<style scoped>
.kline-chart-view {
  padding: 16px;
  position: relative;
  background: linear-gradient(to bottom, rgba(22, 24, 29, 0.7), rgba(28, 30, 38, 0.9));
  min-height: calc(100vh - 120px);
}

.symbol-select {
  max-width: 150px;
}

.interval-select {
  max-width: 100px;
}

.stats-card {
  text-align: center;
  padding: 12px 16px;
  border-radius: 16px;
  background-color: rgba(40, 44, 52, 0.75);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: #fff;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.price-card {
  min-width: 120px;
}

.ohlc-card {
  text-align: left;
  background-color: rgba(53, 53, 77, 0.85);
  color: #fff;
  padding: 12px 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
  min-width: 300px;
  flex-grow: 1;
  border-radius: 16px;
  border: 1px solid rgba(100, 181, 246, 0.2);
}

.chart-wrapper {
  position: relative;
  margin: 16px 0;
  width: 100%;
}

.chart-toolbar {
  display: flex;
  flex-direction: column;
  background-color: rgba(53, 53, 77, 0.85);
  border-radius: 16px;
  padding: 12px 8px;
  z-index: 10;
  position: fixed;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-toolbar:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tool-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  border-radius: 12px;
  cursor: pointer;
  color: #9598a1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  background-color: rgba(255, 255, 255, 0.05);
}

.tool-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.2) 0%, transparent 70%);
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.3s ease;
}

.tool-button:hover {
  background-color: rgba(100, 181, 246, 0.15);
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.tool-button:hover::before {
  opacity: 1;
  transform: scale(1.5);
}

.tool-button.active {
  background-color: rgba(100, 181, 246, 0.3);
  color: #ffffff;
  box-shadow: 0 0 15px rgba(100, 181, 246, 0.4);
}

.chart-container-wrapper {
  position: relative;
  flex-grow: 1;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-container-wrapper:hover {
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(100, 181, 246, 0.2);
}

.chart-container {
  width: 100%;
  height: 500px;
  background-color: rgba(28, 30, 38, 0.9);
}

.drawing-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* 默認不攜擋滑鼠事件，允許十字準心正常工作 */
  z-index: 5;
}

.ohlc-display {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background-color: rgba(53, 53, 77, 0.85);
  border-radius: 4px;
  padding: 8px 12px;
  color: #fff;
  font-size: 12px;
  z-index: 10;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 150px;
}

.ohlc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ohlc-label {
  font-weight: 500;
  margin-right: 8px;
}

.ohlc-value {
  font-weight: 600;
}

.text-success {
  color: #4caf50;
}

.text-error {
  color: #f44336;
}

.text-green {
  color: #26a69a;
}

.text-red {
  color: #ef5350;
}
</style>
