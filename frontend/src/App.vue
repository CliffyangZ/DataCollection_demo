<template>
  <v-app>
    <v-app-bar app color="transparent" elevation="0" class="space-gray-toolbar">
      <v-app-bar-title class="app-title">TradingModel_V3</v-app-bar-title>
      <v-spacer></v-spacer>
      
      <!-- 導航按鈕 -->
      <router-link to="/" custom v-slot="{ navigate, isActive }">
        <v-btn
          @click="navigate"
          variant="text"
          class="nav-btn mx-2"
          :class="{ 'nav-btn-active': isActive }"
        >
          <v-icon start class="nav-icon">mdi-home</v-icon>
          <span class="nav-text">Home</span>
        </v-btn>
      </router-link>
      
      <router-link to="/data" custom v-slot="{ navigate, isActive }">
        <v-btn
          @click="navigate"
          variant="text"
          class="nav-btn mx-2"
          :class="{ 'nav-btn-active': isActive }"
        >
          <v-icon start class="nav-icon">mdi-chart-line</v-icon>
          <span class="nav-text">Data</span>
        </v-btn>
      </router-link>
      
      <v-btn icon class="theme-toggle" @click="toggleTheme">
        <v-icon>{{ isDarkTheme ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view />
      </v-container>
    </v-main>

    <v-footer app class="space-gray-footer">
      <span class="footer-text">&copy; {{ new Date().getFullYear() }} - TradingModel_V3</span>
    </v-footer>
  </v-app>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      isDarkTheme: true
    }
  },
  methods: {
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme
      this.$vuetify.theme.global.name = this.isDarkTheme ? 'dark' : 'light'
    }
  }
}
</script>

<style>
html, body {
  overflow-y: auto;
}

/* Material 3 Expressive Design Styles */
.space-gray-toolbar {
  background: rgba(40, 44, 52, 0.85) !important;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.space-gray-footer {
  background: rgba(40, 44, 52, 0.85) !important;
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.app-title {
  font-weight: 600;
  letter-spacing: 0.5px;
  font-size: 1.25rem;
  background: linear-gradient(90deg, #e0e0e0, #ffffff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.nav-btn {
  border-radius: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
  padding: 0 16px;
  height: 42px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.nav-btn::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, #64B5F6, #2196F3);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  border-radius: 3px;
}

.nav-btn:hover::after {
  width: 70%;
}

.nav-btn-active::after {
  width: 80%;
}

.nav-icon {
  margin-right: 6px;
  transition: transform 0.2s ease;
}

.nav-btn:hover .nav-icon {
  transform: scale(1.15);
}

.nav-text {
  transition: all 0.2s ease;
}

.nav-btn:hover .nav-text {
  letter-spacing: 0.7px;
}

.theme-toggle {
  border-radius: 50%;
  width: 42px;
  height: 42px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.1);
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(15deg);
}

.footer-text {
  opacity: 0.7;
  font-size: 0.85rem;
  letter-spacing: 0.5px;
}
</style>