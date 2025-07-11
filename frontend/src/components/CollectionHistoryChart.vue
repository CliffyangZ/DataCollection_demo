<template>
  <div class="collection-history-chart">
    <div v-if="historyData.length > 0">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="text-center pa-4">
      <p>暫無數據</p>
    </div>
  </div>
</template>

<script>
import { defineComponent, computed, ref, watch } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

// 註冊 ChartJS 組件
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

export default defineComponent({
  name: 'CollectionHistoryChart',
  components: { Line },
  props: {
    historyData: {
      type: Array,
      required: true
    }
  },
  setup(props) {
    // 圖表數據
    const chartData = computed(() => {
      const labels = props.historyData.map((item, index) => {
        const date = new Date(item.timestamp)
        return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
      })
      
      const countData = props.historyData.map(item => item.count)
      const progressData = props.historyData.map(item => item.progress)
      
      return {
        labels,
        datasets: [
          {
            label: '批次數量',
            backgroundColor: 'rgba(63, 81, 181, 0.2)',
            borderColor: 'rgba(63, 81, 181, 1)',
            data: countData,
            tension: 0.4,
            yAxisID: 'y'
          },
          {
            label: '總進度 (%)',
            backgroundColor: 'rgba(0, 188, 212, 0.2)',
            borderColor: 'rgba(0, 188, 212, 1)',
            data: progressData,
            tension: 0.4,
            yAxisID: 'y1'
          }
        ]
      }
    })
    
    // 圖表選項
    const chartOptions = ref({
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: {
            display: true,
            text: '批次數量'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: {
            drawOnChartArea: false
          },
          title: {
            display: true,
            text: '總進度 (%)'
          },
          min: 0,
          max: 100
        }
      },
      plugins: {
        legend: {
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      }
    })
    
    return {
      chartData,
      chartOptions
    }
  }
})
</script>

<style scoped>
.collection-history-chart {
  height: 400px;
  position: relative;
}
</style>