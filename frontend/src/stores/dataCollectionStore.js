import { defineStore } from 'pinia'

// Define the store
const useDataCollectionStore = defineStore('dataCollection', {
  state: () => ({
    isCollecting: false,
    collectionProgress: 0,
    totalKlines: 0,
    collectedKlines: 0,
    symbol: '',
    interval: '',
    startTime: '',
    endTime: '',
    batchCount: 0,
    currentBatch: {
      startTime: '',
      endTime: '',
      count: 0
    },
    collectionHistory: [],
    error: null
  }),
  
  getters: {
    progressPercentage: (state) => {
      if (state.totalKlines === 0) return 0
      return Math.min(100, (state.collectedKlines / state.totalKlines * 100).toFixed(2))
    },
    
    collectionRate: (state) => {
      if (state.collectionHistory.length < 2) return 0
      const latestEntries = state.collectionHistory.slice(-10)
      let totalTime = 0
      let totalKlines = 0
      
      for (let i = 1; i < latestEntries.length; i++) {
        const timeDiff = new Date(latestEntries[i].timestamp) - new Date(latestEntries[i-1].timestamp)
        totalTime += timeDiff
        totalKlines += latestEntries[i].count
      }
      
      // Return klines per second
      return totalTime > 0 ? (totalKlines / (totalTime / 1000)).toFixed(2) : 0
    },
    
    estimatedTimeRemaining: (state) => {
      if (state.collectionRate <= 0 || state.totalKlines <= state.collectedKlines) return '0'
      const remainingKlines = state.totalKlines - state.collectedKlines
      const secondsRemaining = remainingKlines / state.collectionRate
      
      // Format time remaining
      if (secondsRemaining < 60) return `${Math.ceil(secondsRemaining)}秒`
      if (secondsRemaining < 3600) return `${Math.ceil(secondsRemaining / 60)}分鐘`
      return `${Math.ceil(secondsRemaining / 3600)}小時`
    }
  },
  
  actions: {
    startCollection(params) {
      this.isCollecting = true
      this.symbol = params.symbol
      this.interval = params.interval
      this.startTime = params.startTime
      this.endTime = params.endTime
      this.totalKlines = params.estimatedKlines || 0
      this.collectedKlines = 0
      this.batchCount = 0
      this.collectionProgress = 0
      this.collectionHistory = []
      this.error = null
    },
    
    updateProgress(data) {
      this.collectionProgress = data.progress
      this.collectedKlines = data.totalCollected
      this.batchCount = data.batchCount
      this.currentBatch = {
        startTime: data.currentBatchStart,
        endTime: data.currentBatchEnd,
        count: data.batchSize
      }
      
      // Add to history for rate calculation
      this.collectionHistory.push({
        timestamp: new Date().toISOString(),
        count: data.batchSize,
        progress: data.progress
      })
      
      // Keep history at a reasonable size
      if (this.collectionHistory.length > 100) {
        this.collectionHistory.shift()
      }
    },
    
    completeCollection() {
      this.isCollecting = false
      this.collectionProgress = 100
    },
    
    setError(error) {
      this.error = error
    },
    
    resetState() {
      this.isCollecting = false
      this.collectionProgress = 0
      this.totalKlines = 0
      this.collectedKlines = 0
      this.symbol = ''
      this.interval = ''
      this.startTime = ''
      this.endTime = ''
      this.batchCount = 0
      this.currentBatch = {
        startTime: '',
        endTime: '',
        count: 0
      }
      this.collectionHistory = []
      this.error = null
    }
  }
})

// Export the store
export { useDataCollectionStore }